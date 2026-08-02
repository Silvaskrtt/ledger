(function () {
    const MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const TYPE_MAP = {
        "Despesa": "expense",
        "Receita": "income",
        "Economia": "saving",
        "Cartão": "card",
    };
    const TYPE_MAP_REVERSE = {
        "expense": "Despesa",
        "income": "Receita",
        "saving": "Economia",
        "card": "Cartão",
    };

    const API_BASE = '/calendar/api/';

    const state = {
        today: new Date(),
        year: new Date().getFullYear(),
        month: new Date().getMonth(),
        txType: 'Despesa',
        summary: null,
        transactions: [],
        currentDay: null,
        currentType: null,
        categories: [], // Lista de categorias do usuário
    };

    const elements = {
        monthLabel: document.getElementById('monthLabel'),
        daysLabel: document.getElementById('daysLabel'),
        stats: document.getElementById('stats'),
        tbody: document.getElementById('tbody'),
        drawer: document.getElementById('drawer'),
        openDrawer: document.getElementById('openDrawer'),
        closeDrawer: document.getElementById('closeDrawer'),
        cancelDrawer: document.getElementById('cancelDrawer'),
        txForm: document.getElementById('txForm'),
        txTypeButtons: document.querySelectorAll('#txForm .type-btn'),
        txValue: document.getElementById('txValue'),
        txDate: document.getElementById('txDate'),
        txCategory: document.getElementById('txCategory'),
        txDescription: document.getElementById('txDescription'),
        txTag: document.getElementById('txTag'),
        txRepeat: document.getElementById('txRepeat'),
        openResumo: document.getElementById('openResumo'),
        transactionsModal: document.getElementById('transactionsModal'),
        closeTransactionsModal: document.getElementById('closeTransactionsModal'),
        closeTransactionsModalBtn: document.getElementById('closeTransactionsModalBtn'),
        addTransactionFromModal: document.getElementById('addTransactionFromModal'),
        transactionsDayLabel: document.getElementById('transactionsDayLabel'),
        transactionsList: document.getElementById('transactionsList'),
        editDrawer: document.getElementById('editDrawer'),
        closeEditDrawer: document.getElementById('closeEditDrawer'),
        cancelEditDrawer: document.getElementById('cancelEditDrawer'),
        deleteEditTx: document.getElementById('deleteEditTx'),
        editTxForm: document.getElementById('editTxForm'),
        editTxId: document.getElementById('editTxId'),
        editTxTypeButtons: document.querySelectorAll('#editTxForm .type-btn'),
        editTxValue: document.getElementById('editTxValue'),
        editTxDate: document.getElementById('editTxDate'),
        editTxCategory: document.getElementById('editTxCategory'),
        editTxDescription: document.getElementById('editTxDescription'),
        editTxTag: document.getElementById('editTxTag'),
        editTxRepeat: document.getElementById('editTxRepeat'),
    };

    const daysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
    const fmt = (value) => `R$ ${Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    function parseLocalDate(dateString) {
        const [year, month, day] = dateString.split('-').map(Number);
        return new Date(year, month - 1, day);
    }

    function formatLocalDateInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function setLoading(isLoading) {
        if (isLoading) {
            elements.stats.classList.add('loading');
        } else {
            elements.stats.classList.remove('loading');
        }
    }

    function getDailyMap(days) {
        const map = new Map();
        days.forEach((item) => {
            const date = parseLocalDate(item.date);
            const day = date.getDate();
            map.set(day, item);
        });
        return map;
    }

    function buildMonthlyRows(summary) {
        const totalDays = daysInMonth(state.year, state.month);
        const dailyMap = getDailyMap(summary.days);
        const rows = [];
        let balance = Number(summary.opening_balance || 0);

        for (let day = 1; day <= totalDays; day++) {
            const item = dailyMap.get(day) || { income: 0, expense: 0, saving: 0, card: 0 };
            balance += item.income - item.expense - item.card + item.saving;
            rows.push({
                day,
                income: item.income,
                expense: item.expense,
                saving: item.saving,
                card: item.card,
                balance,
            });
        }

        return rows;
    }

    function balanceClass(value) {
        if (value < 0) return 'balance-neg';
        if (value >= 2000) return 'balance-high';
        if (value >= 1000) return 'balance-mid';
        return 'balance-low';
    }

    function renderHeader() {
        elements.monthLabel.textContent = `${MONTHS[state.month]} ${state.year}`;
        elements.daysLabel.textContent = `${daysInMonth(state.year, state.month)} dias no mês`;
    }

    function renderStats(summary) {
        const stats = [
            { label: 'Total Entradas', value: fmt(summary.total_income), tone: 'income' },
            { label: 'Total Saídas (Débito)', value: fmt(summary.total_expense), tone: 'expense' },
            { label: 'Total Cartão', value: fmt(summary.total_card), tone: 'expense' },
            { label: 'Total Economias', value: fmt(summary.total_saving), tone: 'primary' },
            { label: 'Saldo Mensal', value: fmt(summary.total_income - summary.total_expense - summary.total_card + summary.total_saving), tone: (summary.total_income - summary.total_expense - summary.total_card + summary.total_saving >= 0 ? 'primary' : 'expense') },
        ];

        elements.stats.innerHTML = stats.map((stat) => `
            <div class="stat">
                <div class="stat-icon ${stat.tone}">${stat.label.includes('Entradas') ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>' : stat.label.includes('Saídas') ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></svg>' : stat.label.includes('Cartão') ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>' : '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12V8a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4"/><path d="M22 12h-6a2 2 0 0 0 0 4h6"/></svg>'}</div>
                <div style="min-width: 0; width: 100%;">
                    <p class="stat-label">${stat.label}</p>
                    <p class="stat-value">${stat.value}</p>
                </div>
            </div>
        `).join('');
    }

    async function loadCategories() {
        try {
            const response = await fetch(`${API_BASE}categories/`);
            const data = await response.json();
            if (data.success) {
                state.categories = data.categories;
                return state.categories;
            }
            return [];
        } catch (error) {
            console.error('Erro ao carregar categorias:', error);
            return [];
        }
    }

    function populateCategorySelect(selectElement) {
        // Limpa o select
        selectElement.innerHTML = '';

        // Agrupa categorias por tipo
        const expenseCategories = state.categories.filter(c => c.type === 'expense');
        const incomeCategories = state.categories.filter(c => c.type === 'income');

        // Adiciona categorias de despesa
        if (expenseCategories.length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = 'Despesas';
            expenseCategories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = `${cat.icon || '📌'} ${cat.name}`;
                optgroup.appendChild(option);
            });
            selectElement.appendChild(optgroup);
        }

        // Adiciona categorias de receita
        if (incomeCategories.length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = 'Receitas';
            incomeCategories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = `${cat.icon || '💰'} ${cat.name}`;
                optgroup.appendChild(option);
            });
            selectElement.appendChild(optgroup);
        }

        // Se não houver categorias, adiciona opções padrão
        if (state.categories.length === 0) {
            const defaultOptions = [
                { value: 'Alimentação', label: '🍔 Alimentação' },
                { value: 'Moradia', label: '🏠 Moradia' },
                { value: 'Transporte', label: '🚗 Transporte' },
                { value: 'Lazer', label: '🎮 Lazer' },
                { value: 'Educação', label: '📚 Educação' },
                { value: 'Saúde', label: '🏥 Saúde' },
                { value: 'Salário', label: '💰 Salário' },
            ];
            defaultOptions.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.label;
                selectElement.appendChild(option);
            });
        }
    }

    function updateCategorySelects() {
        populateCategorySelect(elements.txCategory);
        populateCategorySelect(elements.editTxCategory);
    }

    async function renderTable(rows) {
        if (!rows.length) {
            elements.tbody.innerHTML = '<tr><td colspan="8" class="text-center">Nenhum dado disponível para este mês.</td></tr>';
            return;
        }

        let dailyGoal = 0;
        try {
            const response = await fetch(`${API_BASE}budget/?year=${state.year}&month=${state.month + 1}`);
            const data = await response.json();
            if (data.success && data.budget) {
                dailyGoal = data.budget.daily_goal || 0;
            }
        } catch (e) {
            console.error('Erro ao buscar planejamento:', e);
        }

        elements.tbody.innerHTML = rows.map((row) => {
            const date = new Date(state.year, state.month, row.day);
            const isToday = row.day === state.today.getDate() && state.month === state.today.getMonth() && state.year === state.today.getFullYear();
            const isWeekend = date.getDay() === 0 || date.getDay() === 6;
            const badgeCls = isToday ? 'today' : (isWeekend ? 'weekend' : '');

            const dayTransactions = state.transactions.filter(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === row.day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year;
            });

            let diarioDisplay = '—';
            if (dailyGoal > 0) {
                diarioDisplay = fmt(dailyGoal);
            }

            const dateStr = `${state.year}-${String(state.month + 1).padStart(2, '0')}-${String(row.day).padStart(2, '0')}`;

            return `
                <tr>
                    <td><span class="day-badge ${badgeCls}">${String(row.day).padStart(2, '0')}</span></td>
                    <td class="${row.income > 0 ? 'pos' : 'dash'} income-cell" data-day="${row.day}" data-date="${dateStr}" style="cursor:pointer;">${row.income > 0 ? fmt(row.income) : '—'}</td>
                    <td class="${row.expense > 0 ? 'neg' : 'dash'} expense-cell" data-day="${row.day}" data-date="${dateStr}" style="cursor:pointer;">${row.expense > 0 ? fmt(row.expense) : '—'}</td>
                    <td class="daily-cell dash" data-day="${row.day}" style="cursor:pointer;">${diarioDisplay}</td>
                    <td class="${row.saving > 0 ? 'pos' : 'dash'} saving-cell" data-day="${row.day}" data-date="${dateStr}" style="cursor:pointer;">${row.saving > 0 ? fmt(row.saving) : '—'}</td>
                    <td class="${row.card > 0 ? 'neg' : 'dash'} card-cell" data-day="${row.day}" data-date="${dateStr}" style="cursor:pointer;">${row.card > 0 ? fmt(row.card) : '—'}</td>
                    <td><span class="${balanceClass(row.balance)}">${fmt(row.balance)}</span></td>
                </tr>
            `;
        }).join('');
    }

    async function fetchSummary(year, month) {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}transactions/monthly-summary/?year=${year}&month=${month + 1}`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Falha ao carregar o resumo');
            state.summary = data.summary;
            return data.summary;
        } finally {
            setLoading(false);
        }
    }

    async function fetchTransactions(year, month) {
        const response = await fetch(`${API_BASE}transactions/filter/?year=${year}&month=${month + 1}`);
        const data = await response.json();
        if (!data.success) throw new Error(data.error || 'Falha ao carregar transações');
        state.transactions = data.transactions;
        return data.transactions;
    }

    async function refresh() {
        renderHeader();

        try {
            const [summary] = await Promise.all([
                fetchSummary(state.year, state.month),
                fetchTransactions(state.year, state.month),
            ]);
            const rows = buildMonthlyRows(summary);
            renderStats(summary);
            await renderTable(rows);
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Erro ao atualizar calendário', 'error');
        }
    }

    function openDrawerWithDate(dateStr, type) {
        elements.drawer.hidden = false;
        elements.txDate.value = dateStr;
        updateCategorySelects();

        if (type) {
            state.txType = type;
            elements.txTypeButtons.forEach((button) => {
                button.classList.toggle('active', button.dataset.type === type);
            });
        }
    }

    function openDrawer() {
        const defaultDate = new Date(state.year, state.month, state.today.getDate());
        elements.txDate.value = formatLocalDateInput(defaultDate);
        updateCategorySelects();
        elements.drawer.hidden = false;
    }

    function closeDrawer() {
        elements.drawer.hidden = true;
    }

    function resetForm() {
        elements.txValue.value = '';
        elements.txDescription.value = '';
        elements.txTag.value = 'none';
        elements.txRepeat.value = 'none';
        state.txType = 'Despesa';
        elements.txTypeButtons.forEach((button) => {
            button.classList.toggle('active', button.dataset.type === state.txType);
        });
        updateCategorySelects();
    }

    // ============ FUNÇÃO DE REPETIÇÃO ============
    function generateRecurringDates(startDate, recurrence, count = 12) {
        const dates = [];
        const current = new Date(startDate);

        for (let i = 0; i < count; i++) {
            if (i === 0) {
                dates.push(new Date(current));
            } else {
                const next = new Date(current);
                if (recurrence === 'weekly') {
                    next.setDate(next.getDate() + (7 * i));
                } else if (recurrence === 'monthly') {
                    next.setMonth(next.getMonth() + i);
                } else if (recurrence === 'yearly') {
                    next.setFullYear(next.getFullYear() + i);
                }
                dates.push(new Date(next));
            }
        }
        return dates;
    }

    async function saveRecurringTransactions(payload, count = 12) {
        const dates = generateRecurringDates(
            parseLocalDate(payload.date),
            payload.recurrence,
            count
        );

        const results = [];
        for (const date of dates) {
            const txPayload = {
                ...payload,
                date: formatLocalDateInput(date),
                recurrence: 'none'
            };

            try {
                const response = await window.fetchWithCSRF(`${API_BASE}transactions/create/`, {
                    method: 'POST',
                    body: JSON.stringify(txPayload),
                });
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Erro ao criar transação recorrente');
                }
                results.push(data.transaction);
            } catch (error) {
                console.error('Erro ao criar transação recorrente:', error);
                throw error;
            }
        }
        return results;
    }

    // ============ FUNÇÕES PRINCIPAIS ============
    async function submitTransaction(event) {
        event.preventDefault();

        const amount = parseFloat(elements.txValue.value);
        if (!amount || amount <= 0) {
            window.showToast('Informe um valor válido.', 'error');
            return;
        }

        const date = elements.txDate.value;
        if (!date) {
            window.showToast('Informe a data da transação.', 'error');
            return;
        }

        const category = elements.txCategory.value;
        if (!category) {
            window.showToast('Selecione uma categoria.', 'error');
            return;
        }

        const recurrence = elements.txRepeat.value;
        const payload = {
            type: TYPE_MAP[state.txType],
            amount,
            date,
            category: category,
            description: elements.txDescription.value || 'Sem descrição',
            tag: elements.txTag.value === 'none' ? '' : elements.txTag.value,
            recurrence: recurrence,
        };

        try {
            if (recurrence !== 'none') {
                await saveRecurringTransactions(payload, 12);
                window.showToast('Transações recorrentes criadas com sucesso.');
            } else {
                const response = await window.fetchWithCSRF(`${API_BASE}transactions/create/`, {
                    method: 'POST',
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (!data.success) {
                    const errorMsg = data.error || Object.values(data.errors || {}).flat().join(' ') || 'Erro ao salvar transação';
                    throw new Error(errorMsg);
                }
                window.showToast('Transação salva com sucesso.');
            }

            closeDrawer();
            resetForm();
            await refresh();
            closeTransactionsModal();
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível salvar a transação', 'error');
        }
    }

    function openTransactionsModal(day, type) {
        state.currentDay = day;
        state.currentType = type || 'all';
        elements.transactionsModal.hidden = false;
        elements.transactionsDayLabel.textContent = `${String(day).padStart(2, '0')}/${String(state.month + 1).padStart(2, '0')}/${state.year}`;
        renderTransactionsList(day, type);
    }

    function closeTransactionsModal() {
        elements.transactionsModal.hidden = true;
        state.currentDay = null;
        state.currentType = null;
    }

    function renderTransactionsList(day, filterType) {
        const dayTransactions = state.transactions.filter(tx => {
            const txDate = parseLocalDate(tx.date);
            const matchDay = txDate.getDate() === day &&
                txDate.getMonth() === state.month &&
                txDate.getFullYear() === state.year;

            if (filterType && filterType !== 'all') {
                return matchDay && tx.type === filterType;
            }
            return matchDay;
        });

        if (dayTransactions.length === 0) {
            elements.transactionsList.innerHTML = `
                <div class="empty-transactions">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                    <p>Nenhuma transação neste dia</p>
                    <button class="btn-primary" style="margin-top:12px;padding:8px 16px;font-size:13px;" onclick="window.addTransactionForDay(${day})">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                        Adicionar
                    </button>
                </div>
            `;
            return;
        }

        elements.transactionsList.innerHTML = dayTransactions.map(tx => {
            const typeLabel = TYPE_MAP_REVERSE[tx.type] || tx.type;
            const amountClass = tx.type === 'income' ? 'income' : (tx.type === 'expense' ? 'expense' : (tx.type === 'card' ? 'expense' : 'saving'));
            const sign = tx.type === 'expense' || tx.type === 'card' ? '-' : '+';
            const recurrenceBadge = tx.recurrence && tx.recurrence !== 'none' ?
                `<span class="recurrence-badge">🔄 ${tx.recurrence}</span>` : '';

            // Busca o ícone da categoria
            const categoryObj = state.categories.find(c => c.name === tx.category);
            const categoryIcon = categoryObj ? categoryObj.icon : '📌';

            return `
                <div class="transaction-item" data-id="${tx.id}">
                    <div class="tx-info">
                        <span class="tx-desc">${categoryIcon} ${tx.description || 'Sem descrição'}</span>
                        <span class="tx-meta">${typeLabel} • ${tx.category} ${tx.tag ? '• #' + tx.tag : ''} ${recurrenceBadge}</span>
                    </div>
                    <span class="tx-amount ${amountClass}">${sign} ${fmt(tx.amount)}</span>
                    <div class="tx-actions">
                        <button class="edit-tx-btn" data-id="${tx.id}" title="Editar">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        </button>
                        <button class="delete-tx-btn" data-id="${tx.id}" title="Excluir">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        elements.transactionsList.querySelectorAll('.edit-tx-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                const transaction = state.transactions.find(tx => tx.id === id);
                if (transaction) {
                    closeTransactionsModal();
                    openEditDrawer(transaction);
                }
            });
        });

        elements.transactionsList.querySelectorAll('.delete-tx-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                if (confirm('Tem certeza que deseja excluir esta transação?')) {
                    await deleteTransactionById(id);
                }
            });
        });
    }

    function openEditDrawer(transaction) {
        elements.editDrawer.hidden = false;
        updateCategorySelects();

        elements.editTxId.value = transaction.id;
        elements.editTxValue.value = transaction.amount;
        elements.editTxDate.value = transaction.date;
        elements.editTxCategory.value = transaction.category;
        elements.editTxDescription.value = transaction.description || '';
        elements.editTxTag.value = transaction.tag || 'none';
        elements.editTxRepeat.value = transaction.recurrence || 'none';

        const typeLabel = TYPE_MAP_REVERSE[transaction.type] || 'Despesa';
        elements.editTxTypeButtons.forEach((button) => {
            button.classList.toggle('active', button.dataset.type === typeLabel);
        });
    }

    function closeEditDrawer() {
        elements.editDrawer.hidden = true;
    }

    async function submitEditTransaction(event) {
        event.preventDefault();

        const id = parseInt(elements.editTxId.value);
        if (!id) {
            window.showToast('ID da transação não encontrado.', 'error');
            return;
        }

        const amount = parseFloat(elements.editTxValue.value);
        if (!amount || amount <= 0) {
            window.showToast('Informe um valor válido.', 'error');
            return;
        }

        const date = elements.editTxDate.value;
        if (!date) {
            window.showToast('Informe a data da transação.', 'error');
            return;
        }

        const category = elements.editTxCategory.value;
        if (!category) {
            window.showToast('Selecione uma categoria.', 'error');
            return;
        }

        let activeType = 'Despesa';
        elements.editTxTypeButtons.forEach((btn) => {
            if (btn.classList.contains('active')) {
                activeType = btn.dataset.type;
            }
        });

        const payload = {
            type: TYPE_MAP[activeType],
            amount,
            date,
            category: category,
            description: elements.editTxDescription.value || 'Sem descrição',
            tag: elements.editTxTag.value === 'none' ? '' : elements.editTxTag.value,
            recurrence: elements.editTxRepeat.value,
        };

        try {
            const response = await window.fetchWithCSRF(`${API_BASE}transactions/${id}/update/`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!data.success) {
                const errorMsg = data.error || Object.values(data.errors || {}).flat().join(' ') || 'Erro ao atualizar transação';
                throw new Error(errorMsg);
            }

            window.showToast('Transação atualizada com sucesso.');
            closeEditDrawer();
            await refresh();
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível atualizar a transação', 'error');
        }
    }

    async function deleteTransactionById(id) {
        try {
            const response = await window.fetchWithCSRF(`${API_BASE}transactions/${id}/delete/`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Erro ao excluir transação');
            }

            window.showToast('Transação excluída com sucesso.');
            await refresh();
            if (state.currentDay) {
                renderTransactionsList(state.currentDay, state.currentType);
            }
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível excluir a transação', 'error');
        }
    }

    window.addTransactionForDay = function (day) {
        const dateStr = `${state.year}-${String(state.month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        closeTransactionsModal();
        openDrawerWithDate(dateStr, 'Despesa');
    };

    function attachEvents() {
        document.getElementById('prevMonth').addEventListener('click', () => {
            if (state.month === 0) {
                state.month = 11;
                state.year -= 1;
            } else {
                state.month -= 1;
            }
            refresh();
        });

        document.getElementById('nextMonth').addEventListener('click', () => {
            if (state.month === 11) {
                state.month = 0;
                state.year += 1;
            } else {
                state.month += 1;
            }
            refresh();
        });

        elements.openDrawer.addEventListener('click', openDrawer);
        elements.closeDrawer.addEventListener('click', closeDrawer);
        elements.cancelDrawer.addEventListener('click', closeDrawer);
        elements.drawer.addEventListener('click', (event) => {
            if (event.target === elements.drawer) {
                closeDrawer();
            }
        });

        elements.txTypeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                state.txType = button.dataset.type;
                elements.txTypeButtons.forEach((btn) => btn.classList.toggle('active', btn === button));
                updateCategorySelects();
            });
        });

        elements.txForm.addEventListener('submit', submitTransaction);

        elements.closeTransactionsModal.addEventListener('click', closeTransactionsModal);
        elements.closeTransactionsModalBtn.addEventListener('click', closeTransactionsModal);
        elements.transactionsModal.addEventListener('click', (event) => {
            if (event.target === elements.transactionsModal) {
                closeTransactionsModal();
            }
        });
        elements.addTransactionFromModal.addEventListener('click', () => {
            if (state.currentDay) {
                window.addTransactionForDay(state.currentDay);
            } else {
                closeTransactionsModal();
                openDrawer();
            }
        });

        elements.closeEditDrawer.addEventListener('click', closeEditDrawer);
        elements.cancelEditDrawer.addEventListener('click', closeEditDrawer);
        elements.editDrawer.addEventListener('click', (event) => {
            if (event.target === elements.editDrawer) {
                closeEditDrawer();
            }
        });

        elements.editTxTypeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                elements.editTxTypeButtons.forEach((btn) => btn.classList.toggle('active', btn === button));
                updateCategorySelects();
            });
        });

        elements.editTxForm.addEventListener('submit', submitEditTransaction);
        elements.deleteEditTx.addEventListener('click', async () => {
            const id = parseInt(elements.editTxId.value);
            if (!id) return;
            if (confirm('Tem certeza que deseja excluir esta transação?')) {
                await deleteTransactionById(id);
                closeEditDrawer();
            }
        });

        // Click on Diário column
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.daily-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;
            if (window.ResumoModal && ResumoModal.open) {
                ResumoModal.open(day);
            }
        });

        // Click on Entradas column
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.income-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;

            const hasIncome = state.transactions.some(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year &&
                    tx.type === 'income';
            });

            if (hasIncome) {
                openTransactionsModal(day, 'income');
            } else {
                const dateStr = td.dataset.date;
                openDrawerWithDate(dateStr, 'Receita');
            }
        });

        // Click on Saídas column
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.expense-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;

            const hasExpense = state.transactions.some(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year &&
                    tx.type === 'expense';
            });

            if (hasExpense) {
                openTransactionsModal(day, 'expense');
            } else {
                const dateStr = td.dataset.date;
                openDrawerWithDate(dateStr, 'Despesa');
            }
        });

        // Click on Cartão column
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.card-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;

            const hasCard = state.transactions.some(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year &&
                    tx.type === 'card';
            });

            if (hasCard) {
                openTransactionsModal(day, 'card');
            } else {
                const dateStr = td.dataset.date;
                openDrawerWithDate(dateStr, 'Cartão');
            }
        });

        // Click on Economias column
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.saving-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;

            const hasSaving = state.transactions.some(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year &&
                    tx.type === 'saving';
            });

            if (hasSaving) {
                openTransactionsModal(day, 'saving');
            } else {
                const dateStr = td.dataset.date;
                openDrawerWithDate(dateStr, 'Economia');
            }
        });

        if (elements.openResumo) {
            elements.openResumo.addEventListener('click', () => {
                if (window.ResumoModal && ResumoModal.open) {
                    ResumoModal.open(state.today.getDate());
                }
            });
        }

        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape') {
                if (!elements.transactionsModal.hidden) closeTransactionsModal();
                if (!elements.editDrawer.hidden) closeEditDrawer();
                if (!elements.drawer.hidden) closeDrawer();
            }
        });
    }

    // ============ INICIALIZAÇÃO ============
    async function init() {
        // Carrega categorias primeiro
        await loadCategories();
        updateCategorySelects();

        // Inicializa ResumoModal
        if (window.ResumoModal && ResumoModal.init) {
            ResumoModal.init({
                getState: () => state,
                onSaved: (day) => {
                    refresh();
                }
            });
        }

        attachEvents();
        resetForm();
        refresh();
    }

    init();
})();