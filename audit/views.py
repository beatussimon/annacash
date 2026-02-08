"""
Audit views for ANNA platform.
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseForbidden


@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_reports(request):
    """System statistics and reports."""
    return render(request, 'audit/reports.html', {
        'page_title': 'System Reports',
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_log(request):
    """View audit log."""
    return render(request, 'audit/log.html', {
        'page_title': 'Audit Log',
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_alerts(request):
    """View system alerts."""
    return render(request, 'audit/alerts.html', {
        'page_title': 'System Alerts',
    })
