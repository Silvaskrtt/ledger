// MyLedger - Transactions JavaScript
// Funcionalidades da tela de listagem de transações

(function () {
    'use strict';

    // ===== DOM Elements =====
    const transactionsList = document.getElementById('transactionsList');
    const searchInput = document.getElementById('searchInput');
    const typeFilter = document.getElementById('typeFilter');
    const categoryFilter = document.getElementById('categoryFilter');
    const monthFilter = document.getElementById('monthFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');
    const totalIncomeSpan = document.getElementById('totalIncome');
    const totalExpenseSpan = document.getElementById('totalExpense');
    const totalBalanceSpan = document.getElementById('totalBalance');
    const deleteModal = document.getElementById('deleteModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // ===== Modal Elements - Com verificação =====
    const transactionModal = document.getElementById('transactionModal');
    const transactionForm = document.getElementById('transactionForm');
    const transactionModalTitle = document.getElementById('transactionModalTitle');
    const submitBtnText = document.getElementById('submitBtnText');
    const transactionIdInput = document.getElementById('transaction_id');
    const transactionTypeInput = document.getElementById('transaction_type');
    const descriptionInput = document.getElementById('description');
    const amountInput = document.getElementById('amount');
    const dateInput = document.getElementById('date');
    const categorySelect = document.getElementById('category');
    const notesTextarea = document.getElementById('notes');
    const typeButtons = document.querySelectorAll('.type-btn');

    // ===== State =====
    let transactions = [];
    let currentPage = 1;
    let totalPages = 1;
    let transactionToDelete = null;

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

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
        toast.className = `toast ${type}`;
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

    // ===== Load Transactions =====
    async function loadTransactions() {
        if (!window.transactionsApiUrl) {
            console.error('API URL not configured');
            showToast('Erro de configuração da API', 'error');
            return;
        }

        try {
            if (transactionsList) {
                transactionsList.innerHTML = `
                    <div class="loading-skeleton">
                        <div class="skeleton-row"></div>
                        <div class="skeleton-row"></div>
                        <div class="skeleton-row"></div>
                    </div>
                `;
            }

            const params = new URLSearchParams();
            if (searchInput?.value) params.append('search', searchInput.value);
            if (typeFilter?.value && typeFilter.value !== 'all') params.append('type', typeFilter.value);
            if (categoryFilter?.value && categoryFilter.value !== 'all') params.append('category', categoryFilter.value);
            if (monthFilter?.value) params.append('month', monthFilter.value);
            params.append('page', currentPage);

            const url = `${window.transactionsApiUrl}?${params.toString()}`;
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();

            transactions = data.transactions || [];
            totalPages = data.total_pages || 1;

            if (totalIncomeSpan) totalIncomeSpan.textContent = formatCurrency(data.total_income || 0);
            if (totalExpenseSpan) totalExpenseSpan.textContent = formatCurrency(data.total_expense || 0);
            if (totalBalanceSpan) {
                const balance = (data.total_income || 0) - (data.total_expense || 0);
                totalBalanceSpan.textContent = formatCurrency(balance);
                totalBalanceSpan.style.color = balance >= 0 ? '#10b981' : '#ef4444';
            }

            updatePagination(data);
            renderTransactions();

        } catch (error) {
            console.error('Error loading transactions:', error);
            showToast('Erro ao carregar transações', 'error');
            if (transactionsList) {
                transactionsList.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Erro ao carregar transações</p>
                        <button onclick="location.reload()">Tentar novamente</button>
                    </div>
                `;
            }
        }
    }

    // ===== Render Transactions =====
    function renderTransactions() {
        if (!transactionsList) return;

        if (!transactions || transactions.length === 0) {
            transactionsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>Nenhuma transação encontrada</p>
                    <button class="btn-add" onclick="window.openTransactionModal()" style="margin-top: 16px;">
                        <i class="fas fa-plus"></i> Adicionar transação
                    </button>
                </div>
            `;
            return;
        }

        transactionsList.innerHTML = transactions.map(transaction => `
            <div class="transaction-row fade-up" data-id="${transaction.id}">
                <div class="transaction-date">${formatDate(transaction.date)}</div>
                <div class="transaction-description">${escapeHtml(transaction.description)}</div>
                <div class="transaction-category">
                    <div class="category-icon">${transaction.categoryIcon || '📌'}</div>
                    <span class="category-name">${escapeHtml(transaction.category)}</span>
                </div>
                <div class="transaction-amount ${transaction.type === 'income' ? 'income' : 'expense'}">
                    ${transaction.type === 'income' ? '+' : '-'} ${formatCurrency(transaction.amount)}
                </div>
                <div class="transaction-actions">
                    <button class="action-icon edit" onclick="window.editTransaction(${transaction.id})" title="Editar">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                    <button class="action-icon delete" onclick="window.confirmDelete(${transaction.id})" title="Excluir">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    // ===== Pagination =====
    function updatePagination(data) {
        if (pageInfo) {
            pageInfo.textContent = `Página ${data.current_page || 1} de ${data.total_pages || 1}`;
        }
        if (prevPageBtn) prevPageBtn.disabled = !data.has_previous;
        if (nextPageBtn) nextPageBtn.disabled = !data.has_next;
    }

    function nextPage() {
        if (nextPageBtn && !nextPageBtn.disabled) {
            currentPage++;
            loadTransactions();
            transactionsList?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function prevPage() {
        if (prevPageBtn && !prevPageBtn.disabled) {
            currentPage--;
            loadTransactions();
            transactionsList?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // ===== Delete Transaction =====
    window.confirmDelete = function (id) {
        transactionToDelete = id;
        if (deleteModal) deleteModal.style.display = 'flex';
    };

    window.closeDeleteModal = function () {
        if (deleteModal) deleteModal.style.display = 'none';
        transactionToDelete = null;
    };

    async function deleteTransaction() {
        if (transactionToDelete === null) return;

        try {
            const response = await fetch(
                `/transactions/api/transactions/${transactionToDelete}/delete/`,
                {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }
            );

            const data = await response.json();

            if (data.success) {
                showToast('Transação excluída com sucesso!', 'success');
                await loadTransactions();
            } else {
                showToast(data.error || 'Erro ao excluir transação', 'error');
            }
        } catch (error) {
            console.error('Error deleting transaction:', error);
            showToast('Erro ao excluir transação', 'error');
        }

        closeDeleteModal();
    }

    // ===== Modal Functions - Com verificações de segurança =====
    window.openTransactionModal = function () {
        // Verificar se o modal existe
        if (!transactionModal) {
            console.error('Modal de transação não encontrado');
            showToast('Erro ao abrir formulário', 'error');
            return;
        }

        // Resetar o formulário
        if (transactionForm) transactionForm.reset();
        if (transactionIdInput) transactionIdInput.value = '';
        if (transactionTypeInput) transactionTypeInput.value = 'expense';
        if (transactionModalTitle) transactionModalTitle.textContent = 'Nova Transação';
        if (submitBtnText) submitBtnText.textContent = 'Salvar';

        // Resetar botões de tipo
        if (typeButtons && typeButtons.length) {
            typeButtons.forEach(btn => btn.classList.remove('active'));
            const expenseBtn = document.querySelector('.type-btn.expense');
            if (expenseBtn) expenseBtn.classList.add('active');
        }

        // Setar data atual
        if (dateInput) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.value = today;
        }

        transactionModal.style.display = 'flex';
    };

    window.editTransaction = async function (id) {
        const transaction = transactions.find(t => t.id === id);
        if (!transaction) {
            showToast('Transação não encontrada', 'error');
            return;
        }

        if (!transactionModal) {
            console.error('Modal de transação não encontrado');
            return;
        }

        if (transactionModalTitle) transactionModalTitle.textContent = 'Editar Transação';
        if (submitBtnText) submitBtnText.textContent = 'Atualizar';
        if (transactionIdInput) transactionIdInput.value = id;
        if (descriptionInput) descriptionInput.value = transaction.description || '';
        if (amountInput) amountInput.value = formatCurrency(transaction.amount);
        if (dateInput) dateInput.value = transaction.date;
        if (categorySelect) categorySelect.value = transaction.category || '';
        if (notesTextarea) notesTextarea.value = transaction.notes || '';

        // Setar tipo
        const type = transaction.type;
        if (typeButtons && typeButtons.length) {
            typeButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.type === type) btn.classList.add('active');
            });
        }
        if (transactionTypeInput) transactionTypeInput.value = type;

        transactionModal.style.display = 'flex';
    };

    window.closeTransactionModal = function () {
        if (transactionModal) transactionModal.style.display = 'none';
    };

    async function saveTransaction(formData) {
        const transactionId = formData.get('transaction_id');
        const isEditing = transactionId && transactionId !== '';

        let amountValue = formData.get('amount') || '0';
        // Limpar formatação do valor
        amountValue = amountValue.replace(/[R$\s.]/g, '').replace(',', '.');
        const amount = parseFloat(amountValue) || 0;

        const transactionData = {
            description: formData.get('description') || '',
            amount: amount,
            date: formData.get('date') || '',
            category: formData.get('category') || '',
            transaction_type: formData.get('transaction_type') || 'expense',
            notes: formData.get('notes') || ''
        };

        // Validação básica
        if (!transactionData.description) {
            showToast('Por favor, informe uma descrição', 'error');
            return;
        }
        if (transactionData.amount <= 0) {
            showToast('Por favor, informe um valor válido', 'error');
            return;
        }
        if (!transactionData.date) {
            showToast('Por favor, informe uma data', 'error');
            return;
        }
        if (!transactionData.category) {
            showToast('Por favor, selecione uma categoria', 'error');
            return;
        }

        try {
            let url, method;
            if (isEditing) {
                url = `/transactions/api/transactions/${transactionId}/update/`;
                method = 'PUT';
            } else {
                url = '/transactions/api/transactions/create/';
                method = 'POST';
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(transactionData)
            });

            const data = await response.json();

            if (data.success) {
                showToast(
                    isEditing ? 'Transação atualizada!' : 'Transação criada!',
                    'success'
                );
                closeTransactionModal();
                await loadTransactions();
            } else {
                showToast(data.error || 'Erro ao salvar', 'error');
            }
        } catch (error) {
            console.error('Error saving transaction:', error);
            showToast('Erro ao salvar transação', 'error');
        }
    }

    // ===== Setup =====
    function setupEventListeners() {
        if (searchInput) searchInput.addEventListener('input', () => { currentPage = 1; loadTransactions(); });
        if (typeFilter) typeFilter.addEventListener('change', () => { currentPage = 1; loadTransactions(); });
        if (categoryFilter) categoryFilter.addEventListener('change', () => { currentPage = 1; loadTransactions(); });
        if (monthFilter) monthFilter.addEventListener('change', () => { currentPage = 1; loadTransactions(); });

        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                if (searchInput) searchInput.value = '';
                if (typeFilter) typeFilter.value = 'all';
                if (categoryFilter) categoryFilter.value = 'all';
                if (monthFilter) monthFilter.value = '';
                currentPage = 1;
                loadTransactions();
            });
        }

        if (prevPageBtn) prevPageBtn.addEventListener('click', prevPage);
        if (nextPageBtn) nextPageBtn.addEventListener('click', nextPage);
        if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', deleteTransaction);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (deleteModal?.style.display === 'flex') closeDeleteModal();
                if (transactionModal?.style.display === 'flex') closeTransactionModal();
            }
        });

        [deleteModal, transactionModal].forEach(modal => {
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        if (modal.id === 'deleteModal') window.closeDeleteModal();
                        if (modal.id === 'transactionModal') window.closeTransactionModal();
                    }
                });
            }
        });

        // Type buttons
        if (typeButtons && typeButtons.length) {
            typeButtons.forEach(btn => {
                btn.addEventListener('click', function () {
                    typeButtons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    if (transactionTypeInput) transactionTypeInput.value = this.dataset.type;
                });
            });
        }

        // Amount input formatting
        if (amountInput) {
            amountInput.addEventListener('input', function (e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value === '') {
                    e.target.value = '';
                    return;
                }
                value = (parseInt(value) / 100).toFixed(2);
                value = value.replace('.', ',');
                e.target.value = `R$ ${value}`;
            });
        }

        // Form submit
        if (transactionForm) {
            transactionForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await saveTransaction(new FormData(transactionForm));
            });
        }
    }

    // Exportar funções para o escopo global
    window.goToAddTransaction = function () {
        window.openTransactionModal();
    };

    window.openTransactionModal = window.openTransactionModal;
    window.editTransaction = window.editTransaction;
    window.confirmDelete = window.confirmDelete;
    window.closeDeleteModal = window.closeDeleteModal;
    window.closeTransactionModal = window.closeTransactionModal;

    // Initialize - Aguardar DOM carregar completamente
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setupEventListeners();
            loadTransactions();
        });
    } else {
        setupEventListeners();
        loadTransactions();
    }
})();