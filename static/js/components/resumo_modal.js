(function () {
    const fmt = (value) => `R$ ${Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    let getState = null;
    let onSaved = null;

    function daysInMonth(year, month) { return new Date(year, month + 1, 0).getDate(); }

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

    function getKey(year, month, day) { return `calendar_resumo_${year}_${month}_${day}`; }
    function getPlanKey(year, month) { return `calendar_resumo_plan_${year}_${month}`; }

    function getResumoForDayInternal(year, month, day) {
        try {
            const raw = localStorage.getItem(getKey(year, month, day));
            if (!raw) return null;
            return JSON.parse(raw);
        } catch (e) {
            console.error('Erro lendo resumo', e);
            return null;
        }
    }

    function getPlanForMonth(year, month) {
        try {
            const raw = localStorage.getItem(getPlanKey(year, month));
            if (!raw) return null;
            return JSON.parse(raw);
        } catch (e) {
            console.error('Erro lendo plano mensal', e);
            return null;
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

        getResumoDisplay(day) {
            const s = getState ? getState() : null;
            if (!s) return null;
            const plan = getPlanForMonth(s.year, s.month);
            const totalDays = daysInMonth(s.year, s.month);
            const today = s.today ? new Date(s.today) : new Date();
            const todayDay = today.getDate();

            // if no monthly plan, fallback to per-day resumo
            if (!plan) {
                const resumo = getResumoForDayInternal(s.year, s.month, day);
                if (!resumo) return null;
                return fmt(Number(resumo.sum || 0));
            }

            // compute spent up to today (inclusive)
            const days = (s.summary && s.summary.days) || [];
            let spentUpToToday = 0;
            days.forEach((d) => {
                const parsed = new Date(d.date);
                const dd = parsed.getDate();
                if (dd <= todayDay) spentUpToToday += Number(d.expense || 0);
            });

            const plannedTotal = Number(plan.sum || 0);
            const remaining = plannedTotal - spentUpToToday;
            const remainingDays = Math.max(1, totalDays - todayDay + 1);
            const allocation = remainingDays > 0 ? (remaining / remainingDays) : 0;

            // For past days (<= today) show actual spent if available, otherwise show allocation
            if (day <= todayDay) {
                const dayObj = (s.summary && (s.summary.days || []).find((d) => new Date(d.date).getDate() === day));
                const spent = dayObj ? Number(dayObj.expense || 0) : 0;
                return spent ? fmt(spent) : fmt(allocation);
            }

            // future days: show allocation per day
            return fmt(allocation);
        },

        open(day) {
            const s = getState ? getState() : null;
            if (!s) {
                console.warn('Estado não disponível');
                return;
            }
            const el = getElements();
            if (!el.modal) return;

            // load monthly plan if present
            const plan = getPlanForMonth(s.year, s.month) || { categories: {}, extras: [], divisor: daysInMonth(s.year, s.month), sum: 0 };

            el.dayLabel.textContent = `${String(day).padStart(2, '0')}/${String(s.month + 1).padStart(2, '0')}/${s.year}`;
            el.totalMensal.textContent = fmt(Number(plan.sum || 0));
            el.divisor.value = plan.divisor || daysInMonth(s.year, s.month);
            el.totalDiario.textContent = fmt((Number(plan.sum || 0) / Number(el.divisor.value || daysInMonth(s.year, s.month))) || 0);

            // Populate categories from plan
            const inputs = el.categoriesWrap.querySelectorAll('.resumo-input');
            inputs.forEach((inp) => {
                const name = inp.name;
                inp.value = plan.categories && plan.categories[name] !== undefined ? plan.categories[name] : '';
            });

            // Populate extras
            el.extraWrap.innerHTML = '';
            (plan.extras || []).forEach((ex) => {
                el.extraWrap.appendChild(createExtraRow(ex.label, ex.amount));
            });

            el.modal.dataset.editDay = String(day);
            el.modal.hidden = false;
            ResumoModal.updateComputed();
        },

        close() {
            const el = getElements();
            if (!el.modal) return;
            el.modal.hidden = true;
            delete el.modal.dataset.editDay;
        },

        save() {
            const s = getState ? getState() : null;
            if (!s) return;
            const el = getElements();
            const day = Number(el.modal.dataset.editDay) || 1;

            // Collect categories
            const categories = {};
            el.categoriesWrap.querySelectorAll('.resumo-input').forEach((inp) => {
                const val = parseFloat(inp.value);
                categories[inp.name] = isNaN(val) ? 0 : val;
            });

            // Collect extras
            const extras = [];
            el.extraWrap.querySelectorAll('.extra-row').forEach((row) => {
                const label = row.querySelector('.extra-label').value || 'Extra';
                const amount = parseFloat(row.querySelector('.extra-amount').value) || 0;
                if (amount > 0) extras.push({ label, amount });
            });

            const divisor = parseInt(el.divisor.value) || daysInMonth(s.year, s.month);
            const sumCategories = Object.values(categories).reduce((a, b) => a + Number(b || 0), 0);
            const sumExtras = extras.reduce((a, b) => a + Number(b.amount || 0), 0);
            const plannedTotal = sumCategories + sumExtras;

            const payload = { categories, extras, divisor, sum: plannedTotal };
            try {
                // save as monthly plan
                localStorage.setItem(getPlanKey(s.year, s.month), JSON.stringify(payload));
                if (onSaved) onSaved(day, plannedTotal);
                ResumoModal.close();
            } catch (e) {
                console.error('Erro ao salvar resumo', e);
                if (window.showToast) {
                    window.showToast('Não foi possível salvar o resumo', 'error');
                }
            }
        },

        updateComputed() {
            const s = getState ? getState() : null;
            if (!s) return;
            const el = getElements();
            const plan = getPlanForMonth(s.year, s.month) || { sum: 0 };
            const totalDays = daysInMonth(s.year, s.month);
            const today = s.today ? new Date(s.today) : new Date();
            const todayDay = today.getDate();

            // compute spent up to today
            const days = (s.summary && s.summary.days) || [];
            let spentUpToToday = 0;
            days.forEach((d) => {
                const parsed = new Date(d.date);
                const dd = parsed.getDate();
                if (dd <= todayDay) spentUpToToday += Number(d.expense || 0);
            });

            const plannedTotal = Number(plan.sum || 0);
            const remaining = plannedTotal - spentUpToToday;
            const remainingDays = Math.max(1, totalDays - todayDay + 1);
            const daily = remainingDays > 0 ? (remaining / remainingDays) : 0;
            el.totalDiario.textContent = fmt(daily);
            el.totalMensal.textContent = fmt(plannedTotal);
        }
    };

    window.ResumoModal = ResumoModal;
})();