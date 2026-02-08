"""
Configuration models for ANNA platform.

Contains all configurable items like networks, banks, fee rules, etc.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Network(models.Model):
    """
    Mobile money network (e.g., M-Pesa, Tigo Pesa, Airtel Money).
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    
    # Contact information
    hotline = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Settings
    ussd_code = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Network'
        verbose_name_plural = 'Networks'
        ordering = ['name']

    def __str__(self):
        return self.name


class Bank(models.Model):
    """
    Bank configuration for bank transfers.
    """
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Contact information
    headquarters = models.CharField(max_length=200, blank=True)
    hotline = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # SWIFT/BIC code for international transfers
    swift_code = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class FeeRule(models.Model):
    """
    Fee rules for transactions.
    
    Defines fees based on transaction type, amount, and other criteria.
    """
    FEE_TYPES = [
        ('flat', 'Flat Fee'),
        ('percentage', 'Percentage Fee'),
        ('tiered', 'Tiered Fee'),
        ('fixed_plus', 'Fixed Plus Percentage'),
    ]
    
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('all', 'All Transactions'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Application criteria
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    network = models.ForeignKey(
        Network,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fee_rules'
    )
    bank = models.ForeignKey(
        Bank,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fee_rules'
    )
    
    # Fee calculation
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES)
    flat_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    percentage_fee = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage as decimal (e.g., 0.5 for 0.5%)"
    )
    
    # Min/Max constraints
    min_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    max_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Amount range
    min_transaction_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    max_transaction_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Higher priority rules are applied first"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fee Rule'
        verbose_name_plural = 'Fee Rules'
        ordering = ['-priority']
    
    def __str__(self):
        return f"{self.name} ({self.get_transaction_type_display()})"
    
    def calculate_fee(self, amount):
        """Calculate fee for a given amount."""
        if self.fee_type == 'flat':
            fee = self.flat_fee
        elif self.fee_type == 'percentage':
            fee = amount * self.percentage_fee
        elif self.fee_type == 'fixed_plus_percentage':
            fee = self.flat_fee + (amount * self.percentage_fee)
        else:
            fee = 0
        
        # Apply min/max constraints
        if self.min_fee and fee < self.min_fee:
            fee = self.min_fee
        if self.max_fee and fee > self.max_fee:
            fee = self.max_fee
        
        return fee


class CommissionRule(models.Model):
    """
    Commission rules for agents.
    
    Defines commissions based on transaction volume, type, etc.
    """
    COMMISSION_TYPES = [
        ('flat', 'Flat Commission'),
        ('percentage', 'Percentage Commission'),
        ('tiered', 'Tiered Commission'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Application criteria
    transaction_type = models.CharField(max_length=20, choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('all', 'All Transactions'),
    ])
    network = models.ForeignKey(
        Network,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules'
    )
    
    # Commission calculation
    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPES)
    flat_commission = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    percentage_commission = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Tiered configuration (JSON)
    tiers = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of tiers: [{'min_amount': 0, 'max_amount': 10000, 'rate': 0.01}]"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Commission Rule'
        verbose_name_plural = 'Commission Rules'
        ordering = ['-priority']
    
    def __str__(self):
        return f"{self.name} ({self.get_transaction_type_display()})"
    
    def calculate_commission(self, amount):
        """Calculate commission for a given amount."""
        if self.commission_type == 'flat':
            return self.flat_commission
        elif self.commission_type == 'percentage':
            return amount * self.percentage_commission
        elif self.commission_type == 'tiered':
            for tier in self.tiers:
                if tier['min_amount'] <= amount <= tier.get('max_amount', float('inf')):
                    return amount * tier.get('rate', 0)
            return 0
        return 0


class Currency(models.Model):
    """
    Currency configuration.
    """
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=5)
    
    # Formatting
    decimal_places = models.PositiveIntegerField(default=2)
    thousand_separator = models.CharField(max_length=2, default=',')
    decimal_separator = models.CharField(max_length=2, default='.')
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
    
    def __str__(self):
        return f"{self.name} ({self.code})"
