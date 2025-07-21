// Charts Configuration and Utilities - Sistema Financeiro

// Global Chart.js configuration
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#6c757d';

// Chart color palette
const CHART_COLORS = {
    primary: '#007bff',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    light: '#f8f9fa',
    dark: '#343a40',
    
    // Gradient colors
    gradients: {
        primary: ['#667eea', '#764ba2'],
        success: ['#4CAF50', '#45a049'],
        danger: ['#FF5722', '#E91E63'],
        warning: ['#FFB74D', '#FF9800'],
        info: ['#29B6F6', '#1976D2']
    }
};

// Chart utilities
const ChartUtils = {
    // Create gradient
    createGradient: function(ctx, color1, color2, direction = 'vertical') {
        let gradient;
        
        if (direction === 'vertical') {
            gradient = ctx.createLinearGradient(0, 0, 0, 400);
        } else {
            gradient = ctx.createLinearGradient(0, 0, 400, 0);
        }
        
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        
        return gradient;
    },
    
    // Format currency for tooltips
    formatCurrency: function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },
    
    // Format percentage
    formatPercentage: function(value) {
        return value.toFixed(1) + '%';
    },
    
    // Get month name
    getMonthName: function(monthIndex) {
        const months = [
            'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
        ];
        return months[monthIndex];
    },
    
    // Generate random color
    generateColor: function(alpha = 1) {
        const hue = Math.floor(Math.random() * 360);
        return `hsla(${hue}, 70%, 60%, ${alpha})`;
    },
    
    // Get status color
    getStatusColor: function(status) {
        const colors = {
            'pending': CHART_COLORS.warning,
            'paid': CHART_COLORS.success,
            'overdue': CHART_COLORS.danger,
            'confirmed': CHART_COLORS.info,
            'approved': CHART_COLORS.success,
            'rejected': CHART_COLORS.danger
        };
        return colors[status] || CHART_COLORS.light;
    }
};

// Default chart options
const DEFAULT_CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        intersect: false,
    },
    plugins: {
        legend: {
            labels: {
                usePointStyle: true,
                padding: 20
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: 'white',
            bodyColor: 'white',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: true
        }
    },
    scales: {
        x: {
            grid: {
                display: false
            },
            ticks: {
                color: '#6c757d'
            }
        },
        y: {
            grid: {
                color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
                color: '#6c757d'
            }
        }
    }
};

// Chart factory functions
const ChartFactory = {
    // Create line chart
    createLineChart: function(ctx, data, options = {}) {
        const config = {
            type: 'line',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                ...options,
                scales: {
                    ...DEFAULT_CHART_OPTIONS.scales,
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true,
                        ticks: {
                            ...DEFAULT_CHART_OPTIONS.scales.y.ticks,
                            callback: function(value) {
                                return ChartUtils.formatCurrency(value);
                            }
                        }
                    }
                },
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    tooltip: {
                        ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + ChartUtils.formatCurrency(context.raw);
                            }
                        }
                    }
                }
            }
        };
        
        return new Chart(ctx, config);
    },
    
    // Create bar chart
    createBarChart: function(ctx, data, options = {}) {
        const config = {
            type: 'bar',
            data: data,
            options: {
                ...DEFAULT_CHART_OPTIONS,
                ...options,
                scales: {
                    ...DEFAULT_CHART_OPTIONS.scales,
                    y: {
                        ...DEFAULT_CHART_OPTIONS.scales.y,
                        beginAtZero: true,
                        ticks: {
                            ...DEFAULT_CHART_OPTIONS.scales.y.ticks,
                            callback: function(value) {
                                return ChartUtils.formatCurrency(value);
                            }
                        }
                    }
                },
                plugins: {
                    ...DEFAULT_CHART_OPTIONS.plugins,
                    tooltip: {
                        ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + ChartUtils.formatCurrency(context.raw);
                            }
                        }
                    }
                }
            }
        };
        
        return new Chart(ctx, config);
    },
    
    // Create pie/doughnut chart
    createPieChart: function(ctx, data, options = {}, isDoughnut = false) {
        const config = {
            type: isDoughnut ? 'doughnut' : 'pie',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: options.legendPosition || 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const label = context.label;
                                const value = ChartUtils.formatCurrency(context.raw);
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                ...options
            }
        };
        
        return new Chart(ctx, config);
    },
    
    // Create area chart
    createAreaChart: function(ctx, data, options = {}) {
        // Ensure all datasets have fill: true
        data.datasets.forEach(dataset => {
            dataset.fill = dataset.fill !== undefined ? dataset.fill : true;
            dataset.tension = dataset.tension || 0.3;
        });
        
        return this.createLineChart(ctx, data, options);
    }
};

