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

    // ===== State =====
    let transactions = [];
    let filteredTransactions = [];
    let currentPage = 1;
    let itemsPerPage = 10;
    let transactionToDelete = null;

    // ===== Sample Data (In production, fetch from API) =====
    const sampleTransactions = [
        { id: 1, type: 'expense', description: 'Supermercado', category: 'Alimentação', categoryIcon: '🍔', amount: 342.50, date: '2025-06-15' },
        { id: 2, type: 'income', description: 'Salário', category: 'Trabalho', categoryIcon: '💼', amount: 5000.00, date: '2025-06-01' },
        { id: 3, type: 'expense', description: 'Uber', category: 'Transporte', categoryIcon: '🚗', amount: 28.90, date: '2025-06-14' },
        { id: 4, type: 'expense', description: 'Netflix', category: 'Lazer', categoryIcon: '🎮', amount: 39.90, date: '2025-06-10' },
        { id: 5, type: 'income', description: 'Freelance', category: 'Trabalho', categoryIcon: '💼', amount: 1200.00, date: '2025-06-08' },
        { id: 6, type: 'expense', description: 'Aluguel', category: 'Moradia', categoryIcon: '🏠', amount: 1500.00, date: '2025-06-05' },
        { id: 7, type: 'expense', description: 'Cinema', category: 'Lazer', categoryIcon: '🎮', amount: 45.00, date: '2025-06-20' },
        { id: 8, type: 'income', description: 'Investimentos', category: 'Outros', categoryIcon: '📈', amount: 350.00, date: '2025-06-25' },
        { id: 9, type: 'expense', description: 'Farmácia', category: 'Saúde', categoryIcon: '💊', amount: 89.50, date: '2025-06-18' },
        { id: 10, type: 'expense', description: 'Curso Online', category: 'Educação', categoryIcon: '📚', amount: 199.00, date: '2025-06-12' },
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

    // ===== Filter Transactions =====
    function filterTransactions() {
        const searchTerm = searchInput?.value.toLowerCase() || '';
        const type = typeFilter?.value || 'all';
        const category = categoryFilter?.value || 'all';
        const month = monthFilter?.value || '';

        filteredTransactions = transactions.filter(transaction => {
            // Search filter
            if (searchTerm && !transaction.description.toLowerCase().includes(searchTerm)) {
                return false;
            }

            // Type filter
            if (type !== 'all' && transaction.type !== type) {
                return false;
            }

            // Category filter
            if (category !== 'all' && transaction.category !== category) {
                return false;
            }

            // Month filter
            if (month) {
                const transactionMonth = transaction.date.substring(0, 7);
                if (transactionMonth !== month) {
                    return false;
                }
            }

            return true;
        });

        // Sort by date (newest first)
        filteredTransactions.sort((a, b) => new Date(b.date) - new Date(a.date));

        currentPage = 1;
        updateSummary();
        renderTransactions();
        updatePagination();
    }

    // ===== Update Summary Cards =====
    function updateSummary() {
        let totalIncome = 0;
        let totalExpense = 0;

        filteredTransactions.forEach(transaction => {
            if (transaction.type === 'income') {
                totalIncome += transaction.amount;
            } else {
                totalExpense += transaction.amount;
            }
        });

        const totalBalance = totalIncome - totalExpense;

        if (totalIncomeSpan) totalIncomeSpan.textContent = formatCurrency(totalIncome);
        if (totalExpenseSpan) totalExpenseSpan.textContent = formatCurrency(totalExpense);
        if (totalBalanceSpan) {
            totalBalanceSpan.textContent = formatCurrency(totalBalance);
            totalBalanceSpan.style.color = totalBalance >= 0 ? '#10b981' : '#ef4444';
        }
    }

    // ===== Render Transactions =====
    function renderTransactions() {
        if (!transactionsList) return;

        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const pageTransactions = filteredTransactions.slice(start, end);

        if (pageTransactions.length === 0) {
            transactionsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>${window.translations?.noTransactions || 'Nenhuma transação encontrada'}</p>
                    <small>${window.translations?.addTransactionHint || 'Adicione sua primeira transação'}</small>
                </div>
            `;
            return;
        }

        transactionsList.innerHTML = pageTransactions.map(transaction => `
            <div class="transaction-row fade-up" data-id="${transaction.id}">
                <div class="transaction-date">${formatDate(transaction.date)}</div>
                <div class="transaction-description">${escapeHtml(transaction.description)}</div>
                <div class="transaction-category">
                    <div class="category-icon">${transaction.categoryIcon || '📌'}</div>
                    <span class="category-name">${transaction.category}</span>
                </div>
                <div class="transaction-amount ${transaction.type === 'income' ? 'income' : 'expense'}">
                    ${transaction.type === 'income' ? '+' : '-'} ${formatCurrency(transaction.amount)}
                </div>
                <div class="transaction-actions">
                    <button class="action-icon edit" onclick="editTransaction(${transaction.id})" title="Editar">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                    <button class="action-icon delete" onclick="confirmDelete(${transaction.id})" title="Excluir">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== Pagination =====
    function updatePagination() {
        const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);

        if (pageInfo) {
            pageInfo.textContent = `${window.translations?.page || 'Página'} ${currentPage} ${window.translations?.of || 'de'} ${totalPages || 1}`;
        }

        if (prevPageBtn) {
            prevPageBtn.disabled = currentPage <= 1;
        }

        if (nextPageBtn) {
            nextPageBtn.disabled = currentPage >= totalPages;
        }
    }

    function nextPage() {
        const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderTransactions();
            updatePagination();
            // Scroll to top
            transactionsList?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function prevPage() {
        if (currentPage > 1) {
            currentPage--;
            renderTransactions();
            updatePagination();
            // Scroll to top
            transactionsList?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // ===== Delete Transaction =====
    window.confirmDelete = function (id) {
        transactionToDelete = id;
        if (deleteModal) {
            deleteModal.style.display = 'flex';
        }
    };

    function closeDeleteModal() {
        if (deleteModal) {
            deleteModal.style.display = 'none';
        }
        transactionToDelete = null;
    }

    function deleteTransaction() {
        if (transactionToDelete !== null) {
            const index = transactions.findIndex(t => t.id === transactionToDelete);
            if (index !== -1) {
                transactions.splice(index, 1);
                filterTransactions();
                showToast('Transação excluída com sucesso!', 'success');
            }
            closeDeleteModal();
        }
    }

    // ===== Edit Transaction =====
    window.editTransaction = function (id) {
        const transaction = transactions.find(t => t.id === id);
        if (transaction) {
            // Store transaction to edit in sessionStorage
            sessionStorage.setItem('editTransaction', JSON.stringify(transaction));
            // Redirect to add/edit page
            window.location.href = '/transactions/add/';
        }
    };

    // ===== Add Transaction =====
    window.goToAddTransaction = function () {
        window.location.href = '/transactions/add/';
    };

    // ===== Clear Filters =====
    function clearFilters() {
        if (searchInput) searchInput.value = '';
        if (typeFilter) typeFilter.value = 'all';
        if (categoryFilter) categoryFilter.value = 'all';
        if (monthFilter) monthFilter.value = '';
        filterTransactions();
    }

    // ===== Load Transactions from API =====
    async function loadTransactions() {
        if (!window.transactionsApiUrl) {
            console.error('API URL not configured');
            showToast('Erro de configuração da API', 'error');
            return;
        }

        try {
            // Mostrar loading
            if (transactionsList) {
                transactionsList.innerHTML = `
                <div class="loading-skeleton">
                    <div class="skeleton-row"></div>
                    <div class="skeleton-row"></div>
                    <div class="skeleton-row"></div>
                </div>
            `;
            }

            // Construir URL com filtros
            const params = new URLSearchParams();
            if (searchInput?.value) params.append('search', searchInput.value);
            if (typeFilter?.value && typeFilter.value !== 'all') params.append('type', typeFilter.value);
            if (categoryFilter?.value && categoryFilter.value !== 'all') params.append('category', categoryFilter.value);
            if (monthFilter?.value) params.append('month', monthFilter.value);
            params.append('page', currentPage);

            const url = `${window.transactionsApiUrl}?${params.toString()}`;

            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Atualizar dados
            transactions = data.transactions;
            filteredTransactions = [...transactions];

            // Atualizar totais
            if (totalIncomeSpan) totalIncomeSpan.textContent = formatCurrency(data.total_income);
            if (totalExpenseSpan) totalExpenseSpan.textContent = formatCurrency(data.total_expense);
            if (totalBalanceSpan) {
                totalBalanceSpan.textContent = formatCurrency(data.balance);
                totalBalanceSpan.style.color = data.balance >= 0 ? '#10b981' : '#ef4444';
            }

            // Atualizar paginação
            updatePaginationFromAPI(data);

            // Renderizar transações
            renderTransactions();

        } catch (error) {
            console.error('Error loading transactions:', error);
            showToast('Erro ao carregar transações do servidor', 'error');

            // Fallback para dados locais se a API falhar
            if (confirm('Erro ao conectar com o servidor. Deseja usar dados de exemplo?')) {
                loadSampleData();
            }
        }
    }

    // Função para atualizar paginação com dados da API
    function updatePaginationFromAPI(data) {
        if (pageInfo) {
            pageInfo.textContent = `${window.translations?.page || 'Página'} ${data.current_page} ${window.translations?.of || 'de'} ${data.total_pages}`;
        }

        if (prevPageBtn) {
            prevPageBtn.disabled = !data.has_previous;
        }

        if (nextPageBtn) {
            nextPageBtn.disabled = !data.has_next;
        }
    }

    // Fallback para dados de exemplo
    function loadSampleData() {
        const savedTransactions = localStorage.getItem('myledger_transactions');
        if (savedTransactions) {
            transactions = JSON.parse(savedTransactions);
        } else {
            transactions = [...sampleTransactions];
        }
        filteredTransactions = [...transactions];
        updateSummary();
        renderTransactions();
        updatePagination();
    }

    // Atualizar função de delete para usar API
    async function deleteTransaction() {
        if (transactionToDelete !== null) {
            try {
                const response = await fetch(window.transactionsApiUrl, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ id: transactionToDelete })
                });

                const data = await response.json();

                if (data.success) {
                    showToast('Transação excluída com sucesso!', 'success');
                    await loadTransactions(); // Recarregar lista
                } else {
                    showToast(data.error || 'Erro ao excluir transação', 'error');
                }
            } catch (error) {
                console.error('Error deleting transaction:', error);
                showToast('Erro ao excluir transação', 'error');
            }

            closeDeleteModal();
        }
    }

    // Função auxiliar para pegar CSRF token
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

    // Atualizar filterTransactions para chamar API
    function filterTransactions() {
        currentPage = 1;
        loadTransactions(); // Recarregar da API em vez de filtrar localmente
    }

    function saveTransactions() {
        localStorage.setItem('myledger_transactions', JSON.stringify(transactions));
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

    // ===== Event Listeners =====
    function setupEventListeners() {
        if (searchInput) searchInput.addEventListener('input', filterTransactions);
        if (typeFilter) typeFilter.addEventListener('change', filterTransactions);
        if (categoryFilter) categoryFilter.addEventListener('change', filterTransactions);
        if (monthFilter) monthFilter.addEventListener('change', filterTransactions);
        if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearFilters);
        if (prevPageBtn) prevPageBtn.addEventListener('click', prevPage);
        if (nextPageBtn) nextPageBtn.addEventListener('click', nextPage);
        if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', deleteTransaction);

        // Close modal on escape
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && deleteModal && deleteModal.style.display === 'flex') {
                closeDeleteModal();
            }
        });

        // Close modal on click outside
        if (deleteModal) {
            deleteModal.addEventListener('click', function (e) {
                if (e.target === deleteModal) {
                    closeDeleteModal();
                }
            });
        }
    }

    // ===== Set current month in filter =====
    function setCurrentMonthFilter() {
        if (monthFilter) {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            monthFilter.value = `${year}-${month}`;
        }
    }

    // ===== Initialize =====
    async function init() {
        setupEventListeners();
        await loadTransactions();
        // setCurrentMonthFilter(); // Uncomment to set current month filter by default
    }

    // Export to global scope
    window.closeDeleteModal = closeDeleteModal;
    window.deleteTransaction = deleteTransaction;
    window.editTransaction = editTransaction;
    window.confirmDelete = confirmDelete;
    window.goToAddTransaction = goToAddTransaction;

    // Translations
    window.translations = {
        noTransactions: 'Nenhuma transação encontrada',
        addTransactionHint: 'Adicione sua primeira transação',
        page: 'Página',
        of: 'de'
    };

    // Start
    init();
})();