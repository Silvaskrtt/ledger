/**
 * Dashboard Module - Carrega e renderiza dados reais do dashboard
 * Endpoints API:
 * - /dashboard/api/summary/
 * - /dashboard/api/monthly-trend/
 * - /dashboard/api/expenses-by-category/
 * - /dashboard/api/recent-transactions/
 */

// Color palette for charts
const CHART_COLORS = {
    primary: '#8A4FFF',
    secondary: '#5E2C9A',
    accent: '#c084fc',
    info: '#6366f1',
    danger: '#ec4899',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
};

// Chart instances (globais para update)
let expenseChartInstance = null;
let trendChartInstance = null;

/**
 * Inicializa o dashboard ao carregar a página
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log('Dashboard inicializando...');

    // Carrega dados resumidos
    loadDashboardSummary();

    // Carrega gráficos
    updateExpenseChart('month');
    updateTrendChart('12');

    // Carrega transações recentes
    loadRecentTransactions();

    // Carrega orçamento por categoria
    loadBudgetByCategory();

    // Setup event listeners
    const expensePeriod = document.getElementById('expensePeriod');
    if (expensePeriod) {
        expensePeriod.addEventListener('change', function () {
            updateExpenseChart(this.value);
        });
    }

    const trendPeriod = document.getElementById('trendPeriod');
    if (trendPeriod) {
        trendPeriod.addEventListener('change', function () {
            updateTrendChart(this.value);
        });
    }
});

/**
 * Carrega dados resumidos do dashboard (cards)
 */
function loadDashboardSummary() {
    fetch('/dashboard/api/summary/')
        .then(response => response.json())
        .then(data => {
            console.log('Dashboard Summary:', data);

            // Formata valores em moeda brasileira
            const formatCurrency = (value) => {
                return new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                }).format(value);
            };

            // Usar totais gerais nos cards principais
            // Saldo Total (já estava correto)
            const balanceEl = document.getElementById('totalBalanceValue');
            if (balanceEl) balanceEl.textContent = formatCurrency(data.total_balance);

            // Total de Receitas (todos os tempos)
            const incomeEl = document.getElementById('totalIncomeValue');
            if (incomeEl) incomeEl.textContent = formatCurrency(data.total_income);  // Mudado de current_month_income

            // Total de Despesas (todos os tempos)
            const expenseEl = document.getElementById('totalExpenseValue');
            if (expenseEl) expenseEl.textContent = formatCurrency(data.total_expenses);  // Mudado de current_month_expenses

            // Economia do mês atual (saldo do mês)
            const savingsEl = document.getElementById('totalSavingsValue');
            if (savingsEl) savingsEl.textContent = formatCurrency(data.savings);  // Já é a economia do mês

            // Atualiza percentuais de mudança
            updateChangeIndicator('balanceChange', 'balanceChangeValue', data.balance_change);
            updateChangeIndicator('incomeChange', 'incomeChangeValue', data.income_change);
            updateChangeIndicator('expenseChange', 'expenseChangeValue', data.expenses_change);
        })
        .catch(error => console.error('Erro ao carregar summary:', error));
}

/**
 * Atualiza o indicador de mudança (positivo/negativo) - CORRIGIDA
 */
function updateChangeIndicator(containerId, valueId, percentage) {
    const container = document.getElementById(containerId);
    const valueElement = document.getElementById(valueId);

    if (!container) {
        console.warn(`Container não encontrado: ${containerId}`);
        return;
    }

    if (!valueElement) {
        console.warn(`Value element não encontrado: ${valueId}`);
        return;
    }

    valueElement.textContent = Math.abs(percentage) + '%';

    // Remove classes anteriores
    container.classList.remove('positive', 'negative');

    // Adiciona nova classe e atualiza ícone
    if (percentage >= 0) {
        container.classList.add('positive');
        const icon = container.querySelector('i');
        if (icon) icon.className = 'fas fa-arrow-up';
    } else {
        container.classList.add('negative');
        const icon = container.querySelector('i');
        if (icon) icon.className = 'fas fa-arrow-down';
    }
}

/**
 * Atualiza gráfico de despesas por categoria
 */
