"""
Forms for wakala app.
"""

from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.forms import FormStyleMixin
from .models import Transaction


class TransactionForm(FormStyleMixin, forms.ModelForm):
    """Form for creating/editing transactions."""

    amount = forms.DecimalField(
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "any",
                "autofocus": "autofocus",
            }
        ),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "amount",
            "customer_name",
            "customer_phone",
            "customer_reference",
            "payment_method",
            "network",
            "bank",
            "reference_number",
            "description",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set transaction type choices
        self.fields["transaction_type"].choices = [
            ("deposit", "Deposit"),
            ("withdrawal", "Withdrawal"),
            ("transfer_in", "Transfer In"),
            ("transfer_out", "Transfer Out"),
        ]
        # Set payment method choices
        self.fields["payment_method"].choices = [
            ("", "-- Select --"),
            ("cash", "Cash"),
            ("mobile_money", "Mobile Money"),
            ("bank_transfer", "Bank Transfer"),
            ("cheque", "Cheque"),
        ]


class DepositForm(FormStyleMixin, forms.Form):
    """Quick deposit form for modal."""

    amount = forms.DecimalField(
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "any",
                "autofocus": "autofocus",
            }
        ),
        validators=[MinValueValidator(Decimal("0"))],
        label="Amount (TZS)",
    )
    customer_name = forms.CharField(max_length=200, required=False)
    customer_phone = forms.CharField(max_length=20, required=False)
    payment_method = forms.ChoiceField(
        choices=[
            ("cash", "Cash"),
            ("mobile_money", "Mobile Money"),
            ("bank_transfer", "Bank Transfer"),
        ]
    )
    reference_number = forms.CharField(max_length=100, required=False)
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class WithdrawalForm(FormStyleMixin, forms.Form):
    """Quick withdrawal form for modal."""

    amount = forms.DecimalField(
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "any",
                "autofocus": "autofocus",
            }
        ),
        validators=[MinValueValidator(Decimal("0"))],
        label="Amount (TZS)",
    )
    customer_name = forms.CharField(max_length=200, required=False)
    customer_phone = forms.CharField(max_length=20, required=False)
    payment_method = forms.ChoiceField(
        choices=[
            ("cash", "Cash"),
            ("mobile_money", "Mobile Money"),
            ("bank_transfer", "Bank Transfer"),
        ]
    )
    reference_number = forms.CharField(max_length=100, required=False)
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
