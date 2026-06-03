/**
 * Reports Module - Carrega e renderiza dados de relatórios
 * Endpoints API:
 * - /reports/api/summary/
 * - /reports/api/monthly-trend/
 * - /reports/api/expenses-by-category/
 * - /reports/api/top-expenses/
 * - /reports/api/monthly-summary/
 * - /reports/api/export/
 */

// Color palette for charts
const REPORT_COLORS = {
    primary: '#8A4FFF',
    secondary: '#5E2C9A',
    accent: '#c084fc',
    info: '#6366f1',
    danger: '#ec4899',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
};

// Chart instances
let trendChartInstance = null;
let categoryChartInstance = null;

// Current filter state
let currentPeriod = 'month';
let currentStartDate = null;
let currentEndDate = null;

/**
 * Initialize reports page
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log('Reports page loading...');
    
    loadReportsSummary();
    loadTrendChart();
    loadCategoryChart();
    loadTopExpenses();
    loadMonthlySummary();
    setupEventListeners();
});

/**
 * Setup event listeners for period buttons and date inputs
 */
function setupEventListeners() {
    // Period buttons
    const periodBtns = document.querySelectorAll('.period-btn');
    periodBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            periodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            currentPeriod = this.dataset.period;
            currentStartDate = null;
            currentEndDate = null;
            
            refreshReports();
        });
    });
    
    // Apply custom dates
    const applyBtn = document.getElementById('applyCustomBtn');
    if (applyBtn) {
        applyBtn.addEventListener('click', function () {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            if (!startDate || !endDate) {
                alert('Por favor, selecione ambas as datas');
                return;
            }
            
            currentPeriod = 'custom';
            currentStartDate = startDate;
            currentEndDate = endDate;
            
            // Deselect all period buttons
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            
            refreshReports();
        });
    }
    
    // Export button
    const exportBtn = document.getElementById('exportReportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportReport);
    }
    
    // Category chart type selector
    const chartTypeSelect = document.getElementById('categoryChartType');
    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', function () {
            loadCategoryChart(this.value);
        });
    }
}

/**
 * Refresh all reports with current filters
 */
function refreshReports() {
    loadReportsSummary();
    loadTrendChart();
    loadCategoryChart();
    loadTopExpenses();
    loadMonthlySummary();
}

/**
 * Format currency value
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Load reports summary (top cards)
 */
