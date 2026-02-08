"""
Mchezo views for ANNA platform.

Implements real backend logic for mchezo (rotating savings) operations:
- Group and membership management
- Contribution recording
- Payout processing
- Cycle management
"""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db import transaction as db_transaction
from django.utils import timezone
from django.http import JsonResponse

from core.permissions import has_mchezo_role
from core.services import AuditLogger
from mchezo.services import MchezoService
from mchezo.models import Group, Membership, Cycle, Contribution, Payout
from mchezo.forms import MembershipForm, ContributionForm, PayoutForm, CycleStartForm


class MchezoMemberListView(ListView):
    """List all members of a group."""
    model = Membership
    template_name = 'mchezo/member_list.html'
    context_object_name = 'memberships'
    
    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return Membership.objects.filter(
            group_id=group_id,
            is_deleted=False,
            status='active'
        ).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(Group, pk=self.kwargs['group_id'])
        context['group'] = group
        return context


class MchezoMemberAddView(CreateView):
    """Add a new member to a group."""
    model = Membership
    form_class = MembershipForm
    template_name = 'mchezo/member_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
    
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group, pk=group_id)
        
        # Check permissions
        if not has_mchezo_role(request.user, group, ['admin']):
            messages.error(request, "Only admins can add members.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        # Check if group is full
        if group.is_full():
            messages.error(request, "Group is at maximum capacity.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        if not group.is_open:
            messages.error(request, "Group is not open for new members.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        return super().get(request, *args, **kwargs)
    
    @db_transaction.atomic
    def form_valid(self, form):
        group = self.group
        
        try:
            membership = MchezoService.add_member(
                group=group,
                user=form.cleaned_data['user'],
                payout_order=form.cleaned_data.get('payout_order'),
                phone_number=form.cleaned_data.get('phone_number', ''),
                created_by=self.request.user,
            )
            
            messages.success(
                self.request, 
                f"{membership.user.get_full_name()} added to {group.name}."
            )
            return redirect('dashboard:mchezo', group_id=group.id)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        context['page_title'] = 'Add Member'
        return context


class MchezoCycleStartView(CreateView):
    """Start a new cycle for a group."""
    model = Cycle
    fields = ['notes']
    template_name = 'mchezo/cycle_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
    
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group, pk=group_id)
        
        # Check permissions
        if not has_mchezo_role(request.user, group, ['admin']):
            messages.error(request, "Only admins can start cycles.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        # Check if there's already an active cycle
        if group.get_current_cycle():
            messages.error(request, "An active cycle already exists.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        # Check if group has enough members
        if group.get_member_count() < 2:
            messages.error(request, "At least 2 members are required to start a cycle.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        return super().get(request, *args, **kwargs)
    
    @db_transaction.atomic
    def form_valid(self, form):
        group = self.group
        
        try:
            cycle = MchezoService.start_cycle(
                group,
                created_by=self.request.user,
            )
            
            # Log the action
            AuditLogger.log(
                user=self.request.user,
                action='create',
                content_object=cycle,
                description=f"Cycle {cycle.cycle_number} started for {group.name}",
                request=self.request
            )
            
            messages.success(
                self.request, 
                f"Cycle {cycle.cycle_number} started for {group.name}."
            )
            return redirect('dashboard:mchezo', group_id=group.id)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        context['page_title'] = 'Start Cycle'
        return context


class MchezoContributionCreateView(CreateView):
    """Record a contribution for a member."""
    model = Contribution
    template_name = 'mchezo/contribution_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
        self.cycle = self.group.get_current_cycle()
    
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group, pk=group_id)
        
        # Check permissions
        if not has_mchezo_role(request.user, group, ['admin', 'treasurer']):
            messages.error(request, "You don't have permission to record contributions.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        # Check for active cycle
        cycle = group.get_current_cycle()
        if not cycle:
            messages.error(request, "No active cycle. Start a cycle first.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = ContributionForm(group=self.group)
        return form
    
    @db_transaction.atomic
    def form_valid(self, form):
        group = self.group
        cycle = self.cycle
        
        try:
            contribution = MchezoService.record_contribution(
                cycle=cycle,
                membership=form.cleaned_data['membership'],
                amount=form.cleaned_data['amount'],
                payment_method=form.cleaned_data['payment_method'],
                reference_number=form.cleaned_data.get('reference_number', ''),
                notes=form.cleaned_data.get('notes', ''),
                created_by=self.request.user,
            )
            
            # Log the contribution
            AuditLogger.log(
                user=self.request.user,
                action='contribution',
                content_object=contribution,
                description=f"Contribution of {contribution.amount} recorded for {contribution.membership.user.get_full_name()}",
                request=self.request
            )
            
            messages.success(
                self.request, 
                f"Contribution of TZS {contribution.amount:,.0f} recorded."
            )
            return redirect('dashboard:mchezo', group_id=group.id)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        context['cycle'] = self.cycle
        context['page_title'] = 'Record Contribution'
        return context


class MchezoPayoutCreateView(CreateView):
    """Record a payout for a member."""
    model = Payout
    template_name = 'mchezo/payout_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
        self.cycle = self.group.get_current_cycle()
    
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group, pk=group_id)
        
        # Check permissions
        if not has_mchezo_role(request.user, group, ['admin', 'treasurer']):
            messages.error(request, "You don't have permission to record payouts.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        # Check for active cycle
        cycle = group.get_current_cycle()
        if not cycle:
            messages.error(request, "No active cycle.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = PayoutForm(group=self.group, cycle=self.cycle)
        return form
    
    @db_transaction.atomic
    def form_valid(self, form):
        group = self.group
        cycle = self.cycle
        
        try:
            payout = MchezoService.record_payout(
                cycle=cycle,
                membership=form.cleaned_data['membership'],
                amount=form.cleaned_data['amount'],
                payment_method=form.cleaned_data['payment_method'],
                reference_number=form.cleaned_data.get('reference_number', ''),
                notes=form.cleaned_data.get('notes', ''),
                created_by=self.request.user,
            )
            
            # Log the payout
            AuditLogger.log(
                user=self.request.user,
                action='payout',
                content_object=payout,
                description=f"Payout of {payout.amount} to {payout.membership.user.get_full_name()}",
                request=self.request
            )
            
            messages.success(
                self.request, 
                f"Payout of TZS {payout.amount:,.0f} recorded."
            )
            return redirect('dashboard:mchezo', group_id=group.id)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        context['cycle'] = self.cycle
        context['page_title'] = 'Record Payout'
        return context


class MchezoCycleCloseView(UpdateView):
    """Close the current cycle."""
    model = Cycle
    fields = ['notes']
    template_name = 'mchezo/cycle_close.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
        self.cycle = self.group.get_current_cycle()
    
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group, pk=group_id)
        
        # Check permissions
        if not has_mchezo_role(request.user, group, ['admin']):
            messages.error(request, "Only admins can close cycles.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        cycle = group.get_current_cycle()
        if not cycle:
            messages.error(request, "No active cycle to close.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        return self.cycle
    
    @db_transaction.atomic
    def form_valid(self, form):
        group = self.group
        cycle = self.cycle
        
        # Check if all members have received payout
        if not cycle.is_complete():
            messages.error(
                self.request, 
                "Cannot close cycle. Not all members have received payout."
            )
            return redirect('dashboard:mchezo', group_id=group.id)
        
        # Save form first (this will set updated_by)
        form.instance.updated_by = self.request.user
        form.save()
        
        # Then complete the cycle
        MchezoService.complete_cycle(cycle, updated_by=self.request.user)
        
        # Log the action
        AuditLogger.log(
            user=self.request.user,
            action='update',
            content_object=cycle,
            description=f"Cycle {cycle.cycle_number} completed",
            new_values={'status': 'completed'},
            request=self.request
        )
        
        messages.success(self.request, f"Cycle {cycle.cycle_number} completed.")
        return redirect('dashboard:mchezo', group_id=group.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        context['cycle'] = self.cycle
        context['page_title'] = 'Close Cycle'
        
        # Add progress info
        progress = MchezoService.get_cycle_progress(self.cycle)
        context['progress'] = progress
        
        return context


@login_required
def mchezo_member_detail(request, group_id, membership_id):
    """View member details."""
    membership = get_object_or_404(
        Membership.objects.select_related('user', 'group'),
        pk=membership_id,
        group_id=group_id
    )
    
    # Check permissions
    if not has_mchezo_role(request.user, membership.group, ['admin', 'treasurer', 'member']):
        messages.error(request, "You don't have permission to view this member.")
        return redirect('dashboard:mchezo', group_id=group_id)
    
    # Get member's contributions and payouts
    contributions = Contribution.objects.filter(
        membership=membership
    ).order_by('-contribution_date', '-contribution_time')
    
    payouts = Payout.objects.filter(
        membership=membership
    ).order_by('-completed_date')
    
    return render(request, 'mchezo/member_detail.html', {
        'membership': membership,
        'group': membership.group,
        'contributions': contributions,
        'payouts': payouts,
        'page_title': f'{membership.user.get_full_name()} - Member Details',
    })


@login_required
def mchezo_group_settings(request, group_id):
    """View and edit group settings."""
    group = get_object_or_404(Group, pk=group_id)
    
    # Check permissions
    if not has_mchezo_role(request.user, group, ['admin']):
        messages.error(request, "Only admins can access group settings.")
        return redirect('dashboard:mchezo', group_id=group.id)
    
    if request.method == 'POST':
        # Update group settings
        group.name = request.POST.get('name', group.name)
        group.description = request.POST.get('description', group.description)
        group.contribution_amount = request.POST.get('contribution_amount', group.contribution_amount)
        group.contribution_frequency = request.POST.get('contribution_frequency', group.contribution_frequency)
        group.max_members = request.POST.get('max_members', group.max_members)
        group.is_open = request.POST.get('is_open', 'off') == 'on'
        group.save()
        
        messages.success(request, "Group settings updated.")
        return redirect('dashboard:mchezo', group_id=group.id)
    
    return render(request, 'mchezo/group_settings.html', {
        'group': group,
        'page_title': f'{group.name} - Settings',
    })


class MchezoMemberEditView(UpdateView):
    """Edit an existing membership."""
    model = Membership
    form_class = MembershipForm
    template_name = 'mchezo/member_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
    
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group, pk=group_id)
        
        # Check permissions
        if not has_mchezo_role(request.user, group, ['admin']):
            messages.error(request, "Only admins can edit members.")
            return redirect('dashboard:mchezo', group_id=group.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        membership_id = self.kwargs.get('membership_id')
        return get_object_or_404(Membership, pk=membership_id, group=self.group)
    
    @db_transaction.atomic
    def form_valid(self, form):
        group = self.group
        membership = self.get_object()
        old_payout_order = membership.payout_order
        
        # Update membership
        membership.payout_order = form.cleaned_data.get('payout_order')
        membership.phone_number = form.cleaned_data.get('phone_number', '')
        membership.save()
        
        # Log the action
        AuditLogger.log(
            user=self.request.user,
            action='update',
            content_object=membership,
            description=f"Membership updated for {membership.user.get_full_name()}",
            request=self.request
        )
        
        messages.success(self.request, f"{membership.user.get_full_name()} updated successfully.")
        return redirect('mchezo:members', group_id=group.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        context['page_title'] = 'Edit Member'
        return context
