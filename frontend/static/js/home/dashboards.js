// frontend/static/js/home/dashboards.js
// Dashboard logic for home page

// Global chart instances
let cardChartHome = null;
let categoryChartHome = null;
let cashFlowChartHome = null;

// Initialize dashboards when page loads
document.addEventListener('DOMContentLoaded', function () {
    initializeDashboards();
    setupEventListeners();
});

// Initialize all dashboards with default dates
function initializeDashboards() {
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));

    // Set date inputs with 30-day range
    document.getElementById('card-start-date').value = formatDateForInput(thirtyDaysAgo);
    document.getElementById('card-end-date').value = formatDateForInput(today);

    document.getElementById('category-start-date').value = formatDateForInput(thirtyDaysAgo);
    document.getElementById('category-end-date').value = formatDateForInput(today);

    // Set cash flow year to current year
    document.getElementById('cash-flow-year-home').value = today.getFullYear();

    // Load all dashboards
    loadCardExpensesHome();
    loadCategoryExpensesHome();
    loadCashFlowHome();
}

// Setup event listeners for interactive elements
function setupEventListeners() {
    const categoryPendingToggle = document.getElementById('category-include-pending-home');
    if (categoryPendingToggle) {
        categoryPendingToggle.addEventListener('change', loadCategoryExpensesHome);
    }
}

// Load card expenses data and render chart
async function loadCardExpensesHome() {
    const startDate = document.getElementById('card-start-date').value;
    const endDate = document.getElementById('card-end-date').value;

    if (!startDate || !endDate) {
        showError('card-error-home', 'Por favor, selecione as datas');
        return;
    }

    try {
        showLoading('card-loading-home', true);
        clearError('card-error-home');

        const data = await fetchAPI('/api/dashboard/card-expenses/', {
            start_date: startDate,
            end_date: endDate
        });

        renderCardExpensesChart(data);
        displayCardTotal(data.total);

    } catch (error) {
        showError('card-error-home', error.message);
    } finally {
        showLoading('card-loading-home', false);
    }
}

// Load category expenses data and render chart
async function loadCategoryExpensesHome() {
    const startDate = document.getElementById('category-start-date').value;
    const endDate = document.getElementById('category-end-date').value;
    const includePending = document.getElementById('category-include-pending-home').checked;

    if (!startDate || !endDate) {
        showError('category-error-home', 'Por favor, selecione as datas');
        return;
    }

    try {
        showLoading('category-loading-home', true);
        clearError('category-error-home');

        const data = await fetchAPI('/api/dashboard/category-expenses/', {
            start_date: startDate,
            end_date: endDate,
            include_pending: includePending
        });

        renderCategoryExpensesChart(data);
        displayCategoryTotal(data.total);

    } catch (error) {
        showError('category-error-home', error.message);
    } finally {
        showLoading('category-loading-home', false);
    }
}

// Load cash flow data and render chart
async function loadCashFlowHome() {
    const year = document.getElementById('cash-flow-year-home').value;

    if (!year) {
        showError('cash-flow-error-home', 'Por favor, selecione um ano');
        return;
    }

    try {
        showLoading('cash-flow-loading-home', true);
        clearError('cash-flow-error-home');

        const data = await fetchAPI('/api/dashboard/cash-flow/', {
            year: year
        });

        renderCashFlowChart(data);

    } catch (error) {
        showError('cash-flow-error-home', error.message);
    } finally {
        showLoading('cash-flow-loading-home', false);
    }
}

// Render card expenses bar chart
function renderCardExpensesChart(data) {
    const ctx = document.getElementById('cardChartHome').getContext('2d');

    // Destroy existing chart if it exists
    if (cardChartHome) {
        cardChartHome.destroy();
    }

    const chartData = {
        labels: data.data.map(item => item.card_name),
        datasets: [{
            label: 'Gastos (R$)',
            data: data.data.map(item => item.total),
            backgroundColor: generateColors(data.data.length),
            borderColor: generateBorderColors(data.data.length),
            borderWidth: 1
        }]
    };

    cardChartHome = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: false
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
}

