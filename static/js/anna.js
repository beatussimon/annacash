/**
 * ANNA Platform JavaScript
 * =======================
 * Progressive enhancement for mobile usability and interactivity.
 * Core functionality works without JS.
 */

(function() {
    'use strict';

    // ==========================================================================
    // Mobile Utilities
    // ==========================================================================

    /**
     * Detect if device is mobile
     */
    function isMobile() {
        return window.innerWidth < 768;
    }

    /**
     * Detect if device supports touch
     */
    function isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    // Add mobile class to body for CSS targeting
    if (isMobile()) {
        document.body.classList.add('anna-mobile');
    }

    if (isTouchDevice()) {
        document.body.classList.add('anna-touch');
    }

    // ==========================================================================
    // Form Enhancements
    // ==========================================================================

    /**
     * Auto-focus first input in modals for better UX
     */
    const modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.addEventListener('shown.bs.modal', function() {
            const input = modal.querySelector('input[autofocus]');
            if (input) {
                input.focus();
            }
        });
    });

    /**
     * Confirm before irreversible actions
     */
    const confirmActions = document.querySelectorAll('[data-confirm]');
    confirmActions.forEach(function(element) {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (message && !confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // ==========================================================================
    // Loading States
    // ==========================================================================

    /**
     * Show loading state on form submission
     */
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.queryElement('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
                
                // Restore after 5 seconds (fallback)
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });

    // ==========================================================================
    // Transaction Quick Entry
    // ==========================================================================

    /**
     * Quick amount entry with common values
     */
    const quickAmountBtns = document.querySelectorAll('[data-quick-amount]');
    quickAmountBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const amount = this.getAttribute('data-quick-amount');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                targetInput.value = amount;
                targetInput.focus();
            }
        });
    });

    // ==========================================================================
    // Alert Auto-dismiss
    // ==========================================================================

    /**
     * Auto-dismiss alerts after 5 seconds
     */
    const alerts = document.querySelectorAll('.anna-alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert.classList.contains('fade-in')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        }, 5000);
    });

    // ==========================================================================
    // Sidebar Toggle for Mobile
    // ==========================================================================

    /**
     * Toggle sidebar on mobile if present
     */
    const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector(this.getAttribute('data-sidebar-toggle'));
            if (sidebar) {
                sidebar.classList.toggle('anna-sidebar-open');
            }
        });
    }

    // ==========================================================================
    // Print Functionality
    // ==========================================================================

    /**
     * Print current page
     */
    const printBtns = document.querySelectorAll('[data-print]');
    printBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            window.print();
        });
    });

    // ==========================================================================
    // Number Formatting
    // ==========================================================================

    /**
     * Format currency amounts on page load
     */
    function formatCurrencyElements() {
        const currencyElements = document.querySelectorAll('[data-currency]');
        currencyElements.forEach(function(el) {
            const value = parseFloat(el.getAttribute('data-currency'));
            if (!isNaN(value)) {
                el.textContent = new Intl.NumberFormat('sw-TZ', {
                    style: 'currency',
                    currency: 'TZS',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(value);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', formatCurrencyElements);
    } else {
        formatCurrencyElements();
    }

    // ==========================================================================
    // Chart Initialization Helper
    // ==========================================================================

    /**
     * Initialize charts if Chart.js is available
     */
    function initCharts() {
        if (typeof Chart === 'undefined') return;

        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(function(el) {
            const config = JSON.parse(el.getAttribute('data-chart'));
            new Chart(el, config);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCharts);
    } else {
        initCharts();
    }

    // ==========================================================================
    // Accessibility Enhancements
    // ==========================================================================

    /**
     * Improve focus visibility for keyboard navigation
     */
    document.addEventListener('keyup', function(e) {
        if (e.key === 'Escape') {
            // Close any open modals
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });

    /**
     * Add aria-labels to icon-only buttons
     */
    const iconButtons = document.querySelectorAll('.anna-btn-icon');
    iconButtons.forEach(function(btn) {
        if (!btn.hasAttribute('aria-label')) {
            const icon = btn.querySelector('i');
            if (icon) {
                const iconClass = icon.className.replace('bi ', '').replace(' ', '-');
                btn.setAttribute('aria-label', iconClass);
            }
        }
    });

    // ==========================================================================
    // Local Storage Utilities
    // ==========================================================================

    const AnnaStorage = {
        get: function(key, defaultValue) {
            try {
                const item = localStorage.getItem('anna_' + key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                return defaultValue;
            }
        },
        set: function(key, value) {
            try {
                localStorage.setItem('anna_' + key, JSON.stringify(value));
            } catch (e) {
                // LocalStorage not available
            }
        },
        remove: function(key) {
            try {
                localStorage.removeItem('anna_' + key);
            } catch (e) {
                // LocalStorage not available
            }
        }
    };

    // Expose globally
    window.AnnaStorage = AnnaStorage;

    // ==========================================================================
    // API Utilities
    // ==========================================================================

    const AnnaAPI = {
        /**
         * Make a POST request with CSRF token
         */
        post: function(url, data) {
            const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]');
            const headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            };
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken.value;
            }
            
            return fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            }).then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            });
        }
    };

    // Expose globally
    window.AnnaAPI = AnnaAPI;

})();
