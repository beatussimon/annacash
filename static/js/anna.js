/*
ANNA Platform JavaScript
=========================
Interactive functionality for the ANNA financial platform.
*/

(function() {
    'use strict';
    
    // ==========================================================================
    // GLOBAL ANNA OBJECT
    // ==========================================================================
    
    window.anna = window.anna || {};
    
    // ==========================================================================
    // FORM UTILITIES
    // ==========================================================================
    
    /**
     * Handle form submission confirmation for irreversible actions
     */
    anna.confirmAction = function(message, onConfirm) {
        if (confirm(message)) {
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
            return true;
        }
        return false;
    };
    
    /**
     * Show confirmation modal for destructive actions
     */
    anna.showConfirmModal = function(options) {
        const {
            title = 'Confirm Action',
            message = 'Are you sure?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            confirmClass = 'anna-btn-danger',
            onConfirm = null
        } = options;
        
        // Create modal if it doesn't exist
        let modal = document.getElementById('annaConfirmModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'annaConfirmModal';
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="anna-btn anna-btn-secondary" data-bs-dismiss="modal">${cancelText}</button>
                            <button type="button" class="anna-btn ${confirmClass}" id="annaConfirmBtn">${confirmText}</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Handle confirm
        document.getElementById('annaConfirmBtn').onclick = function() {
            bsModal.hide();
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        };
    };
    
    // ==========================================================================
    // KEYBOARD SHORTCUTS
    // ==========================================================================
    
    /**
     * Register keyboard shortcuts
     */
    anna.registerShortcut = function(key, callback, options = {}) {
        const {
            ctrl = false,
            shift = false,
            alt = false,
            meta = false
        } = options;
        
        document.addEventListener('keydown', function(e) {
            const keyMatch = e.key.toLowerCase() === key.toLowerCase();
            const ctrlMatch = ctrl === (e.ctrlKey || e.metaKey);
            const shiftMatch = shift === e.shiftKey;
            const altMatch = alt === e.altKey;
            
            if (keyMatch && ctrlMatch && shiftMatch === altMatch) {
                e.preventDefault();
                callback(e);
            }
        });
    };
    
    /**
     * Initialize default shortcuts
     */
    anna.initShortcuts = function() {
        // Ctrl+Enter to submit forms
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    form.submit();
                }
            });
        });
    };
    
    // ==========================================================================
    // LIVE BALANCE UPDATES (HTMX-compatible)
    // ==========================================================================
    
    /**
     * Poll for balance updates
     */
    anna.startBalancePolling = function(url, interval = 5000) {
        const updateBalance = function() {
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const elements = document.querySelectorAll('[data-anna-balance]');
                    elements.forEach(el => {
                        el.textContent = data.balance;
                    });
                })
                .catch(() => {
                    // Silently fail - balance updates are not critical
                });
        };
        
        updateBalance();
        setInterval(updateBalance, interval);
    };
    
    // ==========================================================================
    // TRANSACTION HELPERS
    // ==========================================================================
    
    /**
     * Format TZS amount
     */
    anna.formatTZS = function(amount) {
        const num = parseFloat(amount) || 0;
        return 'TZS ' + num.toLocaleString('en-US');
    };
    
    /**
     * Validate amount input
     */
    anna.validateAmount = function(input, min = 1) {
        const value = parseFloat(input.value);
        if (isNaN(value) || value < min) {
            input.classList.add('is-invalid');
            return false;
        }
        input.classList.remove('is-invalid');
        return true;
    };
    
    // ==========================================================================
    // INITIALIZATION
    // ==========================================================================
    
    document.addEventListener('DOMContentLoaded', function() {
        anna.initShortcuts();
        
        // Initialize tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        popoverTriggerList.forEach(popoverTriggerEl => {
            new bootstrap.Popover(popoverTriggerEl);
        });
    });
    
})();
