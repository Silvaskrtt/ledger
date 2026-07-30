(function () {
    const fmt = (value) => `R$ ${Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    const API_BASE = '/calendar/api/';

    let getState = null;
    let onSaved = null;
    let currentBudget = null;

    function getElements() {
        return {
            modal: document.getElementById('resumoModal'),
            close: document.getElementById('closeResumo'),
            cancel: document.getElementById('cancelResumo'),
            save: document.getElementById('saveResumo'),
            dayLabel: document.getElementById('resumoDayLabel'),
            totalMensal: document.getElementById('resumoTotalMensal'),
            divisor: document.getElementById('resumoDivisor'),
            totalDiario: document.getElementById('resumoTotalDiario'),
            categoriesWrap: document.getElementById('resumoCategories'),
            addExtra: document.getElementById('addExtraExpense'),
            extraWrap: document.getElementById('extraExpenses'),
        };
    }

    async function fetchBudget(year, month) {
        try {
            const response = await fetch(`${API_BASE}budget/?year=${year}&month=${month}`);
            const data = await response.json();
            if (data.success) {
                return data.budget;
            }
            return null;
        } catch (e) {
            console.error('Erro ao carregar planejamento:', e);
            return null;
        }
    }

    async function saveBudget(year, month, data) {
        try {
            const payload = {
                year: year,
                month: month,
                categories: data.categories,
                extras: data.extras,
                divisor: data.divisor
            };

            const response = await window.fetchWithCSRF(`${API_BASE}budget/save/`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            if (result.success) {
                return result.budget;
            }
            throw new Error(result.error || 'Erro ao salvar planejamento');
        } catch (e) {
            console.error('Erro ao salvar planejamento:', e);
            throw e;
        }
    }

    function createExtraRow(label = '', amount = '') {
        const wrapper = document.createElement('div');
        wrapper.className = 'extra-row';
        wrapper.innerHTML = `
            <input type="text" class="extra-label" placeholder="Descrição" value="${label}" />
            <div style="display:flex;gap:8px;align-items:center;">
                <input type="number" step="0.01" class="extra-amount" placeholder="0,00" value="${amount}" />
                <button type="button" class="ghost-btn remove-extra" style="padding:6px 12px;font-size:12px;">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
            </div>
        `;
        wrapper.querySelector('.remove-extra').addEventListener('click', () => wrapper.remove());
        return wrapper;
    }

    const ResumoModal = {
        init(opts = {}) {
            getState = opts.getState;
            onSaved = opts.onSaved;
            const el = getElements();
            if (!el.modal) {
                console.warn('Modal de resumo não encontrado');
                return;
            }

            el.addExtra && el.addExtra.addEventListener('click', () => {
                el.extraWrap.appendChild(createExtraRow());
            });

            el.close && el.close.addEventListener('click', () => ResumoModal.close());
            el.cancel && el.cancel.addEventListener('click', () => ResumoModal.close());
            el.save && el.save.addEventListener('click', () => ResumoModal.save());

            el.modal.addEventListener('click', (ev) => {
                if (ev.target === el.modal) ResumoModal.close();
            });
            document.addEventListener('keydown', (ev) => {
                if (ev.key === 'Escape' && el.modal && !el.modal.hidden) ResumoModal.close();
            });

            el.divisor && el.divisor.addEventListener('input', () => ResumoModal.updateComputed());
        },

        async getResumoDisplay(day) {
            const s = getState ? getState() : null;
            if (!s) return null;

            try {
                const budget = await fetchBudget(s.year, s.month + 1);
                if (budget && budget.daily_goal !== undefined) {
                    return fmt(budget.daily_goal);
                }
                return null;
            } catch (e) {
                console.error('Erro ao buscar planejamento:', e);
                return null;
            }
        },

        async open(day) {
            const s = getState ? getState() : null;
            if (!s) {
                console.warn('Estado não disponível');
                return;
            }
            const el = getElements();
            if (!el.modal) return;

            try {
                currentBudget = await fetchBudget(s.year, s.month + 1);
                if (!currentBudget) {
                    currentBudget = {
                        categories: {},
                        extras: [],
                        divisor: 30,
                        total_planned: 0,
                        daily_goal: 0
                    };
                }

                el.dayLabel.textContent = `${String(day).padStart(2, '0')}/${String(s.month + 1).padStart(2, '0')}/${s.year}`;
                el.totalMensal.textContent = fmt(Number(currentBudget.total_planned || 0));
                el.divisor.value = currentBudget.divisor || 30;
                el.totalDiario.textContent = fmt(currentBudget.daily_goal || 0);

                const inputs = el.categoriesWrap.querySelectorAll('.resumo-input');
                inputs.forEach((inp) => {
                    const name = inp.name;
                    inp.value = currentBudget.categories && currentBudget.categories[name] !== undefined ? currentBudget.categories[name] : '';
                });

                el.extraWrap.innerHTML = '';
                (currentBudget.extras || []).forEach((ex) => {
                    el.extraWrap.appendChild(createExtraRow(ex.label, ex.amount));
                });

                el.modal.dataset.editDay = String(day);
                el.modal.hidden = false;
            } catch (error) {
                console.error('Erro ao abrir modal:', error);
                window.showToast('Erro ao carregar planejamento', 'error');
            }
        },

        close() {
            const el = getElements();
            if (!el.modal) return;
            el.modal.hidden = true;
            delete el.modal.dataset.editDay;
            currentBudget = null;
        },

        async save() {
            const s = getState ? getState() : null;
            if (!s) return;
            const el = getElements();
            const day = Number(el.modal.dataset.editDay) || 1;

            const categories = {};
            el.categoriesWrap.querySelectorAll('.resumo-input').forEach((inp) => {
                const val = parseFloat(inp.value);
                categories[inp.name] = isNaN(val) ? 0 : val;
            });

            const extras = [];
            el.extraWrap.querySelectorAll('.extra-row').forEach((row) => {
                const label = row.querySelector('.extra-label').value || 'Extra';
                const amount = parseFloat(row.querySelector('.extra-amount').value) || 0;
                if (amount > 0) extras.push({ label, amount });
            });

            const divisor = parseInt(el.divisor.value) || 30;

            try {
                const budgetData = {
                    categories: categories,
                    extras: extras,
                    divisor: divisor
                };

                await saveBudget(s.year, s.month + 1, budgetData);

                if (onSaved) onSaved(day);
                ResumoModal.close();
                window.showToast('Planejamento salvo com sucesso!', 'success');
            } catch (e) {
                console.error('Erro ao salvar:', e);
                window.showToast('Erro ao salvar planejamento', 'error');
            }
        },

        async updateComputed() {
            const s = getState ? getState() : null;
            if (!s) return;
            const el = getElements();

            const divisor = parseInt(el.divisor.value) || 30;
            const totalPlanned = parseFloat(el.totalMensal.textContent.replace('R$ ', '').replace(/\./g, '').replace(',', '.')) || 0;
            const daily = divisor > 0 ? (totalPlanned / divisor) : 0;
            el.totalDiario.textContent = fmt(daily);
        }
    };

    window.ResumoModal = ResumoModal;
})();