// MyLedger - Reports JavaScript (CONECTADO AO BACKEND)

(function () {
    'use strict';

    // ===== DOM Elements =====
    const periodBtns = document.querySelectorAll('.period-btn');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const applyCustomBtn = document.getElementById('applyCustomBtn');
    const exportReportBtn = document.getElementById('exportReportBtn');
    const totalIncomeSpan = document.getElementById('totalIncome');
    const totalExpenseSpan = document.getElementById('totalExpense');
    const totalBalanceSpan = document.getElementById('totalBalance');
    const savingsRateSpan = document.getElementById('savingsRate');
    const incomeTrendSpan = document.getElementById('incomeTrend');
    const expenseTrendSpan = document.getElementById('expenseTrend');
    const topExpensesList = document.getElementById('topExpensesList');
    const monthlySummaryBody = document.getElementById('monthlySummaryBody');

    // ===== State =====
    let currentPeriod = 'month';
    let startDate = null;
    let endDate = null;
    let trendChart = null;
    let categoryChart = null;

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function getMonthName(monthNum) {
        const months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        return months[monthNum - 1];
    }

    function getCookie(name) {
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

    function showToast(message, type = 'success') {
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `custom-toast ${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ===== API Calls =====
    async function loadSummary() {
        try {
            const params = new URLSearchParams();
            params.append('period', currentPeriod);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);

            const response = await fetch(`/reports/api/summary/?${params.toString()}`);
            const data = await response.json();

            if (data.success) {
                const summary = data.data;
                if (totalIncomeSpan) totalIncomeSpan.textContent = formatCurrency(summary.total_income);
                if (totalExpenseSpan) totalExpenseSpan.textContent = formatCurrency(summary.total_expense);
                if (totalBalanceSpan) {
                    totalBalanceSpan.textContent = formatCurrency(summary.balance);
                    totalBalanceSpan.style.color = summary.balance >= 0 ? '#10b981' : '#ef4444';
                }
                if (savingsRateSpan) savingsRateSpan.textContent = `${summary.savings_rate}%`;
                if (incomeTrendSpan) {
                    const incomeChange = summary.income_change;
                    incomeTrendSpan.textContent = `${incomeChange >= 0 ? '+' : ''}${incomeChange}%`;
                    incomeTrendSpan.className = `summary-trend ${incomeChange >= 0 ? 'positive' : 'negative'}`;
                }
                if (expenseTrendSpan) {
                    const expenseChange = summary.expense_change;
                    expenseTrendSpan.textContent = `${expenseChange >= 0 ? '+' : ''}${expenseChange}%`;
                    expenseTrendSpan.className = `summary-trend ${expenseChange >= 0 ? 'negative' : 'positive'}`;
                }
            }
        } catch (error) {
            console.error('Erro ao carregar summary:', error);
        }
    }

    async function loadMonthlyTrend() {
        try {
            const response = await fetch('/reports/api/monthly-trend/?months=12');
            const data = await response.json();

            if (data.success && data.data.length > 0) {
                const labels = data.data.map(item => item.month);
                const incomeData = data.data.map(item => item.income);
                const expenseData = data.data.map(item => item.expense);

                initTrendChart(labels, incomeData, expenseData);
            }
        } catch (error) {
            console.error('Erro ao carregar tendência:', error);
        }
    }

    async function loadCategoryChart() {
        try {
            const params = new URLSearchParams();
            params.append('period', currentPeriod);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);

            const response = await fetch(`/reports/api/expenses-by-category/?${params.toString()}`);
            const data = await response.json();

            if (data.success) {
                const chartType = document.getElementById('categoryChartType')?.value || 'pie';
                initCategoryChart(data.data, chartType);
            }
        } catch (error) {
            console.error('Erro ao carregar categorias:', error);
        }
    }

    async function loadTopExpenses() {
        try {
            const params = new URLSearchParams();
            params.append('limit', '5');
            params.append('period', currentPeriod);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);

            const response = await fetch(`/reports/api/top-expenses/?${params.toString()}`);
            const data = await response.json();

            if (topExpensesList) {
                if (data.success && data.data.length > 0) {
                    topExpensesList.innerHTML = data.data.map(expense => `
                        <div class="expense-item">
                            <div class="expense-rank rank-${expense.rank}">${expense.rank}</div>
                            <div class="expense-icon">${expense.icon}</div>
                            <div class="expense-info">
                                <div class="expense-title">${escapeHtml(expense.description)}</div>
                                <div class="expense-meta">
                                    <span>${escapeHtml(expense.category)}</span>
                                    <span>•</span>
                                    <span>${expense.date}</span>
                                </div>
                            </div>
                            <div class="expense-amount">- ${formatCurrency(expense.amount)}</div>
                        </div>
                    `).join('');
                } else {
                    topExpensesList.innerHTML = '<div class="empty-state"><p>Nenhuma despesa encontrada</p></div>';
                }
            }
        } catch (error) {
            console.error('Erro ao carregar top despesas:', error);
        }
    }

    async function loadMonthlySummary() {
        try {
            const response = await fetch('/reports/api/monthly-summary/');
            const data = await response.json();

            if (monthlySummaryBody) {
                if (data.success && data.data.length > 0) {
                    monthlySummaryBody.innerHTML = data.data.map(item => `
                        <tr>
                            <td>${getMonthName(item.month_num)}</td>
                            <td class="amount-positive">${formatCurrency(item.income)}</td>
                            <td class="amount-negative">${formatCurrency(item.expense)}</td>
                            <td class="${item.balance >= 0 ? 'amount-positive' : 'amount-negative'}">${formatCurrency(item.balance)}</td>
                            <td>${item.savings_rate}%</td>
                        </tr>
                    `).join('');
                } else {
                    monthlySummaryBody.innerHTML = '<tr><td colspan="5" class="empty-state">Nenhum dado encontrado</td></tr>';
                }
            }
        } catch (error) {
            console.error('Erro ao carregar resumo mensal:', error);
        }
    }

    // ===== Chart Functions =====
    function initTrendChart(labels, incomeData, expenseData) {
        const ctx = document.getElementById('trendChart')?.getContext('2d');
        if (!ctx) return;

        if (trendChart) trendChart.destroy();

        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Receitas',
                        data: incomeData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#0A0A0A',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Despesas',
                        data: expenseData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#0A0A0A',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)',
                            callback: function (value) {
                                return formatCurrency(value);
                            }
                        }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'rgba(255, 255, 255, 0.5)' }
                    }
                }
            }
        });
    }

    function initCategoryChart(data, type = 'pie') {
        const ctx = document.getElementById('categoryChart')?.getContext('2d');
        if (!ctx) return;

        if (categoryChart) categoryChart.destroy();

        const categories = data.map(item => item.name);
        const amounts = data.map(item => item.amount);
        const colors = data.map(item => item.color || '#8A4FFF');

        if (type === 'pie') {
            categoryChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: categories,
                    datasets: [{
                        data: amounts,
                        backgroundColor: colors,
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#fff', usePointStyle: true, boxWidth: 10 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.raw / total) * 100).toFixed(1);
                                    return `${context.label}: ${formatCurrency(context.raw)} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        } else {
            categoryChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: categories,
                    datasets: [{
                        data: amounts,
                        backgroundColor: colors,
                        borderRadius: 8,
                        barPercentage: 0.6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.5)',
                                callback: function (value) {
                                    return formatCurrency(value);
                                }
                            }
                        },
                        x: {
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.5)',
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        }
    }

    // ===== Update All Reports =====
    async function updateReports() {
        await loadSummary();
        await loadMonthlyTrend();
        await loadCategoryChart();
        await loadTopExpenses();
        await loadMonthlySummary();
    }

    // ===== Period Change Handler =====
    function setPeriod(period) {
        currentPeriod = period;
        startDate = null;
        endDate = null;

        if (startDateInput) startDateInput.value = '';
        if (endDateInput) endDateInput.value = '';

        updateReports();
    }

    // ===== Export Report =====
    async function exportReport() {
        try {
            showToast('Preparando relatório para download...', 'success');

            const response = await fetch('/reports/api/export/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    format: 'csv',
                    period: currentPeriod,
                    start_date: startDate,
                    end_date: endDate
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `relatorio_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                showToast('Relatório exportado com sucesso!', 'success');
            } else {
                showToast('Erro ao exportar relatório', 'error');
            }
        } catch (error) {
            console.error('Erro na exportação:', error);
            showToast('Erro ao exportar relatório', 'error');
        }
    }

    // ===== Event Listeners =====
    periodBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            periodBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setPeriod(btn.dataset.period);
        });
    });

    if (applyCustomBtn) {
        applyCustomBtn.addEventListener('click', () => {
            startDate = startDateInput?.value;
            endDate = endDateInput?.value;

            if (startDate && endDate && startDate > endDate) {
                showToast('Data inicial não pode ser maior que a data final', 'error');
                return;
            }

            periodBtns.forEach(b => b.classList.remove('active'));
            currentPeriod = 'custom';
            updateReports();
        });
    }

    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', exportReport);
    }

    const chartTypeSelect = document.getElementById('categoryChartType');
    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', () => {
            loadCategoryChart();
        });
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== Initialize =====
    function init() {
        // Definir datas padrão
        const today = new Date();
        const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

        if (startDateInput) startDateInput.value = firstDayOfMonth.toISOString().split('T')[0];
        if (endDateInput) endDateInput.value = today.toISOString().split('T')[0];

        updateReports();
    }

    init();
})();