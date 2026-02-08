"""
Audit logging service for ANNA platform.

Provides comprehensive audit logging for all critical financial actions.
"""
import json
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import AuditLog

User = get_user_model()


class AuditLogger:
    """
    Service class for logging audit events.
    
    Usage:
        AuditLogger.log(
            user=request.user,
            action='create',
            content_object=transaction,
            description='Created new deposit transaction',
            request=request
        )
    """
    
    @staticmethod
    def log(user, action, content_object=None, description='', 
            old_values=None, new_values=None, metadata=None, request=None):
        """
        Log an audit event.
        
        Args:
            user: The user performing the action
            action: The action type (from ACTION_CHOICES)
            content_object: The object being acted upon (optional)
            description: Human-readable description
            old_values: Previous state (for updates)
            new_values: New state (for updates)
            metadata: Additional context data
            request: The HTTP request (for IP, user agent)
        """
        from django.utils import timezone
        
        kwargs = {
            'user': user,
            'action': action,
            'description': description,
        }
        
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            kwargs['content_type'] = content_type
            kwargs['object_id'] = str(content_object.pk)
        
        if old_values:
            kwargs['old_values'] = old_values if isinstance(old_values, dict) else {}
        if new_values:
            kwargs['new_values'] = new_values if isinstance(new_values, dict) else {}
        if metadata:
            kwargs['metadata'] = metadata if isinstance(metadata, dict) else {}
        
        if request:
            kwargs['ip_address'] = AuditLogger.get_client_ip(request)
            kwargs['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        AuditLog.objects.create(**kwargs)
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    @transaction.atomic
    def log_transaction(user, transaction, action='record_transaction', request=None):
        """
        Log a financial transaction event with full details.
        
        Args:
            user: The user recording the transaction
            transaction: The Transaction instance
            action: The action type
            request: The HTTP request
        """
        old_values = {}
        new_values = {
            'amount': str(transaction.amount),
            'transaction_type': transaction.transaction_type,
            'wakala_id': str(transaction.wakala_id),
            'financial_day_id': str(transaction.financial_day_id),
        }
        
        metadata = {
            'timestamp': timezone.now().isoformat(),
            'transaction_code': transaction.transaction_code,
        }
        
        AuditLogger.log(
            user=user,
            action=action,
            content_object=transaction,
            description=f"Transaction {transaction.transaction_code}: {transaction.get_transaction_type_display()} of {transaction.amount}",
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            request=request
        )
    
    @staticmethod
    @transaction.atomic
    def log_day_open_close(user, financial_day, action, request=None):
        """
        Log a financial day open/close event.
        
        Args:
            user: The user performing the action
            financial_day: The FinancialDay instance
            action: 'open_day' or 'close_day'
            request: The HTTP request
        """
        new_values = {
            'wakala_id': str(financial_day.wakala_id),
            'date': str(financial_day.date),
            'status': financial_day.status,
            'opening_balance': str(financial_day.opening_balance),
            'closing_balance': str(financial_day.closing_balance),
        }
        
        AuditLogger.log(
            user=user,
            action=action,
            content_object=financial_day,
            description=f"Financial day {action.replace('_', ' ')} for {financial_day.date}",
            new_values=new_values,
            request=request
        )
    
    @staticmethod
    def get_logs_for_object(content_object):
        """Get all audit logs for a specific object."""
        content_type = ContentType.objects.get_for_model(content_object)
        return AuditLog.objects.filter(
            content_type=content_type,
            object_id=str(content_object.pk)
        ).order_by('-timestamp')
    
    @staticmethod
    def get_user_activity(user, limit=100):
        """Get recent activity for a specific user."""
        return AuditLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:limit]
