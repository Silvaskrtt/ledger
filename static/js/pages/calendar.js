(function () {
    const MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const TYPE_MAP = {
        "Despesa": "expense",
        "Receita": "income",
        "Economia": "saving",
    };
    const TYPE_MAP_REVERSE = {
        "expense": "Despesa",
        "income": "Receita",
        "saving": "Economia",
    };
    const TYPE_ICONS = {
        "expense": "expense",
        "income": "income",
        "saving": "primary",
    };

    const API_BASE = '/calendar/api/transactions/';

    const state = {
        today: new Date(),
        year: new Date().getFullYear(),
        month: new Date().getMonth(),
        txType: 'Despesa',
        summary: null,
        transactions: [],
        currentDay: null,
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
        // Transactions list modal
        transactionsModal: document.getElementById('transactionsModal'),
        closeTransactionsModal: document.getElementById('closeTransactionsModal'),
        closeTransactionsModalBtn: document.getElementById('closeTransactionsModalBtn'),
        addTransactionFromModal: document.getElementById('addTransactionFromModal'),
        transactionsDayLabel: document.getElementById('transactionsDayLabel'),
        transactionsList: document.getElementById('transactionsList'),
        // Edit elements
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
            const item = dailyMap.get(day) || { income: 0, expense: 0, saving: 0 };
            balance += item.income - item.expense + item.saving;
            rows.push({
                day,
                income: item.income,
                expense: item.expense,
                saving: item.saving,
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
            { label: 'Total Saídas', value: fmt(summary.total_expense), tone: 'expense' },
            { label: 'Total Economias', value: fmt(summary.total_saving), tone: 'primary' },
            { label: 'Saldo Mensal', value: fmt(summary.total_income - summary.total_expense + summary.total_saving), tone: (summary.total_income - summary.total_expense + summary.total_saving >= 0 ? 'primary' : 'expense') },
        ];

        elements.stats.innerHTML = stats.map((stat) => `
            <div class="stat">
                <div class="stat-icon ${stat.tone}">${stat.label.includes('Entradas') ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>' : stat.label.includes('Saídas') ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></svg>' : '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12V8a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4"/><path d="M22 12h-6a2 2 0 0 0 0 4h6"/></svg>'}</div>
                <div style="min-width: 0; width: 100%;">
                    <p class="stat-label">${stat.label}</p>
                    <p class="stat-value">${stat.value}</p>
                </div>
            </div>
        `).join('');
    }

    function renderTable(rows) {
        if (!rows.length) {
            elements.tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum dado disponível para este mês.</td></tr>';
            return;
        }

        elements.tbody.innerHTML = rows.map((row) => {
            const date = new Date(state.year, state.month, row.day);
            const isToday = row.day === state.today.getDate() && state.month === state.today.getMonth() && state.year === state.today.getFullYear();
            const isWeekend = date.getDay() === 0 || date.getDay() === 6;
            const badgeCls = isToday ? 'today' : (isWeekend ? 'weekend' : '');

            // Check if there are transactions for this day
            const dayTransactions = state.transactions.filter(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === row.day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year;
            });

            const hasExpenses = dayTransactions.some(tx => tx.type === 'expense');
            const expenseClick = hasExpenses ? `style="cursor:pointer;" data-day="${row.day}"` : '';

            // Get resumo display for this day (Diário column)
            let resumoDisplay = '—';
            if (window.ResumoModal && ResumoModal.getResumoDisplay) {
                const display = ResumoModal.getResumoDisplay(row.day);
                if (display) resumoDisplay = display;
            }

            return `
                <tr>
                    <td><span class="day-badge ${badgeCls}">${String(row.day).padStart(2, '0')}</span></td>
                    <td class="${row.income > 0 ? 'pos' : 'dash'}">${row.income > 0 ? fmt(row.income) : '—'}</td>
                    <td class="${row.expense > 0 ? 'neg' : 'dash'} expense-cell" ${expenseClick}>${row.expense > 0 ? fmt(row.expense) : '—'}</td>
                    <td class="daily-cell dash" data-day="${row.day}" style="cursor:pointer;">${resumoDisplay}</td>
                    <td class="dash">${row.saving > 0 ? fmt(row.saving) : '—'}</td>
                    <td class="dash">—</td>
                    <td><span class="${balanceClass(row.balance)}">${fmt(row.balance)}</span></td>
                </tr>
            `;
        }).join('');
    }

    async function fetchSummary(year, month) {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}monthly-summary/?year=${year}&month=${month + 1}`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Falha ao carregar o resumo');
            state.summary = data.summary;
            return data.summary;
        } finally {
            setLoading(false);
        }
    }

    async function fetchTransactions(year, month) {
        const response = await fetch(`${API_BASE}filter/?year=${year}&month=${month + 1}`);
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
            renderTable(rows);
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Erro ao atualizar calendário', 'error');
        }
    }

    function openDrawer() {
        elements.drawer.hidden = false;
        const defaultDate = new Date(state.year, state.month, state.today.getDate());
        elements.txDate.value = formatLocalDateInput(defaultDate);
    }

    function closeDrawer() {
        elements.drawer.hidden = true;
    }

    function resetForm() {
        elements.txValue.value = '';
        elements.txCategory.value = 'food';
        elements.txDescription.value = '';
        elements.txTag.value = 'none';
        elements.txRepeat.value = 'none';
        state.txType = 'Despesa';
        elements.txTypeButtons.forEach((button) => {
            button.classList.toggle('active', button.dataset.type === state.txType);
        });
    }

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

        const payload = {
            type: TYPE_MAP[state.txType],
            amount,
            date,
            category: elements.txCategory.value,
            description: elements.txDescription.value || 'Sem descrição',
            tag: elements.txTag.value === 'none' ? '' : elements.txTag.value,
            recurrence: elements.txRepeat.value,
        };

        try {
            const response = await window.fetchWithCSRF(`${API_BASE}create/`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!data.success) {
                const errorMsg = data.error || Object.values(data.errors || {}).flat().join(' ') || 'Erro ao salvar transação';
                throw new Error(errorMsg);
            }

            window.showToast('Transação salva com sucesso.');
            closeDrawer();
            resetForm();
            const createdDate = parseLocalDate(payload.date);
            if (createdDate.getFullYear() === state.year && createdDate.getMonth() === state.month) {
                await refresh();
                // Close transactions modal if open
                closeTransactionsModal();
            }
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível salvar a transação', 'error');
        }
    }

    // Transactions List Modal functions
    function openTransactionsModal(day) {
        state.currentDay = day;
        elements.transactionsModal.hidden = false;
        elements.transactionsDayLabel.textContent = `${String(day).padStart(2, '0')}/${String(state.month + 1).padStart(2, '0')}/${state.year}`;
        renderTransactionsList(day);
    }

    function closeTransactionsModal() {
        elements.transactionsModal.hidden = true;
        state.currentDay = null;
    }

    function renderTransactionsList(day) {
        const dayTransactions = state.transactions.filter(tx => {
            const txDate = parseLocalDate(tx.date);
            return txDate.getDate() === day &&
                txDate.getMonth() === state.month &&
                txDate.getFullYear() === state.year;
        });

        if (dayTransactions.length === 0) {
            elements.transactionsList.innerHTML = `
                <div class="empty-transactions">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                    <p>Nenhuma transação neste dia</p>
                </div>
            `;
            return;
        }

        elements.transactionsList.innerHTML = dayTransactions.map(tx => {
            const typeLabel = TYPE_MAP_REVERSE[tx.type] || tx.type;
            const amountClass = tx.type === 'income' ? 'income' : (tx.type === 'expense' ? 'expense' : 'saving');
            const sign = tx.type === 'expense' ? '-' : '+';

            return `
                <div class="transaction-item" data-id="${tx.id}">
                    <div class="tx-info">
                        <span class="tx-desc">${tx.description || 'Sem descrição'}</span>
                        <span class="tx-meta">${typeLabel} • ${tx.category} ${tx.tag ? '• #' + tx.tag : ''}</span>
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

        // Add event listeners to edit and delete buttons
        elements.transactionsList.querySelectorAll('.edit-tx-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                const transaction = state.transactions.find(tx => tx.id === id);
                if (transaction) {
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

    // Edit functions
    function openEditDrawer(transaction) {
        elements.editDrawer.hidden = false;

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
            category: elements.editTxCategory.value,
            description: elements.editTxDescription.value || 'Sem descrição',
            tag: elements.editTxTag.value === 'none' ? '' : elements.editTxTag.value,
            recurrence: elements.editTxRepeat.value,
        };

        try {
            const response = await window.fetchWithCSRF(`${API_BASE}${id}/update/`, {
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
            if (state.currentDay) {
                renderTransactionsList(state.currentDay);
            }
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível atualizar a transação', 'error');
        }
    }

    async function deleteTransactionById(id) {
        try {
            const response = await window.fetchWithCSRF(`${API_BASE}${id}/delete/`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Erro ao excluir transação');
            }

            window.showToast('Transação excluída com sucesso.');
            await refresh();
            if (state.currentDay) {
                renderTransactionsList(state.currentDay);
            }
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível excluir a transação', 'error');
        }
    }

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
            });
        });

        elements.txForm.addEventListener('submit', submitTransaction);

        // Transactions Modal events
        elements.closeTransactionsModal.addEventListener('click', closeTransactionsModal);
        elements.closeTransactionsModalBtn.addEventListener('click', closeTransactionsModal);
        elements.transactionsModal.addEventListener('click', (event) => {
            if (event.target === elements.transactionsModal) {
                closeTransactionsModal();
            }
        });
        elements.addTransactionFromModal.addEventListener('click', () => {
            closeTransactionsModal();
            openDrawer();
        });

        // Edit form events
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

        // Click on Diário column - opens Resumo Modal
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.daily-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;
            if (window.ResumoModal && ResumoModal.open) {
                ResumoModal.open(day);
            }
        });

        // Click on Saídas column - opens Transactions List Modal
        elements.tbody.addEventListener('click', (ev) => {
            const td = ev.target.closest('td.expense-cell');
            if (!td) return;
            const day = Number(td.dataset.day);
            if (!day) return;

            // Check if there are expense transactions for this day
            const hasExpenses = state.transactions.some(tx => {
                const txDate = parseLocalDate(tx.date);
                return txDate.getDate() === day &&
                    txDate.getMonth() === state.month &&
                    txDate.getFullYear() === state.year &&
                    tx.type === 'expense';
            });

            if (hasExpenses) {
                openTransactionsModal(day);
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
            }
        });
    }

    if (window.ResumoModal && ResumoModal.init) {
        ResumoModal.init({
            getState: () => state,
            onSaved: (day, total) => {
                refresh();
            }
        });
    }

    attachEvents();
    resetForm();
    refresh();
})();