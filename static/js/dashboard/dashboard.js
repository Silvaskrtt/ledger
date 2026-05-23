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

    // Inicializa selects customizados
    initCustomSelects();

    // Setup event listeners (agora usando os eventos do Choices.js)
    setupChartEventListeners();
});

/**
 * Inicializa todos os selects com Choices.js
 */
function initCustomSelects() {
    const selects = document.querySelectorAll('.chart-period');

    selects.forEach(select => {
        // Destroi instância anterior se existir
        if (select.choicesInstance) {
            select.choicesInstance.destroy();
        }

        // Cria nova instância do Choices
        const choices = new Choices(select, {
            searchEnabled: false,        // Desativa busca (mais leve)
            itemSelectText: '',           // Remove texto padrão
            shouldSort: false,             // Mantém ordem original
            position: 'bottom',           // Posição do dropdown
            classNames: {
                containerOuter: 'choices custom-select',
            }
        });

        // Armazena a instância no elemento para uso posterior
        select.choicesInstance = choices;
    });
}

/**
 * Configura event listeners para os selects customizados
 */
function setupChartEventListeners() {
    const expenseSelect = document.getElementById('expensePeriod');
    const trendSelect = document.getElementById('trendPeriod');

    if (expenseSelect && expenseSelect.choicesInstance) {
        expenseSelect.choicesInstance.passedElement.element.addEventListener('choice', function (e) {
            const value = e.detail.choice.value;
            updateExpenseChart(value);
        });
    }

    if (trendSelect && trendSelect.choicesInstance) {
        trendSelect.choicesInstance.passedElement.element.addEventListener('choice', function (e) {
            const value = e.detail.choice.value;
            updateTrendChart(value);
        });
    }
}

/**
 * Carrega dados resumidos do dashboard (cards)
 */
function loadDashboardSummary() {
    fetch('/dashboard/api/summary/')
        .then(response => response.json())
        .then(data => {
            console.log('Dashboard Summary:', data);

            const formatCurrency = (value) => {
                return new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                }).format(value);
            };

            const balanceEl = document.getElementById('totalBalanceValue');
            if (balanceEl) balanceEl.textContent = formatCurrency(data.total_balance);

            const incomeEl = document.getElementById('totalIncomeValue');
            if (incomeEl) incomeEl.textContent = formatCurrency(data.total_income);

            const expenseEl = document.getElementById('totalExpenseValue');
            if (expenseEl) expenseEl.textContent = formatCurrency(data.total_expenses);

            const savingsEl = document.getElementById('totalSavingsValue');
            if (savingsEl) savingsEl.textContent = formatCurrency(data.savings);

            updateChangeIndicator('balanceChange', 'balanceChangeValue', data.balance_change);
            updateChangeIndicator('incomeChange', 'incomeChangeValue', data.income_change);
            updateChangeIndicator('expenseChange', 'expenseChangeValue', data.expenses_change);
        })
        .catch(error => console.error('Erro ao carregar summary:', error));
}

/**
 * Atualiza o indicador de mudança (positivo/negativo)
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

    container.classList.remove('positive', 'negative');

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

            let categories = [];
            let amounts = [];

            if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                categories = data.data.map(item => item.name);
                amounts = data.data.map(item => item.amount);
            } else {
                console.warn('Nenhum dado de categoria encontrado, usando dados de exemplo');
                categories = ['Alimentação', 'Transporte', 'Lazer', 'Moradia', 'Saúde'];
                amounts = [350, 150, 200, 1200, 100];
            }

            const colors = Object.values(CHART_COLORS);
            const backgroundColors = categories.map((_, i) => colors[i % colors.length]);

            if (expenseChartInstance) {
                expenseChartInstance.destroy();
            }

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
                                    const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });

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

            let labels = [];
            let incomeData = [];
            let expenseData = [];

            if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                labels = data.data.map(item => item.month);
                incomeData = data.data.map(item => item.income);
                expenseData = data.data.map(item => item.expenses);
            } else {
                labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'];
                incomeData = [5000, 5200, 4800, 6000, 5800, 6200];
                expenseData = [3000, 3200, 3500, 3100, 3300, 3400];
            }

            if (trendChartInstance) {
                trendChartInstance.destroy();
            }

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

    if (total === 0) {
        legend.innerHTML = '<div class="legend-empty">Nenhuma despesa registrada</div>';
        return;
    }

    let legendHTML = '';
    categories.forEach((category, index) => {
        const percentage = total > 0 ? ((amounts[index] / total) * 100).toFixed(1) : 0;
        if (amounts[index] > 0) {
            legendHTML += `
                <div class="legend-item">
                    <span class="legend-color" style="background: ${colors[index]};"></span>
                    <span class="legend-name">${category}</span>
                    <span class="legend-percentage">${percentage}%</span>
                </div>
            `;
        }
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

            if (!data.data || data.data.length === 0) {
                container.innerHTML = '<p class="text-center text-gray-500">Nenhuma transação encontrada</p>';
                return;
            }

            let html = '';
            data.data.forEach(transaction => {
                const isIncome = transaction.type === 'income';
                const amountClass = isIncome ? 'income' : 'expense';
                const amountSign = isIncome ? '+' : '-';
                const amountFormatted = formatCurrency(transaction.amount);

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

            if (!data.data || data.data.length === 0) {
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
 * Função para mostrar toast (notificação)
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `custom-toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    toast.style.position = 'fixed';
    toast.style.bottom = '30px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.zIndex = '1100';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '12px';
    toast.style.fontSize = '14px';
    toast.style.fontWeight = '500';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '12px';
    toast.style.animation = 'toastSlideUp 0.3s ease-out';
    toast.style.background = type === 'success'
        ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(5, 150, 105, 0.95))'
        : 'linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(220, 38, 38, 0.95))';
    toast.style.backdropFilter = 'blur(10px)';
    toast.style.border = `1px solid ${type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`;
    toast.style.color = '#fff';

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * EXPORT DATA - Redireciona para página de import/export
 */
function exportData() {
    showToast('Redirecionando para página de exportação...', 'success');
    setTimeout(() => {
        window.location.href = '/import-export/';
    }, 500);
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
        if (panel.style.display === 'none' || panel.style.display === '') {
            panel.style.display = 'block';
        } else {
            panel.style.display = 'none';
        }
    }
}

// Adicionar animação do toast ao stylesheet se não existir
if (!document.querySelector('#toast-animation-style')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'toast-animation-style';
    styleSheet.textContent = `
        @keyframes toastSlideUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
    `;
    document.head.appendChild(styleSheet);
}