(function () {
    const MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const TYPE_MAP = {
        "Despesa": "expense",
        "Receita": "income",
        "Economia": "saving",
    };

    const API_BASE = '/calendar/api/transactions/';

    const state = {
        today: new Date(),
        year: new Date().getFullYear(),
        month: new Date().getMonth(),
        txType: 'Despesa',
        summary: null,
        transactions: [],
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
        txTypeButtons: document.querySelectorAll('.type-btn'),
        txValue: document.getElementById('txValue'),
        txDate: document.getElementById('txDate'),
        txCategory: document.getElementById('txCategory'),
        txDescription: document.getElementById('txDescription'),
        txTag: document.getElementById('txTag'),
        txRepeat: document.getElementById('txRepeat'),
    };

    const daysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
    const fmt = (value) => `R$ ${Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

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
            const date = new Date(item.date);
            const day = date.getDate();
            map.set(day, item);
        });
        return map;
    }

    function buildMonthlyRows(summary) {
        const totalDays = daysInMonth(state.year, state.month);
        const dailyMap = getDailyMap(summary.days);
        const rows = [];
        let balance = 0;

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

            return `
                <tr>
                    <td><span class="day-badge ${badgeCls}">${String(row.day).padStart(2, '0')}</span></td>
                    <td class="${row.income > 0 ? 'pos' : 'dash'}">${row.income > 0 ? fmt(row.income) : '—'}</td>
                    <td class="${row.expense > 0 ? 'neg' : 'dash'}">${row.expense > 0 ? fmt(row.expense) : '—'}</td>
                    <td class="dash">—</td>
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
        elements.txDate.value = defaultDate.toISOString().slice(0, 10);
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
            const createdDate = new Date(payload.date);
            if (createdDate.getFullYear() === state.year && createdDate.getMonth() === state.month) {
                await refresh();
            }
        } catch (error) {
            console.error(error);
            window.showToast(error.message || 'Não foi possível salvar a transação', 'error');
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
    }

    attachEvents();
    resetForm();
    refresh();
})();
