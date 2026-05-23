// MyLedger - Goals JavaScript
// Funcionalidades da tela de metas financeiras com backend

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

    // ===== CSRF Token =====
    function getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookieValue ? cookieValue.split('=')[1] : '';
    }

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function parseCurrency(value) {
        if (!value) return 0;
        // Remove tudo exceto números, vírgula e ponto
        let cleaned = value.toString().replace(/[^0-9,-]/g, '');
        cleaned = cleaned.replace(',', '.');
        return parseFloat(cleaned) || 0;
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    }

    function calculateProgress(current, target) {
        if (target <= 0) return 0;
        return Math.min((current / target) * 100, 100).toFixed(1);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== API Calls =====
    async function loadGoalsFromBackend() {
        try {
            const response = await fetch('/goals/api/get/', {
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                }
            });
            const data = await response.json();

            if (data.success) {
                goals = data.goals;
                renderGoals();
                updateSummary();
                updateStats();
            } else {
                showToast('Erro ao carregar metas', 'error');
            }
        } catch (error) {
            console.error('Erro ao carregar metas:', error);
            showToast('Erro de conexão com o servidor', 'error');
        }
    }

    async function updateStats() {
        try {
            const response = await fetch('/goals/api/stats/', {
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                }
            });
            const data = await response.json();

            if (data.success) {
                if (activeGoalsCountSpan) activeGoalsCountSpan.textContent = data.stats.active_goals;
                if (completedGoalsCountSpan) completedGoalsCountSpan.textContent = data.stats.completed_goals;
                if (totalProgressSpan) totalProgressSpan.textContent = `${data.stats.total_progress}%`;
                if (totalSavedSpan) totalSavedSpan.textContent = formatCurrency(data.stats.total_saved);
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    }

    async function saveGoalToBackend(goalData) {
        const isEditing = goalData.id;
        const url = isEditing ? `/goals/api/update/${goalData.id}/` : '/goals/api/create/';
        const method = isEditing ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(goalData)
            });

            const data = await response.json();

            if (data.success) {
                showToast(data.message, 'success');
                await loadGoalsFromBackend();
                closeGoalModal();
                return true;
            } else {
                const errorMsg = data.errors ? Object.values(data.errors).flat().join(', ') : data.error;
                showToast(errorMsg || 'Erro ao salvar meta', 'error');
                return false;
            }
        } catch (error) {
            console.error('Erro ao salvar meta:', error);
            showToast('Erro de conexão com o servidor', 'error');
            return false;
        }
    }

    async function deleteGoalFromBackend(goalId) {
        try {
            const response = await fetch(`/goals/api/delete/${goalId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                }
            });

            const data = await response.json();

            if (data.success) {
                showToast(data.message, 'success');
                await loadGoalsFromBackend();
                return true;
            } else {
                showToast(data.error || 'Erro ao excluir meta', 'error');
                return false;
            }
        } catch (error) {
            console.error('Erro ao excluir meta:', error);
            showToast('Erro de conexão com o servidor', 'error');
            return false;
        }
    }

    async function completeGoalInBackend(goalId) {
        try {
            const response = await fetch(`/goals/api/complete/${goalId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                }
            });

            const data = await response.json();

            if (data.success) {
                showToast(data.message, 'success');
                await loadGoalsFromBackend();
                return true;
            } else {
                showToast(data.error || 'Erro ao concluir meta', 'error');
                return false;
            }
        } catch (error) {
            console.error('Erro ao concluir meta:', error);
            showToast('Erro de conexão com o servidor', 'error');
            return false;
        }
    }

    // ===== Render Goals =====
    function renderGoals() {
        if (!goalsGrid) return;

        if (goals.length === 0) {
            goalsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bullseye"></i>
                    <p>Nenhuma meta cadastrada</p>
                    <small>Clique em "Nova Meta" para começar</small>
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
                        <div class="goal-deadline ${goal.deadline_status}">
                            <i class="fas fa-calendar-alt"></i>
                            <span>${goal.deadline_text}</span>
                        </div>
                    </div>
                    <div class="goal-actions">
                        <button class="goal-action edit" onclick="window.editGoal(${goal.id})" title="Editar">
                            <i class="fas fa-pencil-alt"></i>
                        </button>
                        <button class="goal-action delete" onclick="window.confirmDeleteGoal(${goal.id})" title="Excluir">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                ${goal.description ? `<div class="goal-description">${escapeHtml(goal.description)}</div>` : ''}
                <div class="goal-progress">
                    <div class="progress-header">
                        <span class="progress-label">Progresso</span>
                        <span class="progress-value">${goal.progress_percentage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${goal.progress_percentage}%; background: ${goal.completed ? '#10b981' : '#8A4FFF'}"></div>
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
                        <div class="stat-value remaining">${formatCurrency(goal.remaining_amount)}</div>
                    </div>
                </div>
                ${!goal.completed && goal.is_completable ? `
                    <div class="goal-complete-banner">
                        <button class="btn-complete-goal" onclick="window.completeGoal(${goal.id})">
                            <i class="fas fa-check-circle"></i>
                            <span>Marcar como concluída</span>
                        </button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    async function updateSummary() {
        await updateStats();
    }

    // ===== Modal Functions =====
    window.openGoalModal = function (id = null) {
        editingId = id;

        if (id) {
            const goal = goals.find(g => g.id === id);
            if (goal) {
                modalTitle.textContent = 'Editar Meta';
                submitBtnText.textContent = 'Atualizar';
                goalIdInput.value = goal.id;
                document.getElementById('goal_title').value = goal.title;
                document.getElementById('goal_target').value = goal.target;
                document.getElementById('goal_deadline').value = goal.deadline;
                document.getElementById('goal_current').value = goal.current;
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
    async function saveGoal(event) {
        event.preventDefault();

        const id = goalIdInput.value ? parseInt(goalIdInput.value) : null;
        const title = document.getElementById('goal_title').value.trim();
        let target = document.getElementById('goal_target').value;
        let current = document.getElementById('goal_current').value;
        const deadline = document.getElementById('goal_deadline').value;
        const description = document.getElementById('goal_description').value;
        const icon = document.getElementById('goal_icon').value;

        // Parse currency values
        target = parseCurrency(target);
        current = parseCurrency(current);

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

        // Show loading state on button
        const submitBtn = document.querySelector('#goalForm .btn-submit');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        submitBtn.disabled = true;

        const goalData = {
            title: title,
            target: target,
            current: current,
            deadline: deadline,
            description: description,
            icon: icon
        };

        if (id) {
            goalData.id = id;
        }

        const success = await saveGoalToBackend(goalData);

        // Restore button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }

    // ===== Edit Goal =====
    window.editGoal = function (id) {
        openGoalModal(id);
    };

    // ===== Complete Goal =====
    window.completeGoal = async function (id) {
        await completeGoalInBackend(id);
    };

    // ===== Delete Goal =====
    window.confirmDeleteGoal = function (id) {
        goalToDelete = id;
        if (deleteModal) {
            deleteModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeDeleteModal = function () {
        if (deleteModal) {
            deleteModal.style.display = 'none';
            document.body.style.overflow = '';
            goalToDelete = null;
        }
    };

    async function deleteGoal() {
        if (goalToDelete !== null) {
            await deleteGoalFromBackend(goalToDelete);
            closeDeleteModal();
        }
    }

    // ===== Format Currency Input =====
    function setupCurrencyInputs() {
        const targetInput = document.getElementById('goal_target');
        const currentInput = document.getElementById('goal_current');

        function formatInput(input) {
            if (input && input.value) {
                let value = parseCurrency(input.value);
                if (!isNaN(value)) {
                    input.value = value;
                }
            }
        }

        if (targetInput) {
            targetInput.addEventListener('blur', () => formatInput(targetInput));
            targetInput.addEventListener('input', function () {
                let value = this.value.replace(/\D/g, '');
                if (value) {
                    value = (parseInt(value) / 100).toFixed(2);
                    this.value = value;
                }
            });
        }
        if (currentInput) {
            currentInput.addEventListener('blur', () => formatInput(currentInput));
            currentInput.addEventListener('input', function () {
                let value = this.value.replace(/\D/g, '');
                if (value) {
                    value = (parseInt(value) / 100).toFixed(2);
                    this.value = value;
                }
            });
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
        // Check if toast container exists, if not create one
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

    document.addEventListener('click', (e) => {
        if (goalModal && e.target === goalModal) {
            closeGoalModal();
        }
        if (deleteModal && e.target === deleteModal) {
            closeDeleteModal();
        }
    });

    // ===== Initialize =====
    function init() {
        setupCurrencyInputs();
        setupIconSelector();
        loadGoalsFromBackend();
    }

    // Expose functions globally
    window.editGoal = editGoal;
    window.confirmDeleteGoal = confirmDeleteGoal;
    window.completeGoal = completeGoal;
    window.openGoalModal = openGoalModal;
    window.closeGoalModal = closeGoalModal;
    window.closeDeleteModal = closeDeleteModal;

    init();
})();