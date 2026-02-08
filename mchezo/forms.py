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
    
    # Week selection for flexible payments
    contribution_week = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'anna-form-input'}),
        help_text="Select which week/period this contribution is for"
    )
    
    # Optional: pay for multiple weeks at once
    weeks_to_pay = forms.ChoiceField(
        choices=[(1, '1 week'), (2, '2 weeks'), (3, '3 weeks'), (4, '4 weeks')],
        initial=1,
        widget=forms.Select(attrs={'class': 'anna-form-input'}),
        help_text="Pay for multiple weeks in advance (bulk payment)"
    )
    
    class Meta:
        model = Contribution
        fields = ['membership', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'membership': forms.Select(attrs={'class': 'anna-form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'anna-form-input', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'anna-form-input'}),
            'reference_number': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'notes': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        cycle = kwargs.pop('cycle', None)
        super().__init__(*args, **kwargs)
        
        if group and cycle:
            # Set default amount from group
            self.fields['amount'].initial = group.contribution_amount
            self.fields['amount'].help_text = (
                f"Fixed amount per week: TZS {group.contribution_amount:,.0f}. "
                "You can pay more or less (incremental payments allowed)."
            )
            
            # Filter membership choices
            self.fields['membership'].queryset = Membership.objects.filter(
                group=group,
                status='active',
                is_deleted=False
            ).select_related('user')
            
            # Build week choices based on cycle progress
            current_week = cycle.get_current_week()
            total_weeks = group.get_member_count()
            
            week_choices = []
            for w in range(1, total_weeks + 1):
                week_choices.append((w, f"Week {w}"))
            
            self.fields['contribution_week'].choices = week_choices
            self.fields['contribution_week'].initial = current_week
            
            # Add info about current week
            self.fields['contribution_week'].help_text = (
                f"Current week is {current_week}. "
                "You can pay for current week or future weeks in advance."
            )
        
        # Set payment method choices
        self.fields['payment_method'].choices = [
            ('', '-- Select --'),
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
        ]
    
    def clean_amount(self):
        """Validate amount - allow any positive amount."""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        return amount


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


class PayoutEditForm(forms.ModelForm):
    """Form for editing existing payouts - shows all memberships."""
    
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
        
        if group:
            # Show all active memberships for editing
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
