// MyLedger - Home JavaScript
// Funcionalidades da página inicial (Dashboard)

(function () {
    'use strict';

    // ===== DOM Elements =====
    const notificationsPanel = document.getElementById('notificationsPanel');
    let expenseChart = null;
    let trendChart = null;

    // ===== SHOW TOAST (placeholder) =====
    function showToast(message, type = 'success') {
        // Create toast element
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

        if (type === 'success') {
            toast.style.background = 'linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(5, 150, 105, 0.95))';
            toast.style.backdropFilter = 'blur(10px)';
            toast.style.border = '1px solid rgba(16, 185, 129, 0.3)';
            toast.style.color = '#fff';
        } else {
            toast.style.background = 'linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(220, 38, 38, 0.95))';
            toast.style.backdropFilter = 'blur(10px)';
            toast.style.border = '1px solid rgba(239, 68, 68, 0.3)';
            toast.style.color = '#fff';
        }

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ===== INITIALIZE CHARTS =====
    function initExpenseChart() {
        const ctx = document.getElementById('expenseChart').getContext('2d');

        expenseChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Alimentação', 'Transporte', 'Lazer', 'Moradia', 'Outros'],
                datasets: [{
                    data: [35, 25, 20, 12, 8],
                    backgroundColor: ['#8A4FFF', '#5E2C9A', '#c084fc', '#6366f1', '#ec4899'],
                    borderWidth: 0,
                    hoverOffset: 10
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
                            label: function (context) {
                                return `${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }

    function initTrendChart() {
        const ctx = document.getElementById('trendChart').getContext('2d');

        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                datasets: [
                    {
                        label: 'Receitas',
                        data: [5200, 5800, 6100, 7200, 7800, 8200],
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
                        data: [3100, 3400, 3600, 3900, 3700, 3750],
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
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#fff',
                            usePointStyle: true,
                            boxWidth: 10
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: R$ ${context.raw.toLocaleString('pt-BR')}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)',
                            callback: function (value) {
                                return 'R$ ' + value.toLocaleString('pt-BR');
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)'
                        }
                    }
                }
            }
        });
    }

    // ===== NAVIGATION FUNCTIONS =====
    window.goToProfile = function () {
        window.location.href = '/accounts/profile/';
    };

    window.goToTransactions = function () {
        window.location.href = '/transactions/';
    };

    window.goToAddTransaction = function () {
        window.location.href = '/transactions/add/';
    };

    window.goToReports = function () {
        window.location.href = '/reports/';
    };

    window.goToCategories = function () {
        window.location.href = '/categories/';
    };

    window.goToBudget = function () {
        window.location.href = '/budget/';
    };

    window.exportData = function () {
        showToast('Preparando exportação de dados...', 'success');

        setTimeout(() => {
            const data = {
                exportDate: new Date().toISOString(),
                message: 'Dados exportados com sucesso!'
            };
            const dataStr = JSON.stringify(data, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `myledger_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast('Dados exportados com sucesso!', 'success');
        }, 1000);
    };

    // ===== NOTIFICATIONS =====
    window.toggleNotifications = function () {
        if (notificationsPanel) {
            notificationsPanel.classList.toggle('open');
            if (notificationsPanel.style.display === 'none') {
                notificationsPanel.style.display = 'flex';
                setTimeout(() => {
                    notificationsPanel.classList.add('open');
                }, 10);
            } else {
                notificationsPanel.classList.remove('open');
                setTimeout(() => {
                    if (!notificationsPanel.classList.contains('open')) {
                        notificationsPanel.style.display = 'none';
                    }
                }, 300);
            }
        }
    };

    // Close notifications when clicking outside
    document.addEventListener('click', function (e) {
        if (notificationsPanel && notificationsPanel.classList.contains('open')) {
            const isClickInside = notificationsPanel.contains(e.target);
            const isNotificationBtn = e.target.closest('.notifications-btn');

            if (!isClickInside && !isNotificationBtn) {
                notificationsPanel.classList.remove('open');
                setTimeout(() => {
                    if (!notificationsPanel.classList.contains('open')) {
                        notificationsPanel.style.display = 'none';
                    }
                }, 300);
            }
        }
    });

    // ===== UPDATE DASHBOARD DATA =====
    function updateDashboardData() {
        // This would fetch real data from backend
        // For now, using mock data

        const balanceElement = document.getElementById('totalBalance');
        const incomeElement = document.getElementById('totalIncome');
        const expenseElement = document.getElementById('totalExpense');
        const savingsElement = document.getElementById('totalSavings');

        // Simulate data update
        // In production, fetch from API
    }

    // ===== ADD GRADIENT ANIMATION =====
    function addGradientAnimation() {
        const orbs = document.querySelectorAll('.gradient-orb');
        orbs.forEach((orb, index) => {
            orb.style.animationDelay = `${index * 3}s`;
        });
    }

    // ===== ANIMATION DELAYS =====
    function addAnimationDelays() {
        const elements = document.querySelectorAll('.stat-card, .chart-card, .transactions-section, .budget-section, .quick-actions');
        elements.forEach((element, index) => {
            element.style.animation = `fadeUp 0.5s ease-out ${0.05 + index * 0.03}s both`;
        });
    }

    // ===== CHART PERIOD CHANGE =====
    const expensePeriodSelect = document.getElementById('expensePeriod');
    if (expensePeriodSelect) {
        expensePeriodSelect.addEventListener('change', function () {
            // Update expense chart data based on period
            showToast('Atualizando gráfico de despesas...', 'success');
        });
    }

    const trendPeriodSelect = document.getElementById('trendPeriod');
    if (trendPeriodSelect) {
        trendPeriodSelect.addEventListener('change', function () {
            // Update trend chart data based on period
            showToast('Atualizando gráfico de evolução...', 'success');
        });
    }

    // ===== LOAD USER DATA =====
    function loadUserData() {
        // Fetch user data from backend
        // Example:
        // fetch('/api/user/profile/')
        //     .then(response => response.json())
        //     .then(data => {
        //         document.getElementById('userName').textContent = data.name;
        //     });
    }

    // ===== ADD TO STYLESHEET FOR TOAST ANIMATION =====
    const styleSheet = document.createElement('style');
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

    // ===== INITIALIZE =====
    document.addEventListener('DOMContentLoaded', function () {
        addGradientAnimation();
        addAnimationDelays();
        initExpenseChart();
        initTrendChart();
        loadUserData();
        updateDashboardData();

        console.log('MyLedger - Dashboard inicializado');
    });
})();