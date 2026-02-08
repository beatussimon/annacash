/*
ANNA Platform Chart.js Configurations
=====================================
Analytics charts for dashboards.
*/

(function() {
    'use strict';
    
    // ==========================================================================
    // DEFAULT CHART CONFIGURATION
    // ==========================================================================
    
    // Set default font
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#64748b';
    
    // Set default colors
    const colors = {
        primary: '#1a5f7a',
        secondary: '#159895',
        accent: '#57c5b6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#3b82f6',
        gray: '#64748b'
    };
    
    // ==========================================================================
    // CHART FACTORY
    // ==========================================================================
    
    /**
     * Create a line chart for balance trends
     */
    function createBalanceChart(ctx, data) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Balance',
                    data: data.values || [],
                    borderColor: colors.primary,
                    backgroundColor: colors.primary + '20',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#f1f5f9',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return 'TZS ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#e2e8f0'
                        },
                        ticks: {
                            callback: function(value) {
                                return 'TZS ' + (value / 1000) + 'k';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Create a bar chart for transaction types
     */
    function createTransactionBarChart(ctx, data) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || ['Deposits', 'Withdrawals'],
                datasets: [{
                    label: 'Amount',
                    data: data.values || [0, 0],
                    backgroundColor: [colors.success, colors.danger],
                    borderRadius: 6,
                    barThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return 'TZS ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e2e8f0'
                        },
                        ticks: {
                            callback: function(value) {
                                return 'TZS ' + (value / 1000) + 'k';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Create a doughnut chart for group contributions
     */
    function createContributionChart(ctx, data) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Collected', 'Remaining'],
                datasets: [{
                    data: data || [0, 100],
                    backgroundColor: [colors.success, '#e2e8f0'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return context.label + ': TZS ' + context.parsed.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Create a chart for weekly activity
     */
    function createActivityChart(ctx, data) {
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const values = data || [0, 0, 0, 0, 0, 0, 0];
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: days,
                datasets: [{
                    label: 'Transactions',
                    data: values,
                    backgroundColor: colors.primary,
                    borderRadius: 4,
                    barThickness: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e2e8f0'
                        },
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    // ==========================================================================
    // EXPORT
    // ==========================================================================
    
    window.annaCharts = {
        colors: colors,
        createBalanceChart: createBalanceChart,
        createTransactionBarChart: createTransactionBarChart,
        createContributionChart: createContributionChart,
        createActivityChart: createActivityChart
    };
    
})();
