"""
Forms for mchezo app.
"""
from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal

from .models import Group, Membership, Cycle, Contribution, Payout


class MembershipForm(forms.ModelForm):
    """Form for adding/editing membership."""
    
    class Meta:
        model = Membership
        fields = ['user', 'phone_number', 'payout_order']
        widgets = {
            'user': forms.Select(attrs={'class': 'anna-form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Phone number'}),
            'payout_order': forms.NumberInput(attrs={'class': 'anna-form-input', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for payout_order
        self.fields['payout_order'].help_text = "Position in payout order (leave empty for next position)"


class GroupForm(forms.ModelForm):
    """Form for creating/editing groups."""
    
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'contribution_amount', 'contribution_frequency',
            'contribution_day', 'max_members', 'is_open', 'payout_order_method'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'description': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 3}),
            'contribution_amount': forms.NumberInput(attrs={'class': 'anna-form-input', 'min': '100'}),
            'contribution_frequency': forms.Select(attrs={'class': 'anna-form-input'}),
            'contribution_day': forms.NumberInput(attrs={'class': 'anna-form-input', 'min': '1', 'max': '31'}),
            'max_members': forms.NumberInput(attrs={'class': 'anna-form-input', 'min': '2', 'max': '100'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payout_order_method': forms.Select(attrs={'class': 'anna-form-input'}),
        }


class ContributionForm(forms.ModelForm):
    """Form for recording contributions."""
    
    class Meta:
        model = Contribution
        fields = ['membership', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'membership': forms.Select(attrs={'class': 'anna-form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'anna-form-input'}),
            'payment_method': forms.Select(attrs={'class': 'anna-form-input'}),
            'reference_number': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'notes': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        
        if group:
            # Set default amount from group
            self.fields['amount'].initial = group.contribution_amount
            self.fields['amount'].help_text = f"Fixed amount: TZS {group.contribution_amount:,.0f}"
            
            # Filter membership choices
            self.fields['membership'].queryset = Membership.objects.filter(
                group=group,
                status='active',
                is_deleted=False
            ).select_related('user')
        
        # Set payment method choices
        self.fields['payment_method'].choices = [
            ('', '-- Select --'),
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
        ]


class PayoutForm(forms.ModelForm):
    """Form for recording payouts."""
    
    class Meta:
        model = Payout
        fields = ['membership', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'membership': forms.Select(attrs={'class': 'anna-form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'anna-form-input'}),
            'payment_method': forms.Select(attrs={'class': 'anna-form-input'}),
            'reference_number': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'notes': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        cycle = kwargs.pop('cycle', None)
        super().__init__(*args, **kwargs)
        
        if group and cycle:
            # Get memberships who haven't received payout
            paid_memberships = cycle.payouts.filter(
                status='completed'
            ).values_list('membership_id', flat=True)
            
            self.fields['membership'].queryset = Membership.objects.filter(
                group=group,
                status='active',
                is_deleted=False
            ).exclude(id__in=paid_memberships).select_related('user')
            
            # Set default amount
            total_amount = group.contribution_amount * group.get_member_count()
            self.fields['amount'].initial = total_amount
            self.fields['amount'].help_text = f"Total pool: TZS {total_amount:,.0f}"
        
        # Set payment method choices
        self.fields['payment_method'].choices = [
            ('', '-- Select --'),
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
        ]


class CycleStartForm(forms.ModelForm):
    """Form for starting a cycle."""
    
    class Meta:
        model = Cycle
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 3, 'placeholder': 'Optional notes for this cycle'}),
        }
