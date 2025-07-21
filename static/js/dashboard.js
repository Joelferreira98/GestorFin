// Dashboard JavaScript - Sistema Financeiro

let dashboardCharts = {};
let dashboardData = null;
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setupDashboardRefresh();
    setupDateFilters();
});

function loadDashboardData() {
    showLoading();
    
    fetch('/api/dashboard')
        .then(response => response.json())
        .then(data => {
            if (data.stats) {
                dashboardData = data;
                renderDashboardStats(data.stats);
                renderRecentActivities(data.recent_activities);
                renderUpcomingItems(data.upcoming);
                loadDashboardCharts();
            } else {
                showToast(data.error || 'Erro ao carregar dados do dashboard', 'error');
            }
        })
        .catch(error => {
            showToast('Erro de conexão ao carregar dashboard', 'error');
            console.error('Dashboard load error:', error);
        })
        .finally(() => {
            hideLoading();
        });
}

function renderDashboardStats(stats) {
    const statsContainer = document.getElementById('statsCards');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <div class="col-md-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="card-title">Total Clientes</h6>
                            <h4 class="mb-0">${stats.total_clients}</h4>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-users fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="card-title">A Receber</h6>
                            <h4 class="mb-0">${stats.total_receivables_formatted}</h4>
                            <small class="opacity-75">Pendente</small>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-arrow-up fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card bg-danger text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="card-title">Vencidas</h6>
                            <h4 class="mb-0">${stats.overdue_receivables_formatted}</h4>
                            <small class="opacity-75">Em atraso</small>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-exclamation-triangle fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="card-title">A Pagar</h6>
                            <h4 class="mb-0">${stats.total_payables_formatted}</h4>
                            <small class="opacity-75">Pendente</small>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-arrow-down fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-12 mt-3">
            <div class="card">
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-md-4">
                            <h6 class="text-muted">Fluxo de Caixa</h6>
                            <h4 class="${stats.cash_flow >= 0 ? 'text-success' : 'text-danger'}">
                                ${stats.cash_flow_formatted}
                            </h4>
                        </div>
                        <div class="col-md-4">
                            <h6 class="text-muted">Recebido</h6>
                            <h4 class="text-success">${stats.paid_receivables_formatted}</h4>
                        </div>
                        <div class="col-md-4">
                            <h6 class="text-muted">Este Mês</h6>
                            <h4 class="text-info">${stats.monthly_receivables_formatted}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderRecentActivities(activities) {
    if (!activities) return;
    
    renderRecentReceivables(activities.receivables || []);
    renderRecentPayables(activities.payables || []);
    renderRecentSales(activities.sales || []);
}

function renderRecentReceivables(receivables) {
    const container = document.getElementById('recentReceivables');
    if (!container) return;
    
    if (receivables.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhuma atividade recente</p>';
        return;
    }
    
    container.innerHTML = receivables.map(item => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
            <div>
                <div class="fw-semibold">${item.description}</div>
                <small class="text-muted">${item.client_name}</small>
            </div>
            <div class="text-end">
                <div class="fw-bold text-success">${item.amount_formatted}</div>
                <small class="text-muted">${formatDate(item.due_date)}</small>
            </div>
        </div>
    `).join('');
}

function renderRecentPayables(payables) {
    const container = document.getElementById('recentPayables');
    if (!container) return;
    
    if (payables.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhuma atividade recente</p>';
        return;
    }
    
    container.innerHTML = payables.map(item => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
            <div>
                <div class="fw-semibold">${item.description}</div>
                <small class="text-muted">${item.supplier_name}</small>
            </div>
            <div class="text-end">
                <div class="fw-bold text-danger">${item.amount_formatted}</div>
                <small class="text-muted">${formatDate(item.due_date)}</small>
            </div>
        </div>
    `).join('');
}

function renderRecentSales(sales) {
    const container = document.getElementById('recentSales');
    if (!container) return;
    
    if (sales.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhuma venda recente</p>';
        return;
    }
    
    container.innerHTML = sales.map(item => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
            <div>
                <div class="fw-semibold">${item.description}</div>
                <small class="text-muted">${item.client_name}</small>
            </div>
            <div class="text-end">
                <div class="fw-bold text-primary">${item.total_amount_formatted}</div>
                <small class="text-muted">
                    <span class="badge ${getStatusBadgeClass(item.status)}">${getStatusText(item.status)}</span>
                </small>
            </div>
        </div>
    `).join('');
}

function renderUpcomingItems(upcoming) {
    if (!upcoming) return;
    
    renderUpcomingReceivables(upcoming.receivables || []);
    renderUpcomingPayables(upcoming.payables || []);
}

function renderUpcomingReceivables(receivables) {
    const container = document.getElementById('upcomingReceivables');
    if (!container) return;
    
    if (receivables.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhum vencimento próximo</p>';
        return;
    }
    
    container.innerHTML = receivables.map(item => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom ${item.is_overdue ? 'bg-light-danger' : ''}">
            <div>
                <div class="fw-semibold">${item.description}</div>
                <small class="text-muted">${item.client_name}</small>
            </div>
            <div class="text-end">
                <div class="fw-bold ${item.is_overdue ? 'text-danger' : 'text-success'}">
                    ${item.amount_formatted}
                </div>
                <small class="${item.is_overdue ? 'text-danger' : 'text-muted'}">
                    ${item.is_overdue ? 'VENCIDO' : `${item.days_until_due} dias`}
                </small>
            </div>
        </div>
    `).join('');
}

function renderUpcomingPayables(payables) {
    const container = document.getElementById('upcomingPayables');
    if (!container) return;
    
    if (payables.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhum vencimento próximo</p>';
        return;
    }
    
    container.innerHTML = payables.map(item => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom ${item.is_overdue ? 'bg-light-warning' : ''}">
            <div>
                <div class="fw-semibold">${item.description}</div>
                <small class="text-muted">${item.supplier_name}</small>
            </div>
            <div class="text-end">
                <div class="fw-bold ${item.is_overdue ? 'text-danger' : 'text-warning'}">
                    ${item.amount_formatted}
                </div>
                <small class="${item.is_overdue ? 'text-danger' : 'text-muted'}">
                    ${item.is_overdue ? 'VENCIDO' : `${item.days_until_due} dias`}
                </small>
            </div>
        </div>
    `).join('');
}

function loadDashboardCharts() {
    loadCashFlowChart();
    loadStatusChart();
}

function loadCashFlowChart() {
    fetch('/api/dashboard/chart-data?type=monthly')
        .then(response => response.json())
        .then(data => {
            if (data.chart_data) {
                renderCashFlowChart(data.chart_data);
            }
        })
        .catch(error => {
            console.error('Error loading cash flow chart:', error);
        });
}

function renderCashFlowChart(data) {
    const ctx = document.getElementById('cashFlowChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (dashboardCharts.cashFlow) {
        dashboardCharts.cashFlow.destroy();
    }
    
    dashboardCharts.cashFlow = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.month_name),
            datasets: [
                {
                    label: 'A Receber',
                    data: data.map(item => item.receivables),
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'A Pagar',
                    data: data.map(item => item.payables),
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Saldo',
                    data: data.map(item => item.net),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: false,
                    tension: 0.3,
                    borderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.raw);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Mês'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Valor (R$)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

function loadStatusChart() {
    fetch('/api/dashboard/chart-data?type=status')
        .then(response => response.json())
        .then(data => {
            if (data.status_data) {
                renderStatusChart(data.status_data);
            }
        })
        .catch(error => {
            console.error('Error loading status chart:', error);
        });
}

function renderStatusChart(data) {
    const ctx = document.getElementById('statusChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (dashboardCharts.status) {
        dashboardCharts.status.destroy();
    }
    
    const colors = {
        'pending': '#ffc107',
        'paid': '#28a745',
        'overdue': '#dc3545'
    };
    
    dashboardCharts.status = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => getStatusText(item.status)),
            datasets: [{
                data: data.map(item => item.amount),
                backgroundColor: data.map(item => colors[item.status] || '#6c757d'),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label;
                            const value = formatCurrency(context.raw);
                            const count = data[context.dataIndex].count;
                            return `${label}: ${value} (${count} contas)`;
                        }
                    }
                }
            }
        }
    });
}

function setupDashboardRefresh() {
    // Auto-refresh every 5 minutes
    refreshInterval = setInterval(() => {
        loadDashboardData();
    }, 5 * 60 * 1000);
    
    // Refresh when page becomes visible
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            loadDashboardData();
        }
    });
}

function refreshDashboard() {
    loadDashboardData();
    showToast('Dashboard atualizado', 'success', 2000);
}

function setupDateFilters() {
    const dateFilters = document.querySelectorAll('[data-date-filter]');
    dateFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            const period = this.value;
            loadDashboardWithPeriod(period);
        });
    });
}

function loadDashboardWithPeriod(period) {
    showLoading();
    
    fetch(`/api/dashboard?period=${period}`)
        .then(response => response.json())
        .then(data => {
            if (data.stats) {
                renderDashboardStats(data.stats);
                loadDashboardCharts();
            }
        })
        .catch(error => {
            showToast('Erro ao filtrar dados', 'error');
        })
        .finally(() => {
            hideLoading();
        });
}

function getStatusText(status) {
    const statusMap = {
        'pending': 'Pendente',
        'paid': 'Pago',
        'overdue': 'Vencido',
        'confirmed': 'Confirmado',
        'approved': 'Aprovado',
        'rejected': 'Rejeitado'
    };
    return statusMap[status] || status;
}

function getStatusBadgeClass(status) {
    const classMap = {
        'pending': 'bg-warning',
        'paid': 'bg-success',
        'overdue': 'bg-danger',
        'confirmed': 'bg-info',
        'approved': 'bg-success',
        'rejected': 'bg-danger'
    };
    return classMap[status] || 'bg-secondary';
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Destroy charts
    Object.values(dashboardCharts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
});

// Export functions
window.refreshDashboard = refreshDashboard;
window.loadDashboardWithPeriod = loadDashboardWithPeriod;
