"""
Forms for wakala app.
"""
from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal

from .models import Transaction


class TransactionForm(forms.ModelForm):
    """Form for creating/editing transactions."""
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'anna-form-input',
            'min': '1',
            'step': '100',
            'autofocus': 'autofocus'
        }),
        validators=[MinValueValidator(Decimal('1'))]
    )
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'amount', 'customer_name', 'customer_phone',
            'customer_reference', 'payment_method', 'network', 'bank',
            'reference_number', 'description', 'notes'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'anna-form-input'}),
            'customer_name': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'customer_phone': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'customer_reference': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'payment_method': forms.Select(attrs={'class': 'anna-form-input'}),
            'network': forms.Select(attrs={'class': 'anna-form-input'}),
            'bank': forms.Select(attrs={'class': 'anna-form-input'}),
            'reference_number': forms.TextInput(attrs={'class': 'anna-form-input'}),
            'description': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set transaction type choices
        self.fields['transaction_type'].choices = [
            ('deposit', 'Deposit'),
            ('withdrawal', 'Withdrawal'),
            ('transfer_in', 'Transfer In'),
            ('transfer_out', 'Transfer Out'),
        ]
        # Set payment method choices
        self.fields['payment_method'].choices = [
            ('', '-- Select --'),
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
            ('cheque', 'Cheque'),
        ]


class DepositForm(forms.Form):
    """Quick deposit form for modal."""
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'anna-form-input',
            'min': '1',
            'step': '100',
            'placeholder': 'Enter amount',
            'autofocus': 'autofocus'
        }),
        validators=[MinValueValidator(Decimal('1'))],
        label="Amount (TZS)"
    )
    customer_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Customer name'})
    )
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Customer phone'})
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        widget=forms.Select(attrs={'class': 'anna-form-input'})
    )
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Reference number'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2, 'placeholder': 'Notes'})
    )


class WithdrawalForm(forms.Form):
    """Quick withdrawal form for modal."""
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'anna-form-input',
            'min': '1',
            'step': '100',
            'placeholder': 'Enter amount',
            'autofocus': 'autofocus'
        }),
        validators=[MinValueValidator(Decimal('1'))],
        label="Amount (TZS)"
    )
    customer_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Customer name'})
    )
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Customer phone'})
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        widget=forms.Select(attrs={'class': 'anna-form-input'})
    )
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'anna-form-input', 'placeholder': 'Reference number'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'anna-form-input', 'rows': 2, 'placeholder': 'Notes'})
    )
