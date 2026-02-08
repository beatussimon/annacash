"""
Transaction service for ANNA platform.

Implements the core financial transaction lifecycle with
instant saving, precise timestamping, and audit trails.
"""
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone


class TransactionService:
    """
    Service class for managing financial transactions.
    
    All transactions MUST be:
    - Entered manually by a logged-in user
    - Saved instantly (no drafts, no batching)
    - Timestamped precisely
    - Attributed to the exact user who recorded it
    """
    
    @staticmethod
    @db_transaction.atomic
    def create_transaction(
        user,
        wakala,
        financial_day,
        transaction_type,
        amount,
        payment_method,
        **kwargs
    ):
        """
        Create and save a new transaction instantly.
        
        Args:
            user: The user recording the transaction
            wakala: The wakala business
            financial_day: The financial day
            transaction_type: Type of transaction
            amount: Transaction amount
            payment_method: Payment method used
            **kwargs: Additional transaction fields
            
        Returns:
            Transaction: The created transaction
            
        Raises:
            ValueError: If validation fails
        """
        from wakala.models import Transaction
        from core.services import AuditLogger
        
        # Validate financial day is open
        if financial_day.status != 'open':
            raise ValueError("Cannot record transactions on a closed financial day")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Transaction amount must be positive")
        
        # Create transaction
        txn = Transaction(
            wakala=wakala,
            financial_day=financial_day,
            transaction_type=transaction_type,
            amount=amount,
            payment_method=payment_method,
            created_by=user,
            original_recorder=user,
            **kwargs
        )
        
        txn.full_save()  # This triggers audit fields
        
        # Log the transaction
        AuditLogger.log_transaction(
            user=user,
            transaction=txn,
            action='record_transaction'
        )
        
        return txn
    
    @staticmethod
    @db_transaction.atomic
    def deposit(
        user,
        wakala,
        financial_day,
        amount,
        customer_name='',
        customer_phone='',
        network=None,
        reference_number='',
        **kwargs
    ):
        """
        Record a deposit transaction.
        
        Args:
            user: The user recording the deposit
            wakala: The wakala business
            financial_day: The financial day
            amount: Deposit amount
            customer_name: Customer's name
            customer_phone: Customer's phone
            network: Mobile money network
            reference_number: Payment reference
            
        Returns:
            Transaction: The created deposit transaction
        """
        return TransactionService.create_transaction(
            user=user,
            wakala=wakala,
            financial_day=financial_day,
            transaction_type='deposit',
            amount=amount,
            payment_method='Mobile Money' if network else 'Cash',
            customer_name=customer_name,
            customer_phone=customer_phone,
            network=network,
            reference_number=reference_number,
            **kwargs
        )
    
    @staticmethod
    @db_transaction.atomic
    def withdrawal(
        user,
        wakala,
        financial_day,
        amount,
        customer_name='',
        customer_phone='',
        network=None,
        bank=None,
        reference_number='',
        **kwargs
    ):
        """
        Record a withdrawal transaction.
        
        Args:
            user: The user recording the withdrawal
            wakala: The wakala business
            financial_day: The financial day
            amount: Withdrawal amount
            customer_name: Customer's name
            customer_phone: Customer's phone
            network: Mobile money network
            bank: Bank for bank transfer
            reference_number: Payment reference
            
        Returns:
            Transaction: The created withdrawal transaction
        """
        # Check sufficient balance
        computed_balance = financial_day.calculate_computed_balance()
        if amount > computed_balance:
            raise ValueError("Insufficient balance for withdrawal")
        
        payment_method = 'Bank Transfer' if bank else 'Mobile Money' if network else 'Cash'
        
        return TransactionService.create_transaction(
            user=user,
            wakala=wakala,
            financial_day=financial_day,
            transaction_type='withdrawal',
            amount=amount,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_phone=customer_phone,
            network=network,
            bank=bank,
            reference_number=reference_number,
            **kwargs
        )
    
    @staticmethod
    @db_transaction.atomic
    def transfer_in(
        user,
        wakala,
        financial_day,
        amount,
        customer_name='',
        reference_number='',
        **kwargs
    ):
        """Record an incoming transfer."""
        return TransactionService.create_transaction(
            user=user,
            wakala=wakala,
            financial_day=financial_day,
            transaction_type='transfer_in',
            amount=amount,
            payment_method='Transfer',
            customer_name=customer_name,
            reference_number=reference_number,
            **kwargs
        )
    
    @staticmethod
    @db_transaction.atomic
    def transfer_out(
        user,
        wakala,
        financial_day,
        amount,
        customer_name='',
        reference_number='',
        **kwargs
    ):
        """Record an outgoing transfer."""
        return TransactionService.create_transaction(
            user=user,
            wakala=wakala,
            financial_day=financial_day,
            transaction_type='transfer_out',
            amount=amount,
            payment_method='Transfer',
            customer_name=customer_name,
            reference_number=reference_number,
            **kwargs
        )
