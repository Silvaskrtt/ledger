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
    let allCategories = [];

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function formatDate(dateString) {
        const [year, month, day] = dateString.split('-').map(Number);
        const date = new Date(year, month - 1, day);
        return date.toLocaleDateString('pt-BR');
    }

    // ===== FUNÇÃO CORRIGIDA: Parse Amount =====
    function parseAmountToNumber(amountString) {
        if (!amountString) return 0;

        // Remove "R$" se presente
        let cleanValue = amountString.replace(/R\$/g, '').trim();

        // Se estiver vazio após remover R$, retorna 0
        if (cleanValue === '') return 0;

        // Substitui ponto de milhar por nada (remove)
        cleanValue = cleanValue.replace(/\./g, '');

        // Substitui vírgula por ponto (separador decimal)
        cleanValue = cleanValue.replace(/,/g, '.');

        // Remove qualquer caractere que não seja número ou ponto
        cleanValue = cleanValue.replace(/[^0-9.]/g, '');

        const number = parseFloat(cleanValue);
        return isNaN(number) ? 0 : number;
    }

    // ===== FUNÇÃO CORRIGIDA: Formatar valor para exibição =====
    function formatAmountToDisplay(value) {
        if (!value) return '';
        const num = typeof value === 'string' ? parseAmountToNumber(value) : value;
        if (isNaN(num) || num === 0) return '';
        return formatCurrency(num);
    }

    // ===== Load Categories =====
    async function loadCategories() {
        try {
            const response = await fetch('/categories/api/categories/');
            const data = await response.json();

            allCategories = data.categories || [];

            if (categorySelect) {
                const currentValue = categorySelect.value;
                categorySelect.innerHTML = '<option value="">Selecione uma categoria</option>';

                allCategories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = `${cat.icon || '📌'} ${cat.name}`;
                    categorySelect.appendChild(option);
                });

                if (currentValue && Array.from(categorySelect.options).some(opt => opt.value === currentValue)) {
                    categorySelect.value = currentValue;
                }
            }

            if (categoryFilter) {
                const currentFilterValue = categoryFilter.value;
                categoryFilter.innerHTML = '<option value="all">Todas as categorias</option>';

                allCategories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.name;
                    option.textContent = `${cat.icon || '📌'} ${cat.name}`;
                    categoryFilter.appendChild(option);
                });

                if (currentFilterValue && currentFilterValue !== 'all') {
                    categoryFilter.value = currentFilterValue;
                }
            }

            console.log(`✅ ${allCategories.length} categorias carregadas`);

        } catch (error) {
            console.error('Erro ao carregar categorias:', error);
            showToast('Erro ao carregar categorias', 'error');
        }
    }

    // ===== Category Modal =====
    window.openCategoryModal = function () {
        const categoryModal = document.getElementById('categoryModal');
        if (categoryModal) {
            const categoryForm = document.getElementById('categoryForm');
            if (categoryForm) categoryForm.reset();
            categoryModal.style.display = 'flex';
        }
    };

    window.closeCategoryModal = function () {
        const categoryModal = document.getElementById('categoryModal');
        if (categoryModal) {
            categoryModal.style.display = 'none';
        }
    };

    // ===== Save Category =====
    async function saveCategory() {
        const form = document.getElementById('categoryForm');
        if (!form) return;

        const formData = new FormData(form);
        const categoryData = {
            name: formData.get('name'),
            icon: formData.get('icon') || '📌',
            color: formData.get('color') || '#8A4FFF',
            type: 'expense'
        };

        if (!categoryData.name || categoryData.name.trim() === '') {
            showToast('Por favor, informe o nome da categoria', 'error');
            return;
        }

        try {
            const response = await fetch('/categories/api/categories/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(categoryData)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    showToast('Categoria criada com sucesso!', 'success');
                    closeCategoryModal();
                    await loadCategories();
                    form.reset();
                } else {
                    showToast(result.error || 'Erro ao criar categoria', 'error');
                }
            } else {
                const error = await response.json();
                showToast(error.error || 'Erro ao criar categoria', 'error');
            }
        } catch (error) {
            console.error('Erro ao salvar categoria:', error);
            showToast('Erro ao criar categoria', 'error');
        }
    }

    // ===== Get Cookie =====
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

    // ===== Show Toast =====
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

    // ===== Save Transaction =====
    async function saveTransaction(formData) {
        const transactionId = formData.get('transaction_id');
        const isEditing = transactionId && transactionId !== '';

        // CORREÇÃO: Usa a função parseAmountToNumber para converter corretamente
        let amountString = formData.get('amount') || '0';
        const amount = parseAmountToNumber(amountString);

        const transactionData = {
            description: formData.get('description') || '',
            amount: amount,
            date: formData.get('date') || '',
            category: formData.get('category') || '',
            type: formData.get('transaction_type') || 'expense',
            notes: formData.get('notes') || ''
        };

        // Validação
        const errors = [];
        if (!transactionData.description || transactionData.description.trim() === '') {
            errors.push('Por favor, informe uma descrição');
        }
        if (transactionData.amount <= 0) {
            errors.push('Por favor, informe um valor válido maior que zero');
        }
        if (!transactionData.date) {
            errors.push('Por favor, informe uma data');
        }
        if (!transactionData.category) {
            errors.push('Por favor, selecione uma categoria');
        }

        if (errors.length > 0) {
            errors.forEach(error => showToast(error, 'error'));
            return;
        }

        const submitBtn = document.querySelector('#transactionModal .btn-submit');
        const originalText = submitBtn?.textContent || 'Salvar';
        if (submitBtn) {
            submitBtn.textContent = 'Salvando...';
            submitBtn.disabled = true;
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

            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                throw new Error('Erro no servidor');
            }

            if (response.ok && data.success) {
                showToast(
                    isEditing ? 'Transação atualizada com sucesso!' : 'Transação criada com sucesso!',
                    'success'
                );
                window.closeTransactionModal();
                await loadTransactions();
                if (!isEditing) currentPage = 1;
            } else {
                const errorMsg = data.error || data.message || 'Erro ao salvar transação';
                showToast(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Error saving transaction:', error);
            showToast('Erro ao conectar com o servidor', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        }
    }

    // ===== Open Transaction Modal =====
    window.openTransactionModal = async function () {
        if (!transactionModal) {
            console.error('Modal de transação não encontrado');
            showToast('Erro ao abrir formulário', 'error');
            return;
        }

        await loadCategories();

        if (transactionForm) transactionForm.reset();
        if (transactionIdInput) transactionIdInput.value = '';
        if (transactionTypeInput) transactionTypeInput.value = 'expense';
        if (transactionModalTitle) transactionModalTitle.textContent = 'Nova Transação';
        if (submitBtnText) submitBtnText.textContent = 'Salvar';

        if (typeButtons && typeButtons.length) {
            typeButtons.forEach(btn => btn.classList.remove('active'));
            const expenseBtn = document.querySelector('.type-btn.expense');
            if (expenseBtn) expenseBtn.classList.add('active');
        }

        if (dateInput) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.value = today;
        }

        if (amountInput) amountInput.value = '';

        transactionModal.style.display = 'flex';
    };

    // ===== Edit Transaction =====
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

        await loadCategories();

        if (transactionModalTitle) transactionModalTitle.textContent = 'Editar Transação';
        if (submitBtnText) submitBtnText.textContent = 'Atualizar';
        if (transactionIdInput) transactionIdInput.value = id;
        if (descriptionInput) descriptionInput.value = transaction.description || '';

        // CORREÇÃO: Formata o valor para exibição
        if (amountInput) amountInput.value = formatAmountToDisplay(transaction.amount);

        if (dateInput) dateInput.value = transaction.date;

        if (categorySelect && transaction.category) {
            const category = allCategories.find(c => c.name === transaction.category);
            if (category) {
                categorySelect.value = category.id;
            }
        }

        if (notesTextarea) notesTextarea.value = transaction.notes || '';

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

    // ===== Close Transaction Modal =====
    window.closeTransactionModal = function () {
        if (transactionModal) transactionModal.style.display = 'none';
    };

    // ===== Confirm Delete =====
    window.confirmDelete = function (id) {
        transactionToDelete = id;
        if (deleteModal) deleteModal.style.display = 'flex';
    };

    window.closeDeleteModal = function () {
        if (deleteModal) deleteModal.style.display = 'none';
        transactionToDelete = null;
    };

    // ===== Load Transactions =====
    async function loadTransactions() {
        if (!window.transactionsApiUrl) {
            console.error('API URL not configured');
            showToast('Erro de configuração da API', 'error');
            return;
        }

        try {
            if (transactionsList) {
                transactionsList.innerHTML = `<div class="loading-skeleton">Carregando...</div>`;
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
        }
    }

    function renderTransactions() {
        if (!transactionsList) return;
        if (!transactions || transactions.length === 0) {
            transactionsList.innerHTML = `<div class="empty-state">Nenhuma transação encontrada</div>`;
            return;
        }

        transactionsList.innerHTML = transactions.map(transaction => `
            <div class="transaction-row" data-id="${transaction.id}">
                <div class="transaction-date">${formatDate(transaction.date)}</div>
                <div class="transaction-description">${escapeHtml(transaction.description)}</div>
                <div class="transaction-category">
                    <span class="category-name">${escapeHtml(transaction.category)}</span>
                </div>
                <div class="transaction-amount ${transaction.type === 'income' ? 'income' : 'expense'}">
                    ${transaction.type === 'income' ? '+' : '-'} ${formatCurrency(transaction.amount)}
                </div>
                <div class="transaction-actions">
                    <button class="action-icon edit" onclick="window.editTransaction(${transaction.id})">✏️</button>
                    <button class="action-icon delete" onclick="window.confirmDelete(${transaction.id})">🗑️</button>
                </div>
            </div>
        `).join('');
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function updatePagination(data) {
        if (pageInfo) pageInfo.textContent = `Página ${data.current_page || 1} de ${data.total_pages || 1}`;
        if (prevPageBtn) prevPageBtn.disabled = !data.has_previous;
        if (nextPageBtn) nextPageBtn.disabled = !data.has_next;
    }

    // ===== Delete Transaction =====
    async function deleteTransaction() {
        if (transactionToDelete === null) return;
        try {
            const response = await fetch(`/transactions/api/transactions/${transactionToDelete}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
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
        window.closeDeleteModal();
    }

    // ===== Setup Event Listeners =====
    function setupEventListeners() {
        if (searchInput) searchInput.addEventListener('input', () => { currentPage = 1; loadTransactions(); });
        if (typeFilter) typeFilter.addEventListener('change', () => { currentPage = 1; loadTransactions(); });
        if (categoryFilter) categoryFilter.addEventListener('change', () => { currentPage = 1; loadTransactions(); });
        if (monthFilter) monthFilter.addEventListener('change', () => { currentPage = 1; loadTransactions(); });
        if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (typeFilter) typeFilter.value = 'all';
            if (categoryFilter) categoryFilter.value = 'all';
            if (monthFilter) monthFilter.value = '';
            currentPage = 1;
            loadTransactions();
        });
        if (prevPageBtn) prevPageBtn.addEventListener('click', () => { currentPage--; loadTransactions(); });
        if (nextPageBtn) nextPageBtn.addEventListener('click', () => { currentPage++; loadTransactions(); });
        if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', deleteTransaction);

        const categoryForm = document.getElementById('categoryForm');
        if (categoryForm) {
            categoryForm.addEventListener('submit', (e) => {
                e.preventDefault();
                saveCategory();
            });
        }

        if (transactionForm) {
            transactionForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await saveTransaction(new FormData(transactionForm));
            });
        }

        if (typeButtons) {
            typeButtons.forEach(btn => {
                btn.addEventListener('click', function () {
                    typeButtons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    if (transactionTypeInput) transactionTypeInput.value = this.dataset.type;
                });
            });
        }

        // CORREÇÃO: Formatação do campo de valor
        if (amountInput) {
            // Quando o campo perde o foco, formata o valor
            amountInput.addEventListener('blur', function (e) {
                const value = e.target.value;
                if (value) {
                    const num = parseAmountToNumber(value);
                    if (num > 0) {
                        e.target.value = formatAmountToDisplay(num);
                    }
                }
            });

            // Permite apenas números, vírgula e ponto
            amountInput.addEventListener('input', function (e) {
                // Mantém apenas números, vírgula e ponto
                let value = e.target.value.replace(/[^0-9,.]/g, '');
                e.target.value = value;
            });

            // Ao pressionar Enter, aplica a formatação
            amountInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.blur();
                }
            });
        }

        // Fechar modais ao clicar fora
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

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (deleteModal?.style.display === 'flex') window.closeDeleteModal();
                if (transactionModal?.style.display === 'flex') window.closeTransactionModal();
            }
        });
    }

    // ===== Initialize =====
    async function init() {
        setupEventListeners();
        await loadCategories();
        loadTransactions();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export functions to window
    window.openTransactionModal = openTransactionModal;
    window.editTransaction = editTransaction;
    window.closeTransactionModal = closeTransactionModal;
    window.openCategoryModal = openCategoryModal;
    window.closeCategoryModal = closeCategoryModal;
    window.confirmDelete = confirmDelete;
    window.closeDeleteModal = closeDeleteModal;
    window.goToAddTransaction = openTransactionModal;

})();