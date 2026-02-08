"""
Wakala views for ANNA platform.

Implements real backend logic for wakala operations:
- Transaction creation, editing, deletion
- Financial day opening/closing
- Dashboard data loading
"""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db import transaction as db_transaction
from django.utils import timezone
from django.http import JsonResponse

from core.permissions import has_wakala_role
from core.services import AuditLogger
from balancing.services import BalancingEngine
from transactions.services import TransactionService
from .models import Wakala, FinancialDay, Transaction
from .forms import TransactionForm, DepositForm, WithdrawalForm


class WakalaListView(ListView):
    """List all wakalas (admin view)."""
    model = Wakala
    template_name = 'wakala/wakala_list.html'
    context_object_name = 'wakalas'
    
    def get_queryset(self):
        # Only show wakalas the user has access to
        if self.request.user.is_superuser:
            return Wakala.objects.all()
        return Wakala.objects.filter(
            wakalauser__user=self.request.user
        ).distinct()


class WakalaTransactionListView(ListView):
    """List all transactions for a wakala."""
    model = Transaction
    template_name = 'wakala/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        wakala_id = self.kwargs['wakala_id']
        return Transaction.objects.filter(
            wakala_id=wakala_id
        ).select_related('financial_day', 'network', 'bank', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wakala = get_object_or_404(Wakala, pk=self.kwargs['wakala_id'])
        context['wakala'] = wakala
        return context


class WakalaTransactionCreateView(CreateView):
    """Create a new transaction for a wakala."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'wakala/transaction_form.html'
    
    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return []
        return [self.template_name]
    
    def get(self, request, *args, **kwargs):
        wakala = get_object_or_404(Wakala, pk=self.kwargs['wakala_id'])
        
        # Check permissions
        if not has_wakala_role(request.user, wakala, ['owner', 'manager', 'agent']):
            messages.error(request, "You don't have permission to record transactions.")
            return redirect('dashboard:wakala', wakala_id=wakala.id)
        
        # Check for open day
        open_day = wakala.get_open_financial_day()
        if not open_day:
            messages.error(request, "No open financial day. Please open a day first.")
            return redirect('dashboard:wakala', wakala_id=wakala.id)
        
        self.open_day = open_day
        self.wakala = wakala
        return super().get(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return form
    
    @db_transaction.atomic
    def form_valid(self, form):
        wakala = get_object_or_404(Wakala, pk=self.kwargs['wakala_id'])
        open_day = wakala.get_open_financial_day()
        
        if not open_day:
            messages.error(self.request, "No open financial day.")
            return redirect('dashboard:wakala', wakala_id=wakala.id)
        
        # Get network and bank from form data
        network = form.cleaned_data.get('network')
        bank = form.cleaned_data.get('bank')
        
        # Create transaction
        txn = TransactionService.create_transaction(
            user=self.request.user,
            wakala=wakala,
            financial_day=open_day,
            transaction_type=form.cleaned_data['transaction_type'],
            amount=form.cleaned_data['amount'],
            payment_method=form.cleaned_data['payment_method'],
            customer_name=form.cleaned_data.get('customer_name', ''),
            customer_phone=form.cleaned_data.get('customer_phone', ''),
            customer_reference=form.cleaned_data.get('customer_reference', ''),
            network=network,
            bank=bank,
            reference_number=form.cleaned_data.get('reference_number', ''),
            description=form.cleaned_data.get('description', ''),
            notes=form.cleaned_data.get('notes', ''),
        )
        
        messages.success(self.request, f"Transaction {txn.transaction_code} recorded successfully.")
        
        # Return JSON for AJAX requests
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'transaction_code': txn.transaction_code,
                'amount': str(txn.amount),
                'transaction_type': txn.get_transaction_type_display(),
            })
        
        return redirect('dashboard:wakala', wakala_id=wakala.id)
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
            }, status=400)
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wakala'] = self.wakala
        context['open_day'] = self.open_day
        context['page_title'] = 'New Transaction'
        return context


class WakalaTransactionEditView(UpdateView):
    """Edit an existing transaction."""
    model = Transaction
    fields = [
        'amount', 'customer_name', 'customer_phone',
        'customer_reference', 'payment_method', 'network', 'bank',
        'reference_number', 'description', 'notes'
    ]
    template_name = 'wakala/transaction_form.html'
    
    def get_object(self, queryset=None):
        """Retrieve the transaction using transaction_id from URL kwargs."""
        transaction_id = self.kwargs.get('transaction_id')
        return get_object_or_404(Transaction, pk=transaction_id)
    
    def get(self, request, *args, **kwargs):
        txn = self.get_object()
        
        # Check if transaction is editable
        if not txn.is_editable():
            messages.error(request, "This transaction cannot be edited.")
            return redirect('dashboard:wakala', wakala_id=txn.wakala.id)
        
        # Check permissions
        if not has_wakala_role(request.user, txn.wakala, ['owner', 'manager']):
            messages.error(request, "You don't have permission to edit transactions.")
            return redirect('dashboard:wakala', wakala_id=txn.wakala.id)
        
        return super().get(request, *args, **kwargs)
    
    @db_transaction.atomic
    def form_valid(self, form):
        txn = self.get_object()
        old_values = {
            'amount': str(txn.amount),
            'customer_name': txn.customer_name,
            'payment_method': txn.payment_method,
        }
        
        response = super().form_valid(form)
        
        # Log the edit
        AuditLogger.log(
            user=self.request.user,
            action='update',
            content_object=txn,
            description=f"Transaction {txn.transaction_code} edited",
            old_values=old_values,
            new_values={
                'amount': str(txn.amount),
                'customer_name': txn.customer_name,
                'payment_method': txn.payment_method,
            },
            request=self.request
        )
        
        messages.success(self.request, f"Transaction {txn.transaction_code} updated successfully.")
        return redirect('dashboard:wakala', wakala_id=txn.wakala.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        txn = self.get_object()
        context['wakala'] = txn.wakala
        context['page_title'] = f'Edit Transaction {txn.transaction_code}'
        context['is_edit'] = True
        return context


class WakalaTransactionDeleteView(DeleteView):
    """Soft delete a transaction."""
    model = Transaction
    template_name = 'wakala/transaction_confirm_delete.html'
    
    def get_object(self, queryset=None):
        """Retrieve the transaction using transaction_id from URL kwargs."""
        transaction_id = self.kwargs.get('transaction_id')
        return get_object_or_404(Transaction, pk=transaction_id)
    
    def get(self, request, *args, **kwargs):
        txn = self.get_object()
        
        # Check if deletable
        if not txn.is_deletable():
            messages.error(request, "This transaction cannot be deleted.")
            return redirect('dashboard:wakala', wakala_id=txn.wakala.id)
        
        # Check permissions
        if not has_wakala_role(request.user, txn.wakala, ['owner']):
            messages.error(request, "Only owners can delete transactions.")
            return redirect('dashboard:wakala', wakala_id=txn.wakala.id)
        
        return super().get(request, *args, **kwargs)
    
    @db_transaction.atomic
    def delete(self, request, *args, **kwargs):
        txn = self.get_object()
        txn_code = txn.transaction_code
        wakala_id = txn.wakala.id
        
        # Soft delete
        txn.delete()
        
        messages.success(request, f"Transaction {txn_code} deleted.")
        return redirect('dashboard:wakala', wakala_id=wakala_id)


class WakalaDayOpenView(CreateView):
    """Open a new financial day."""
    model = FinancialDay
    fields = ['date', 'opening_balance', 'opening_balance_note']
    template_name = 'wakala/day_open.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        wakala_id = self.kwargs.get('wakala_id')
        self.wakala = get_object_or_404(Wakala, pk=wakala_id)
    
    def get(self, request, wakala_id, *args, **kwargs):
        wakala = get_object_or_404(Wakala, pk=wakala_id)
        
        # Check permissions
        if not has_wakala_role(request.user, wakala, ['owner', 'manager', 'agent']):
            messages.error(request, "You don't have permission to open days.")
            return redirect('dashboard:wakala', wakala_id=wakala.id)
        
        # Check if already has open day
        if wakala.get_open_financial_day():
            messages.warning(request, f"Day for {wakala.get_open_financial_day().date} is still open.")
            return redirect('dashboard:wakala', wakala_id=wakala.id)
        
        self.wakala = wakala
        return super().get(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super().get_initial()
        initial['date'] = timezone.now().date()
        return initial
    
    @db_transaction.atomic
    def form_valid(self, form):
        wakala = self.wakala
        
        try:
            day = BalancingEngine.open_day(
                user=self.request.user,
                wakala=wakala,
                date=form.cleaned_data['date'],
                opening_balance=form.cleaned_data.get('opening_balance', 0),
                note=form.cleaned_data.get('opening_balance_note', ''),
            )
            
            messages.success(self.request, f"Financial day for {day.date} opened successfully.")
            return redirect('dashboard:wakala', wakala_id=wakala.id)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wakala'] = self.wakala
        context['page_title'] = 'Open Financial Day'
        return context


class WakalaDayCloseView(UpdateView):
    """Close the current financial day."""
    model = FinancialDay
    fields = ['closing_balance', 'closing_balance_note']
    template_name = 'wakala/day_close.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        wakala_id = self.kwargs.get('wakala_id')
        self.wakala = get_object_or_404(Wakala, pk=wakala_id)
        self.open_day = self.wakala.get_open_financial_day()
    
    def get(self, request, *args, **kwargs):
        if not self.open_day:
            messages.error(request, "No open financial day to close.")
            return redirect('dashboard:wakala', wakala_id=self.wakala.id)
        
        # Check permissions
        if not has_wakala_role(request.user, self.wakala, ['owner', 'manager']):
            messages.error(request, "You don't have permission to close days.")
            return redirect('dashboard:wakala', wakala_id=self.wakala.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        if not self.open_day:
            raise PermissionDenied("No open financial day to close.")
        return self.open_day
    
    def dispatch(self, request, *args, **kwargs):
        if not self.open_day:
            messages.error(request, "No open financial day to close.")
            return redirect('dashboard:wakala', wakala_id=self.wakala.id)
        if not has_wakala_role(request.user, self.wakala, ['owner', 'manager']):
            messages.error(request, "You don't have permission to close days.")
            return redirect('dashboard:wakala', wakala_id=self.wakala.id)
        return super().dispatch(request, *args, **kwargs)
    
    @db_transaction.atomic
    def form_valid(self, form):
        wakala = self.wakala
        
        try:
            day = BalancingEngine.close_day(
                user=self.request.user,
                wakala=wakala,
                closing_balance=form.cleaned_data['closing_balance'],
                note=form.cleaned_data.get('closing_balance_note', ''),
            )
            
            status = "balanced" if day.discrepancy == 0 else "discrepancy"
            messages.success(
                self.request, 
                f"Financial day closed. {status.capitalize()}: TZS {abs(day.discrepancy):,.2f}"
            )
            return redirect('dashboard:wakala', wakala_id=wakala.id)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wakala'] = self.wakala
        context['open_day'] = self.open_day
        context['page_title'] = 'Close Financial Day'
        context['computed_balance'] = self.open_day.calculate_computed_balance()
        return context


@login_required
def transaction_detail(request, wakala_id, transaction_id):
    """View transaction details."""
    txn = get_object_or_404(
        Transaction.objects.select_related('financial_day', 'wakala', 'network', 'bank', 'created_by'),
        pk=transaction_id,
        wakala_id=wakala_id
    )
    
    # Check permissions
    if not has_wakala_role(request.user, txn.wakala, ['owner', 'manager', 'agent']):
        messages.error(request, "You don't have permission to view this transaction.")
        return redirect('dashboard:wakala', wakala_id=wakala_id)
    
    # Get audit logs
    audit_logs = AuditLogger.get_logs_for_object(txn)
    
    return render(request, 'wakala/transaction_detail.html', {
        'transaction': txn,
        'wakala': txn.wakala,
        'audit_logs': audit_logs,
        'page_title': f'Transaction {txn.transaction_code}',
    })


@login_required
def wakala_settings(request, wakala_id):
    """View and edit wakala settings."""
    wakala = get_object_or_404(Wakala, pk=wakala_id)
    
    # Check permissions
    if not has_wakala_role(request.user, wakala, ['owner']):
        messages.error(request, "Only owners can access settings.")
        return redirect('dashboard:wakala', wakala_id=wakala.id)
    
    if request.method == 'POST':
        # Update wakala settings
        wakala.name = request.POST.get('name', wakala.name)
        wakala.business_type = request.POST.get('business_type', wakala.business_type)
        wakala.phone_number = request.POST.get('phone_number', wakala.phone_number)
        wakala.alternate_phone = request.POST.get('alternate_phone', wakala.alternate_phone)
        wakala.email = request.POST.get('email', wakala.email)
        wakala.address = request.POST.get('address', wakala.address)
        wakala.region = request.POST.get('region', wakala.region)
        wakala.district = request.POST.get('district', wakala.district)
        wakala.allows_agents = request.POST.get('allows_agents', 'off') == 'on'
        wakala.requires_manager_approval = request.POST.get('requires_manager_approval', 'off') == 'on'
        wakala.save()
        
        messages.success(request, "Wakala settings updated.")
        return redirect('dashboard:wakala', wakala_id=wakala.id)
    
    return render(request, 'wakala/settings.html', {
        'wakala': wakala,
        'page_title': f'{wakala.name} - Settings',
    })