function updateExpenseChart(period) {
    fetch(`/dashboard/api/expenses-by-category/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            console.log('Expenses by Category:', data);

            const categories = data.data.map(item => item.name);
            const amounts = data.data.map(item => item.amount);

            // Define cores (cicla entre as definidas)
            const colors = Object.values(CHART_COLORS);
            const backgroundColors = categories.map((_, i) => colors[i % colors.length]);

            // Destroy o gráfico anterior se existir
            if (expenseChartInstance) {
                expenseChartInstance.destroy();
            }

            // Cria novo gráfico
            const canvas = document.getElementById('expenseChart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            expenseChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: categories,
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
                            display: false,
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = formatCurrency(context.parsed);
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });

            // Atualiza legenda
            updateChartLegend(categories, amounts, backgroundColors);
        })
        .catch(error => console.error('Erro ao carregar expenses:', error));
}

/**
 * Atualiza gráfico de tendência mensal
 */
function updateTrendChart(months) {
    fetch(`/dashboard/api/monthly-trend/?months=${months}`)
        .then(response => response.json())
        .then(data => {
            console.log('Monthly Trend:', data);

            const labels = data.data.map(item => item.month);
            const incomeData = data.data.map(item => item.income);
            const expenseData = data.data.map(item => item.expenses);

            // Destroy o gráfico anterior se existir
            if (trendChartInstance) {
                trendChartInstance.destroy();
            }

            // Cria novo gráfico
            const canvas = document.getElementById('trendChart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Receitas',
                            data: incomeData,
                            borderColor: CHART_COLORS.success,
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: CHART_COLORS.success,
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                        },
                        {
                            label: 'Despesas',
                            data: expenseData,
                            borderColor: CHART_COLORS.error,
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: CHART_COLORS.error,
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
                            position: 'bottom',
                            labels: {
                                usePointStyle: true,
                                padding: 15,
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function (context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += formatCurrency(context.parsed.y);
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function (value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Erro ao carregar trend:', error));
}

/**
 * Atualiza legenda do gráfico de despesas
 */
function updateChartLegend(categories, amounts, colors) {
    const legend = document.getElementById('expenseLegend');
    if (!legend) return;

    const total = amounts.reduce((a, b) => a + b, 0);

    let legendHTML = '';
    categories.forEach((category, index) => {
        const percentage = total > 0 ? ((amounts[index] / total) * 100).toFixed(1) : 0;
        legendHTML += `
            <div class="legend-item">
                <span class="legend-color" style="background: ${colors[index]};"></span>
                ${category} - ${percentage}%
            </div>
        `;
    });

    legend.innerHTML = legendHTML;
}

/**
 * Carrega transações recentes
 */
function loadRecentTransactions() {
    fetch('/dashboard/api/recent-transactions/?limit=5')
        .then(response => response.json())
        .then(data => {
            console.log('Recent Transactions:', data);

            const container = document.getElementById('recentTransactionsList');
            if (!container) return;

            if (data.data.length === 0) {
                container.innerHTML = '<p class="text-center text-gray-500">Nenhuma transação encontrada</p>';
                return;
            }

            let html = '';
            data.data.forEach(transaction => {
                const isIncome = transaction.type === 'income';
                const amountClass = isIncome ? 'income' : 'expense';
                const amountSign = isIncome ? '+' : '-';
                const amountFormatted = formatCurrency(transaction.amount);

                // Define cores e ícones baseado no tipo
                let bgColor = isIncome ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
                let textColor = isIncome ? '#10b981' : '#ef4444';
                let iconClass = isIncome ? 'fas fa-arrow-down' : 'fas fa-shopping-cart';

                html += `
                    <div class="transaction-item">
                        <div class="transaction-icon" style="background: ${bgColor};">
                            <i class="${iconClass}" style="color: ${textColor};"></i>
                        </div>
                        <div class="transaction-info">
                            <div class="transaction-title">${escapeHtml(transaction.title)}</div>
                            <div class="transaction-meta">
                                <span>${escapeHtml(transaction.category)}</span>
                                <span class="separator">•</span>
                                <span>${transaction.date}</span>
                            </div>
                        </div>
                        <div class="transaction-amount ${amountClass}">${amountSign} ${amountFormatted}</div>
                    </div>
                `;
            });

            container.innerHTML = html;
        })
        .catch(error => console.error('Erro ao carregar transações:', error));
}

/**
 * Carrega orçamento por categoria
 */
function loadBudgetByCategory() {
    fetch('/dashboard/api/expenses-by-category/?period=month')
        .then(response => response.json())
        .then(data => {
            console.log('Budget by Category:', data);

            const container = document.getElementById('budgetList');
            if (!container) return;

            if (data.data.length === 0) {
                container.innerHTML = '<p class="text-center text-gray-500">Nenhuma categoria com despesas este mês</p>';
                return;
            }

            const colors = Object.values(CHART_COLORS);

            let html = '';
            data.data.forEach((category, index) => {
                const color = colors[index % colors.length];
                const percentage = category.percentage || 0;

                html += `
                    <div class="budget-item">
                        <div class="budget-info">
                            <div class="budget-category">
                                <span class="category-dot" style="background: ${color};"></span>
                                <span>${escapeHtml(category.name)}</span>
                            </div>
                            <div class="budget-stats">
                                <span class="budget-spent">${formatCurrency(category.amount)}</span>
                            </div>
                        </div>
                        <div class="budget-bar">
                            <div class="budget-progress" style="width: ${percentage}%; background: ${color};"></div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        })
        .catch(error => console.error('Erro ao carregar budget:', error));
}

/**
 * Função auxiliar para escapar HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Formata valor em moeda brasileira
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Funções de navegação
 */
function goToTransactions() {
    window.location.href = '/transactions/';
}

function goToCategories() {
    window.location.href = '/categories/';
}

function goToProfile() {
    window.location.href = '/accounts/profile/';
}

function goToBudget() {
    window.location.href = '/transactions/';
}

function toggleNotifications() {
    const panel = document.getElementById('notificationsPanel');
    if (panel) {
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
        } else {
            panel.style.display = 'none';
        }
    }
}

function exportData() {
    alert('Funcionalidade de exportação em desenvolvimento!');
}