// Specific chart creators
const FinancialCharts = {
    // Cash flow chart
    createCashFlowChart: function(ctx, monthlyData) {
        const data = {
            labels: monthlyData.map(item => item.month_name || ChartUtils.getMonthName(item.month - 1)),
            datasets: [
                {
                    label: 'A Receber',
                    data: monthlyData.map(item => item.receivables || 0),
                    borderColor: CHART_COLORS.success,
                    backgroundColor: ChartUtils.createGradient(ctx, 
                        'rgba(40, 167, 69, 0.2)', 
                        'rgba(40, 167, 69, 0.05)'
                    ),
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'A Pagar',
                    data: monthlyData.map(item => item.payables || 0),
                    borderColor: CHART_COLORS.danger,
                    backgroundColor: ChartUtils.createGradient(ctx, 
                        'rgba(220, 53, 69, 0.2)', 
                        'rgba(220, 53, 69, 0.05)'
                    ),
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Saldo Líquido',
                    data: monthlyData.map(item => (item.receivables || 0) - (item.payables || 0)),
                    borderColor: CHART_COLORS.primary,
                    backgroundColor: 'transparent',
                    fill: false,
                    tension: 0.3,
                    borderWidth: 3
                }
            ]
        };
        
        return ChartFactory.createLineChart(ctx, data);
    },
    
    // Revenue chart
    createRevenueChart: function(ctx, revenueData) {
        const data = {
            labels: revenueData.map(item => item.period),
            datasets: [{
                label: 'Receita',
                data: revenueData.map(item => item.amount),
                backgroundColor: ChartUtils.createGradient(ctx, 
                    CHART_COLORS.gradients.success[0], 
                    CHART_COLORS.gradients.success[1]
                ),
                borderColor: CHART_COLORS.success,
                borderWidth: 2
            }]
        };
        
        return ChartFactory.createBarChart(ctx, data);
    },
    
    // Status distribution chart
    createStatusChart: function(ctx, statusData) {
        const data = {
            labels: statusData.map(item => {
                const statusLabels = {
                    'pending': 'Pendente',
                    'paid': 'Pago',
                    'overdue': 'Vencido'
                };
                return statusLabels[item.status] || item.status;
            }),
            datasets: [{
                data: statusData.map(item => item.amount),
                backgroundColor: statusData.map(item => ChartUtils.getStatusColor(item.status)),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        };
        
        return ChartFactory.createPieChart(ctx, data, {}, true);
    },
    
    // Client ranking chart
    createClientRankingChart: function(ctx, clientData) {
        const data = {
            labels: clientData.map(item => item.client_name.length > 15 ? 
                item.client_name.substring(0, 12) + '...' : 
                item.client_name
            ),
            datasets: [{
                label: 'Valor Total',
                data: clientData.map(item => item.total_amount),
                backgroundColor: clientData.map((_, index) => 
                    `hsl(${(index * 360) / clientData.length}, 70%, 60%)`
                ),
                borderWidth: 0
            }]
        };
        
        const options = {
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            }
        };
        
        return ChartFactory.createBarChart(ctx, data, options);
    },
    
    // Growth chart
    createGrowthChart: function(ctx, growthData) {
        const data = {
            labels: growthData.map(item => item.period),
            datasets: [{
                label: 'Crescimento (%)',
                data: growthData.map(item => item.growth_percentage),
                borderColor: CHART_COLORS.info,
                backgroundColor: ChartUtils.createGradient(ctx, 
                    'rgba(23, 162, 184, 0.1)', 
                    'rgba(23, 162, 184, 0.05)'
                ),
                fill: true,
                tension: 0.4
            }]
        };
        
        const options = {
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Crescimento: ' + context.raw + '%';
                        }
                    }
                }
            }
        };
        
        return ChartFactory.createLineChart(ctx, data, options);
    }
};

// Chart management utilities
const ChartManager = {
    charts: {},
    
    // Register a chart
    register: function(id, chart) {
        this.charts[id] = chart;
    },
    
    // Get a chart by ID
    get: function(id) {
        return this.charts[id];
    },
    
    // Destroy a chart
    destroy: function(id) {
        if (this.charts[id]) {
            this.charts[id].destroy();
            delete this.charts[id];
        }
    },
    
    // Destroy all charts
    destroyAll: function() {
        Object.keys(this.charts).forEach(id => {
            this.destroy(id);
        });
    },
    
    // Update chart data
    updateData: function(id, newData) {
        const chart = this.charts[id];
        if (chart) {
            chart.data = newData;
            chart.update('none'); // No animation for better performance
        }
    },
    
    // Resize all charts
    resizeAll: function() {
        Object.values(this.charts).forEach(chart => {
            chart.resize();
        });
    }
};

// Responsive chart handling
window.addEventListener('resize', () => {
    ChartManager.resizeAll();
});

// Export for global use
window.ChartUtils = ChartUtils;
window.ChartFactory = ChartFactory;
window.FinancialCharts = FinancialCharts;
window.ChartManager = ChartManager;
window.CHART_COLORS = CHART_COLORS;
