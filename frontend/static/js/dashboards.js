// frontend/static/js/dashboards.js

const API_BASE_URL = '/api';
let cardChart = null;
let categoryChart = null;
let cashFlowChart = null;

// ===================================
// Funções utilitárias
// ===================================

/**
 * Formata número como moeda brasileira
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Obtém token CSRF do documento
 */
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Faz requisição à API
 */
async function fetchAPI(endpoint, params = {}) {
    try {
        const url = new URL(`${API_BASE_URL}${endpoint}`, window.location.origin);
        
        // Adicionar parâmetros à query string
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });

        const response = await fetch(url.toString(), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Erro na requisição:', error);
        throw error;
    }
}

/**
 * Exibe mensagem de erro
 */
function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    errorEl.textContent = `❌ ${message}`;
    errorEl.style.display = 'block';
}

/**
 * Limpa mensagem de erro
 */
function clearError(elementId) {
    const errorEl = document.getElementById(elementId);
    errorEl.style.display = 'none';
}

/**
 * Destrói gráfico anterior se existir
 */
function destroyChart(chartInstance) {
    if (chartInstance) {
        chartInstance.destroy();
    }
}

// ===================================
// Dashboard: Gastos por Cartão
// ===================================

async function loadCardExpenses() {
    const startDate = document.getElementById('card-start-date').value;
    const endDate = document.getElementById('card-end-date').value;
    
    const loadingEl = document.getElementById('card-loading');
    const totalEl = document.getElementById('card-total');
    
    try {
        loadingEl.style.display = 'flex';
        clearError('card-error');

        const data = await fetchAPI('/dashboard/card-expenses/', {
            start_date: startDate,
            end_date: endDate
        });

        // Destruir gráfico anterior
        destroyChart(cardChart);

        // Preparar dados
        const labels = data.data.map(item => item.card_name);
        const values = data.data.map(item => parseFloat(item.total_spent));
        const colors = generateColors(data.data.length);

        // Criar gráfico
        const ctx = document.getElementById('cardChart').getContext('2d');
        cardChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Gastos (R$)',
                    data: values,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1,
                    borderRadius: 4
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
                        callbacks: {
                            label: function(context) {
                                return formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });

        // Exibir total
        const total = parseFloat(data.total);
        document.getElementById('card-total-value').textContent = formatCurrency(total);
        totalEl.style.display = 'flex';

        loadingEl.style.display = 'none';
    } catch (error) {
        showError('card-error', 'Erro ao carregar dados. Tente novamente.');
        loadingEl.style.display = 'none';
        console.error('Erro:', error);
    }
}

// ===================================
// Dashboard: Gastos por Categoria
// ===================================

async function loadCategoryExpenses() {
    const startDate = document.getElementById('category-start-date').value;
    const endDate = document.getElementById('category-end-date').value;
    const includePending = document.getElementById('category-include-pending').checked;
    
    const loadingEl = document.getElementById('category-loading');
    const totalEl = document.getElementById('category-total');
    
    try {
        loadingEl.style.display = 'flex';
        clearError('category-error');

        const data = await fetchAPI('/dashboard/category-expenses/', {
            start_date: startDate,
            end_date: endDate,
            include_pending: includePending ? 'true' : 'false'
        });

        // Se não há dados
        if (!data.data || data.data.length === 0) {
            destroyChart(categoryChart);
            const ctx = document.getElementById('categoryChart').getContext('2d');
            categoryChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Sem dados'],
                    datasets: [{
                        data: [1],
                        backgroundColor: ['#e5e7eb']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
            loadingEl.style.display = 'none';
            totalEl.style.display = 'none';
            return;
        }

        // Destruir gráfico anterior
        destroyChart(categoryChart);

        // Preparar dados
        const labels = data.data.map(item => `${item.category_name} (${item.percentage}%)`);
        const values = data.data.map(item => parseFloat(item.total_spent));
        const colors = data.data.map(item => item.category_color);

        // Criar gráfico
        const ctx = document.getElementById('categoryChart').getContext('2d');
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: '#ffffff',
                    borderWidth: 2
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
                                return formatCurrency(context.parsed);
                            }
                        }
                    }
                }
            }
        });

        // Exibir total
        const total = parseFloat(data.total);
        document.getElementById('category-total-value').textContent = formatCurrency(total);
        totalEl.style.display = 'flex';

        loadingEl.style.display = 'none';
    } catch (error) {
        showError('category-error', 'Erro ao carregar dados. Tente novamente.');
        loadingEl.style.display = 'none';
        console.error('Erro:', error);
    }
}

// ===================================
// Dashboard: Fluxo de Caixa
// ===================================

async function loadCashFlow() {
    const year = document.getElementById('cash-flow-year').value;
    const loadingEl = document.getElementById('cash-flow-loading');
    
    try {
        loadingEl.style.display = 'flex';
        clearError('cash-flow-error');

        const data = await fetchAPI('/dashboard/cash-flow/', {
            year: year
        });

        // Destruir gráfico anterior
        destroyChart(cashFlowChart);

        // Preparar dados
        const labels = data.data.map(item => item.month);
        const incomeData = data.data.map(item => parseFloat(item.income));
        const expenseData = data.data.map(item => parseFloat(item.expense));
        const balanceData = data.data.map(item => parseFloat(item.balance));

        // Criar gráfico
        const ctx = document.getElementById('cashFlowChart').getContext('2d');
        cashFlowChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Receitas',
                        data: incomeData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2
                    },
                    {
                        label: 'Despesas',
                        data: expenseData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2
                    },
                    {
                        label: 'Saldo',
                        data: balanceData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: false,
                        tension: 0.4,
                        borderWidth: 2,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });

        loadingEl.style.display = 'none';
    } catch (error) {
        showError('cash-flow-error', 'Erro ao carregar dados. Tente novamente.');
        loadingEl.style.display = 'none';
        console.error('Erro:', error);
    }
}

// ===================================
// Funções auxiliares
// ===================================

/**
 * Gera cores aleatórias para os gráficos
 */
function generateColors(count) {
    const colors = [
        '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
        '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#0ea5e9'
    ];
    
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

/**
 * Adiciona listener para mudanças no toggle de pendentes
 */
document.addEventListener('DOMContentLoaded', function() {
    const pendingToggle = document.getElementById('category-include-pending');
    if (pendingToggle) {
        pendingToggle.addEventListener('change', loadCategoryExpenses);
    }
});