// Render category expenses pie chart
function renderCategoryExpensesChart(data) {
    const ctx = document.getElementById('categoryChartHome').getContext('2d');

    // Destroy existing chart if it exists
    if (categoryChartHome) {
        categoryChartHome.destroy();
    }

    const chartData = {
        labels: data.data.map(item => {
            const percentage = ((item.total / data.total) * 100).toFixed(1);
            return `${item.category_name} (${percentage}%)`;
        }),
        datasets: [{
            data: data.data.map(item => item.total),
            backgroundColor: generateColors(data.data.length),
            borderColor: '#fff',
            borderWidth: 2
        }]
    };

    categoryChartHome = new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return formatCurrency(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

// Render cash flow line chart
function renderCashFlowChart(data) {
    const ctx = document.getElementById('cashFlowChartHome').getContext('2d');

    // Destroy existing chart if it exists
    if (cashFlowChartHome) {
        cashFlowChartHome.destroy();
    }

    const chartData = {
        labels: data.data.map(item => item.month),
        datasets: [
            {
                label: 'Receitas (R$)',
                data: data.data.map(item => item.income),
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Despesas (R$)',
                data: data.data.map(item => item.expense),
                borderColor: '#f44336',
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }
        ]
    };

    cashFlowChartHome = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
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
}

// Display total for card expenses
function displayCardTotal(total) {
    const totalElement = document.getElementById('card-total-home');
    const totalValue = document.getElementById('card-total-value-home');

    if (total > 0) {
        totalValue.textContent = formatCurrency(total);
        totalElement.style.display = 'block';
    } else {
        totalElement.style.display = 'none';
    }
}

// Display total for category expenses
function displayCategoryTotal(total) {
    const totalElement = document.getElementById('category-total-home');
    const totalValue = document.getElementById('category-total-value-home');

    if (total > 0) {
        totalValue.textContent = formatCurrency(total);
        totalElement.style.display = 'block';
    } else {
        totalElement.style.display = 'none';
    }
}

// Utility: Fetch API data with error handling
async function fetchAPI(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${endpoint}${queryString ? '?' + queryString : ''}`;

    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    });

    if (!response.ok) {
        let errorMessage = 'Erro ao carregar dados';
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.error || errorMessage;
        } catch (e) {
            // Use default error message
        }
        throw new Error(errorMessage);
    }

    return await response.json();
}

// Utility: Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Utility: Format date for input field
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Utility: Generate chart colors
function generateColors(count) {
    const colors = [
        'rgba(76, 175, 80, 0.7)',    // Green
        'rgba(33, 150, 243, 0.7)',   // Blue
        'rgba(255, 152, 0, 0.7)',    // Orange
        'rgba(156, 39, 176, 0.7)',   // Purple
        'rgba(244, 67, 54, 0.7)',    // Red
        'rgba(0, 188, 212, 0.7)',    // Cyan
        'rgba(255, 193, 7, 0.7)',    // Yellow
        'rgba(63, 81, 181, 0.7)',    // Indigo
        'rgba(233, 30, 99, 0.7)',    // Pink
        'rgba(76, 175, 80, 0.5)'     // Light Green
    ];

    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

// Utility: Generate border colors
function generateBorderColors(count) {
    const colors = [
        'rgba(76, 175, 80, 1)',      // Green
        'rgba(33, 150, 243, 1)',     // Blue
        'rgba(255, 152, 0, 1)',      // Orange
        'rgba(156, 39, 176, 1)',     // Purple
        'rgba(244, 67, 54, 1)',      // Red
        'rgba(0, 188, 212, 1)',      // Cyan
        'rgba(255, 193, 7, 1)',      // Yellow
        'rgba(63, 81, 181, 1)',      // Indigo
        'rgba(233, 30, 99, 1)',      // Pink
        'rgba(76, 175, 80, 1)'       // Light Green
    ];

    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

// Utility: Show loading indicator
function showLoading(elementId, show) {
    const element = document.getElementById(elementId);
    if (element) {
        if (show) {
            element.classList.add('active');
        } else {
            element.classList.remove('active');
        }
    }
}

// Utility: Show error message
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.classList.add('active');
    }
}

// Utility: Clear error message
function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
        element.classList.remove('active');
    }
}