function loadReportsSummary() {
    const params = new URLSearchParams();
    params.append('period', currentPeriod);
    
    if (currentStartDate) params.append('start_date', currentStartDate);
    if (currentEndDate) params.append('end_date', currentEndDate);
    
    fetch(`/reports/api/summary/?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('Reports Summary:', data);
            
            if (!data.success) {
                console.error('API Error:', data.error);
                return;
            }
            
            const reportData = data.data;
            
            // Update income
            document.getElementById('totalIncome').textContent = formatCurrency(reportData.total_income);
            document.getElementById('incomeTrend').textContent = (reportData.income_change >= 0 ? '+' : '') + reportData.income_change + '%';
            document.getElementById('incomeTrend').classList.remove('positive', 'negative');
            document.getElementById('incomeTrend').classList.add(reportData.income_change >= 0 ? 'positive' : 'negative');
            
            // Update expenses
            document.getElementById('totalExpense').textContent = formatCurrency(reportData.total_expense);
            document.getElementById('expenseTrend').textContent = (reportData.expense_change >= 0 ? '+' : '') + reportData.expense_change + '%';
            document.getElementById('expenseTrend').classList.remove('positive', 'negative');
            document.getElementById('expenseTrend').classList.add(reportData.expense_change >= 0 ? 'positive' : 'negative');
            
            // Update balance
            document.getElementById('totalBalance').textContent = formatCurrency(reportData.balance);
            
            // Update savings rate
            document.getElementById('savingsRate').textContent = reportData.savings_rate + '%';
        })
        .catch(error => console.error('Error loading summary:', error));
}

/**
 * Load trend chart (line chart)
 */
function loadTrendChart() {
    const params = new URLSearchParams();
    params.append('months', 12);
    
    fetch(`/reports/api/monthly-trend/?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('Monthly Trend:', data);
            
            if (!data.success || !data.data) return;
            
            const labels = data.data.map(item => item.month);
            const incomeData = data.data.map(item => item.income);
            const expenseData = data.data.map(item => item.expense);
            
            const canvas = document.getElementById('trendChart');
            if (!canvas) return;
            
            if (trendChartInstance) {
                trendChartInstance.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Receitas',
                            data: incomeData,
                            borderColor: REPORT_COLORS.success,
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 3,
                            tension: 0.4,
                            fill: true,
                            pointRadius: 5,
                            pointBackgroundColor: REPORT_COLORS.success,
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                        },
                        {
                            label: 'Despesas',
                            data: expenseData,
                            borderColor: REPORT_COLORS.error,
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            borderWidth: 3,
                            tension: 0.4,
                            fill: true,
                            pointRadius: 5,
                            pointBackgroundColor: REPORT_COLORS.error,
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: 'rgba(255, 255, 255, 0.8)',
                                font: { size: 12, weight: '500' }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {
                                label: function (context) {
                                    return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.5)',
                                callback: function (value) {
                                    return formatCurrency(value);
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.5)'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error loading trend chart:', error));
}

/**
 * Load category chart (pie or bar)
 */
function loadCategoryChart(chartType = 'pie') {
    const params = new URLSearchParams();
    params.append('period', currentPeriod);
    
    if (currentStartDate) params.append('start_date', currentStartDate);
    if (currentEndDate) params.append('end_date', currentEndDate);
    
    fetch(`/reports/api/expenses-by-category/?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('Expenses by Category:', data);
            
            if (!data.success || !data.data) return;
            
            const labels = data.data.map(item => item.name);
            const amounts = data.data.map(item => item.amount);
            
            const colors = Object.values(REPORT_COLORS);
            const backgroundColors = labels.map((_, i) => colors[i % colors.length]);
            
            const canvas = document.getElementById('categoryChart');
            if (!canvas) return;
            
            if (categoryChartInstance) {
                categoryChartInstance.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            categoryChartInstance = new Chart(ctx, {
                type: chartType || 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: amounts,
                        backgroundColor: backgroundColors,
                        borderColor: '#fff',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: chartType !== 'bar',
                            labels: {
                                color: 'rgba(255, 255, 255, 0.8)',
                                font: { size: 12, weight: '500' }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = formatCurrency(context.parsed.y || context.parsed);
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed.y || context.parsed) / total * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    scales: chartType === 'bar' ? {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.5)',
                                callback: function (value) {
                                    return formatCurrency(value);
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.5)'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        }
                    } : {}
                }
            });
        })
        .catch(error => console.error('Error loading category chart:', error));
}

/**
 * Load top expenses
 */
function loadTopExpenses() {
    const params = new URLSearchParams();
    params.append('limit', 5);
    params.append('period', currentPeriod);
    
    if (currentStartDate) params.append('start_date', currentStartDate);
    if (currentEndDate) params.append('end_date', currentEndDate);
    
    fetch(`/reports/api/top-expenses/?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('Top Expenses:', data);
            
            if (!data.success || !data.data) return;
            
            const container = document.getElementById('topExpensesList');
            if (!container) return;
            
            container.innerHTML = '';
            
            data.data.forEach((expense, index) => {
                const item = document.createElement('div');
                item.className = 'top-expense-item';
                item.innerHTML = `
                    <div class="expense-rank">#${expense.rank}</div>
                    <div class="expense-icon">${expense.icon}</div>
                    <div class="expense-info">
                        <div class="expense-description">${expense.description}</div>
                        <div class="expense-category">${expense.category}</div>
                    </div>
                    <div class="expense-amount">${formatCurrency(expense.amount)}</div>
                    <div class="expense-date">${expense.date}</div>
                `;
                container.appendChild(item);
            });
        })
        .catch(error => console.error('Error loading top expenses:', error));
}

/**
 * Load monthly summary table
 */
function loadMonthlySummary() {
    const year = new Date().getFullYear();
    
    fetch(`/reports/api/monthly-summary/?year=${year}`)
        .then(response => response.json())
        .then(data => {
            console.log('Monthly Summary:', data);
            
            if (!data.success || !data.data) return;
            
            const tbody = document.getElementById('monthlySummaryBody');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            
            data.data.forEach(month => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${month.month}</td>
                    <td>${formatCurrency(month.income)}</td>
                    <td>${formatCurrency(month.expense)}</td>
                    <td>${formatCurrency(month.balance)}</td>
                    <td>${month.savings_rate}%</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading monthly summary:', error));
}

/**
 * Export report
 */
function exportReport() {
    const format = prompt('Selecione o formato de exportação:\n1. CSV\n2. JSON', '1');
    
    if (!format) return;
    
    const formatMap = { '1': 'csv', '2': 'json' };
    const exportFormat = formatMap[format];
    
    if (!exportFormat) {
        alert('Formato inválido');
        return;
    }
    
    const params = {
        format: exportFormat,
        period: currentPeriod
    };
    
    if (currentStartDate) params.start_date = currentStartDate;
    if (currentEndDate) params.end_date = currentEndDate;
    
    fetch('/reports/api/export/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        },
        body: JSON.stringify(params)
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Erro ao exportar');
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `relatorio_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Export error:', error);
        alert('Erro ao exportar relatório');
    });
}
