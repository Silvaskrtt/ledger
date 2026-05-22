// MyLedger - Goals JavaScript
// Funcionalidades da tela de metas financeiras

(function () {
    'use strict';

    // ===== DOM Elements =====
    const goalsGrid = document.getElementById('goalsGrid');
    const activeGoalsCountSpan = document.getElementById('activeGoalsCount');
    const completedGoalsCountSpan = document.getElementById('completedGoalsCount');
    const totalProgressSpan = document.getElementById('totalProgress');
    const totalSavedSpan = document.getElementById('totalSaved');
    const goalModal = document.getElementById('goalModal');
    const deleteModal = document.getElementById('deleteModal');
    const goalForm = document.getElementById('goalForm');
    const modalTitle = document.getElementById('modalTitle');
    const submitBtnText = document.getElementById('submitBtnText');
    const goalIdInput = document.getElementById('goalId');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // ===== State =====
    let goals = [];
    let goalToDelete = null;
    let editingId = null;

    // ===== Sample Data =====
    const sampleGoals = [
        {
            id: 1,
            title: 'Viagem para Europa',
            target: 15000,
            current: 5200,
            deadline: '2025-12-31',
            description: 'Realizar uma viagem de 15 dias pela Europa',
            icon: '✈️',
            completed: false,
            createdAt: '2025-01-15'
        },
        {
            id: 2,
            title: 'Carro Novo',
            target: 50000,
            current: 12500,
            deadline: '2026-06-30',
            description: 'Comprar um carro seminovo',
            icon: '🚗',
            completed: false,
            createdAt: '2025-02-01'
        },
        {
            id: 3,
            title: 'Reserva de Emergência',
            target: 20000,
            current: 20000,
            deadline: '2025-05-15',
            description: 'Fundo de emergência para 6 meses',
            icon: '🏦',
            completed: true,
            createdAt: '2024-10-01'
        },
        {
            id: 4,
            title: 'MBA em Finanças',
            target: 25000,
            current: 8900,
            deadline: '2025-08-20',
            description: 'Especialização em finanças corporativas',
            icon: '🎓',
            completed: false,
            createdAt: '2025-03-10'
        }
    ];

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    }

    function calculateProgress(current, target) {
        return Math.min((current / target) * 100, 100).toFixed(1);
    }

    function getDaysRemaining(deadline) {
        const today = new Date();
        const deadlineDate = new Date(deadline);
        const diffTime = deadlineDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    }

    function getDeadlineClass(deadline) {
        const daysRemaining = getDaysRemaining(deadline);
        if (daysRemaining < 0) return 'overdue';
        if (daysRemaining < 30) return 'urgent';
        return '';
    }

    function getDeadlineText(deadline) {
        const daysRemaining = getDaysRemaining(deadline);
        if (daysRemaining < 0) {
            return 'Atrasado há ' + Math.abs(daysRemaining) + ' dias';
        }
        if (daysRemaining === 0) return 'Vence hoje';
        if (daysRemaining === 1) return 'Vence amanhã';
        return daysRemaining + ' dias restantes';
    }

    // ===== Load Goals =====
    function loadGoals() {
        const savedGoals = localStorage.getItem('myledger_goals');
        if (savedGoals) {
            goals = JSON.parse(savedGoals);
        } else {
            goals = [...sampleGoals];
            saveGoals();
        }
        renderGoals();
        updateSummary();
    }

    function saveGoals() {
        localStorage.setItem('myledger_goals', JSON.stringify(goals));
    }

    // ===== Render Goals =====
    function renderGoals() {
        if (!goalsGrid) return;

        if (goals.length === 0) {
            goalsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bullseye"></i>
                    <p>${window.translations?.noGoals || 'Nenhuma meta cadastrada'}</p>
                    <small>${window.translations?.addGoalHint || 'Clique em "Nova Meta" para começar'}</small>
                </div>
            `;
            return;
        }

        const activeGoals = goals.filter(g => !g.completed);
        const completedGoals = goals.filter(g => g.completed);

        goalsGrid.innerHTML = [...activeGoals, ...completedGoals].map(goal => `
            <div class="goal-card ${goal.completed ? 'completed' : ''}" data-id="${goal.id}">
                <div class="goal-header">
                    <div class="goal-icon">${goal.icon || '🎯'}</div>
                    <div class="goal-info">
                        <div class="goal-title">${escapeHtml(goal.title)}</div>
                        <div class="goal-deadline ${getDeadlineClass(goal.deadline)}">
                            <i class="fas fa-calendar-alt"></i>
                            <span>${getDeadlineText(goal.deadline)}</span>
                        </div>
                    </div>
                    <div class="goal-actions">
                        <button class="goal-action edit" onclick="editGoal(${goal.id})" title="Editar">
                            <i class="fas fa-pencil-alt"></i>
                        </button>
                        <button class="goal-action delete" onclick="confirmDeleteGoal(${goal.id})" title="Excluir">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                ${goal.description ? `<div class="goal-description">${escapeHtml(goal.description)}</div>` : ''}
                <div class="goal-progress">
                    <div class="progress-header">
                        <span class="progress-label">Progresso</span>
                        <span class="progress-value">${calculateProgress(goal.current, goal.target)}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${calculateProgress(goal.current, goal.target)}%; background: ${goal.completed ? '#10b981' : '#8A4FFF'}"></div>
                    </div>
                </div>
                <div class="goal-stats">
                    <div class="stat">
                        <div class="stat-label">Meta</div>
                        <div class="stat-value">${formatCurrency(goal.target)}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Economizado</div>
                        <div class="stat-value saved">${formatCurrency(goal.current)}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Falta</div>
                        <div class="stat-value remaining">${formatCurrency(goal.target - goal.current)}</div>
                    </div>
                </div>
                ${!goal.completed && goal.current >= goal.target ? `
                    <div class="goal-complete-banner">
                        <button class="btn-complete-goal" onclick="completeGoal(${goal.id})">
                            <i class="fas fa-check-circle"></i>
                            <span>Marcar como concluída</span>
                        </button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== Update Summary =====
    function updateSummary() {
        const activeGoals = goals.filter(g => !g.completed);
        const completedGoals = goals.filter(g => g.completed);

        if (activeGoalsCountSpan) activeGoalsCountSpan.textContent = activeGoals.length;
        if (completedGoalsCountSpan) completedGoalsCountSpan.textContent = completedGoals.length;

        let totalProgressSum = 0;
        let totalSaved = 0;

        goals.forEach(goal => {
            totalProgressSum += calculateProgress(goal.current, goal.target);
            totalSaved += goal.current;
        });

        const avgProgress = goals.length > 0 ? (totalProgressSum / goals.length).toFixed(1) : 0;
        if (totalProgressSpan) totalProgressSpan.textContent = `${avgProgress}%`;
        if (totalSavedSpan) totalSavedSpan.textContent = formatCurrency(totalSaved);
    }

    // ===== Open Modal =====
    window.openGoalModal = function (id = null) {
        editingId = id;

        if (id) {
            const goal = goals.find(g => g.id === id);
            if (goal) {
                modalTitle.textContent = 'Editar Meta';
                submitBtnText.textContent = 'Atualizar';
                goalIdInput.value = goal.id;
                document.getElementById('goal_title').value = goal.title;
                document.getElementById('goal_target').value = formatCurrency(goal.target);
                document.getElementById('goal_deadline').value = goal.deadline;
                document.getElementById('goal_current').value = formatCurrency(goal.current);
                document.getElementById('goal_description').value = goal.description || '';
                document.getElementById('goal_icon').value = goal.icon || '🎯';

                // Highlight selected icon
                document.querySelectorAll('.icon-option').forEach(btn => {
                    btn.classList.remove('active');
                    if (btn.dataset.icon === goal.icon) {
                        btn.classList.add('active');
                    }
                });
            }
        } else {
            modalTitle.textContent = 'Nova Meta';
            submitBtnText.textContent = 'Salvar';
            goalIdInput.value = '';
            document.getElementById('goalForm').reset();
            document.getElementById('goal_target').value = '';
            document.getElementById('goal_current').value = '';
            document.getElementById('goal_icon').value = '🎯';

            // Set default deadline to end of year
            const endOfYear = new Date();
            endOfYear.setMonth(11, 31);
            document.getElementById('goal_deadline').value = endOfYear.toISOString().split('T')[0];

            // Reset icon selection
            document.querySelectorAll('.icon-option').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.icon === '🎯') {
                    btn.classList.add('active');
                }
            });
        }

        if (goalModal) {
            goalModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeGoalModal = function () {
        if (goalModal) {
            goalModal.style.display = 'none';
            document.body.style.overflow = '';
            editingId = null;
        }
    };

    // ===== Save Goal =====
    function saveGoal(event) {
        event.preventDefault();

        const id = parseInt(goalIdInput.value);
        const title = document.getElementById('goal_title').value.trim();
        let target = document.getElementById('goal_target').value;
        let current = document.getElementById('goal_current').value;
        const deadline = document.getElementById('goal_deadline').value;
        const description = document.getElementById('goal_description').value;
        const icon = document.getElementById('goal_icon').value;

        // Parse currency values
        target = parseFloat(target.replace(/[^0-9,-]/g, '').replace(',', '.')) || 0;
        current = parseFloat(current.replace(/[^0-9,-]/g, '').replace(',', '.')) || 0;

        if (!title) {
            showToast('Por favor, insira um título para a meta', 'error');
            return;
        }

        if (target <= 0) {
            showToast('Por favor, insira um valor alvo válido', 'error');
            return;
        }

        if (!deadline) {
            showToast('Por favor, selecione uma data limite', 'error');
            return;
        }

        if (id) {
            // Update existing goal
            const index = goals.findIndex(g => g.id === id);
            if (index !== -1) {
                const completed = current >= goals[index].target ? goals[index].completed : false;
                goals[index] = {
                    ...goals[index],
                    title: title,
                    target: target,
                    current: current,
                    deadline: deadline,
                    description: description,
                    icon: icon,
                    completed: completed
                };
                showToast('Meta atualizada com sucesso!', 'success');
            }
        } else {
            // Create new goal
            const newGoal = {
                id: Date.now(),
                title: title,
                target: target,
                current: current,
                deadline: deadline,
                description: description,
                icon: icon,
                completed: false,
                createdAt: new Date().toISOString().split('T')[0]
            };
            goals.push(newGoal);
            showToast('Meta criada com sucesso!', 'success');
        }

        saveGoals();
        renderGoals();
        updateSummary();
        closeGoalModal();
    }

    // ===== Edit Goal =====
    window.editGoal = function (id) {
        openGoalModal(id);
    };

    // ===== Complete Goal =====
    window.completeGoal = function (id) {
        const goal = goals.find(g => g.id === id);
        if (goal) {
            goal.completed = true;
            saveGoals();
            renderGoals();
            updateSummary();
            showToast('Parabéns! Meta concluída com sucesso!', 'success');
        }
    };

    // ===== Delete Goal =====
    window.confirmDeleteGoal = function (id) {
        goalToDelete = id;
        if (deleteModal) {
            deleteModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    };

    function closeDeleteModal() {
        if (deleteModal) {
            deleteModal.style.display = 'none';
            document.body.style.overflow = '';
            goalToDelete = null;
        }
    }

    function deleteGoal() {
        if (goalToDelete !== null) {
            goals = goals.filter(g => g.id !== goalToDelete);
            saveGoals();
            renderGoals();
            updateSummary();
            showToast('Meta excluída com sucesso!', 'success');
            closeDeleteModal();
        }
    }

    // ===== Format Currency Input =====
    function setupCurrencyInputs() {
        const targetInput = document.getElementById('goal_target');
        const currentInput = document.getElementById('goal_current');

        function formatInput(input) {
            let value = input.value.replace(/\D/g, '');
            value = (parseInt(value) / 100).toFixed(2);
            input.value = formatCurrency(value);
        }

        if (targetInput) {
            targetInput.addEventListener('input', () => formatInput(targetInput));
        }
        if (currentInput) {
            currentInput.addEventListener('input', () => formatInput(currentInput));
        }
    }

    // ===== Icon Selector =====
    function setupIconSelector() {
        const iconOptions = document.querySelectorAll('.icon-option');
        const iconInput = document.getElementById('goal_icon');

        iconOptions.forEach(btn => {
            btn.addEventListener('click', () => {
                iconOptions.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                iconInput.value = btn.dataset.icon;
            });
        });
    }

    // ===== Show Toast =====
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `custom-toast ${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ===== Event Listeners =====
    if (goalForm) {
        goalForm.addEventListener('submit', saveGoal);
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', deleteGoal);
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeGoalModal();
            closeDeleteModal();
        }
    });

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeGoalModal();
                closeDeleteModal();
            }
        });
    });

    // ===== Initialize =====
    function init() {
        setupCurrencyInputs();
        setupIconSelector();
        loadGoals();
    }

    window.closeDeleteModal = closeDeleteModal;
    window.editGoal = editGoal;
    window.confirmDeleteGoal = confirmDeleteGoal;
    window.completeGoal = completeGoal;
    window.openGoalModal = openGoalModal;
    window.closeGoalModal = closeGoalModal;

    window.translations = {
        noGoals: 'Nenhuma meta cadastrada',
        addGoalHint: 'Clique em "Nova Meta" para começar',
        save: 'Salvar',
        update: 'Atualizar'
    };

    init();
})();