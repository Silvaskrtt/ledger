(function () {
    const MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const SEED = [
        { day: 1, income: 3000, expense: 500, daily: 100, savings: 200, card: 0 },
        { day: 2, income: 0, expense: 180, daily: 100, savings: 0, card: 150 },
        { day: 3, income: 0, expense: 320, daily: 100, savings: 0, card: 0 },
        { day: 4, income: 0, expense: 420, daily: 100, savings: 0, card: 200 },
        { day: 5, income: 0, expense: 290, daily: 100, savings: 100, card: 0 },
        { day: 6, income: 1200, expense: 450, daily: 100, savings: 150, card: 200 },
        { day: 7, income: 0, expense: 250, daily: 100, savings: 0, card: 0 },
        { day: 8, income: 0, expense: 380, daily: 100, savings: 0, card: 180 },
        { day: 9, income: 0, expense: 540, daily: 100, savings: 0, card: 220 },
        { day: 10, income: 0, expense: 180, daily: 100, savings: 50, card: 0 },
    ];

    const state = {
        today: new Date(),
        month: 5,
        year: 2025,
        txType: "Despesa",
        data: {}, // key `${y}-${m}` -> array of tx entries
    };

    const key = (y, m) => `${y}-${m}`;
    const daysInMonth = (y, m) => new Date(y, m + 1, 0).getDate();
    const fmt = (n) => "R$ " + Number(n).toLocaleString("pt-BR");
    const rand = (i) => (Math.sin(i * 9973) + 1) / 2;

    function ensureMonth(y, m) {
        const k = key(y, m);
        if (state.data[k]) return state.data[k];
        const dim = daysInMonth(y, m);
        const seed = (y === 2025 && m === 5) ? SEED : [];
        const map = new Map(seed.map((t) => [t.day, { ...t }]));
        for (let d = 1; d <= dim; d++) {
            if (!map.has(d)) {
                const seeded = d <= 10 && seed.length === 0;
                const expense = seeded ? 0 : Math.floor(rand(d + m * 31 + y) * 300) + 50;
                const savings = rand(d + m + 1) > 0.6 ? Math.floor(rand(d + m + 2) * 100) + 50 : 0;
                const card = rand(d + m + 3) > 0.5 ? Math.floor(rand(d + m + 4) * 150) + 50 : 0;
                map.set(d, { day: d, income: 0, expense, daily: 100, savings, card });
            }
        }
        const arr = Array.from(map.values()).sort((a, b) => a.day - b.day);
        state.data[k] = arr;
        return arr;
    }

    function computeBalances(arr) {
        let bal = 0;
        return arr.map((t) => {
            bal += (t.income || 0) - (t.expense || 0) + (t.savings || 0);
            return { ...t, balance: bal };
        });
    }

    function balanceClass(b) {
        if (b < 0) return "balance-neg";
        if (b >= 2000) return "balance-high";
        if (b >= 1000) return "balance-mid";
        return "balance-low";
    }

    function iconSvg(name) {
        const p = {
            wallet: '<path d="M20 12V8a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4"/><path d="M22 12h-6a2 2 0 0 0 0 4h6"/>',
            card: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
            up: '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
            down: '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
            pig: '<path d="M4 12v3a2 2 0 0 0 2 2h1l1 3h3l-1-3h4l1 3h3l-1-3a4 4 0 0 0 3-4v-1a4 4 0 0 0-3-3.8V6a2 2 0 0 0-2-2 3 3 0 0 0-3 3H9a5 5 0 0 0-5 5z"/><circle cx="15" cy="10" r="1"/>',
        };
        return `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${p[name]}</svg>`;
    }

    function renderStats(arr) {
        let income = 0, expense = 0;
        arr.forEach((t) => { income += t.income; expense += t.expense; });
        const finalBal = arr.length ? arr[arr.length - 1].balance : 0;
        const stats = [
            { label: "Renda Prevista", value: "R$ 3.000", tone: "primary", icon: "wallet" },
            { label: "Diário Disponível", value: "R$ 100", tone: "primary", icon: "card" },
            { label: "Total Entradas", value: fmt(income), tone: "income", icon: "up" },
            { label: "Total Saídas", value: fmt(expense), tone: "expense", icon: "down" },
            { label: "Saldo Projetado", value: fmt(finalBal), tone: "primary", icon: "pig" },
        ];
        document.getElementById("stats").innerHTML = stats.map((s) => `
      <div class="stat">
        <div class="stat-icon ${s.tone}">${iconSvg(s.icon)}</div>
        <div style="min-width:0">
          <p class="stat-label">${s.label}</p>
          <p class="stat-value">${s.value}</p>
        </div>
      </div>
    `).join("");
    }

    function renderTable(arr) {
        const { today, year, month } = state;
        const tbody = document.getElementById("tbody");
        tbody.innerHTML = arr.map((tx) => {
            const date = new Date(year, month, tx.day);
            const isToday = tx.day === today.getDate() && month === today.getMonth() && year === today.getFullYear();
            const isWeekend = date.getDay() === 0 || date.getDay() === 6;
            const badgeCls = isToday ? "today" : (isWeekend ? "weekend" : "");
            const dd = String(tx.day).padStart(2, "0");
            return `<tr>
        <td><span class="day-badge ${badgeCls}">${dd}</span></td>
        <td class="${tx.income > 0 ? "pos" : "dash"}">${tx.income > 0 ? "+ " + fmt(tx.income) : "—"}</td>
        <td class="${tx.expense > 0 ? "neg" : "dash"}">${tx.expense > 0 ? "- " + fmt(tx.expense) : "—"}</td>
        <td class="dash">${tx.daily > 0 ? fmt(tx.daily) : "—"}</td>
        <td class="dash">${tx.savings > 0 ? fmt(tx.savings) : "—"}</td>
        <td class="dash">${tx.card > 0 ? fmt(tx.card) : "—"}</td>
        <td><span class="${balanceClass(tx.balance)}">${fmt(tx.balance)}</span></td>
      </tr>`;
        }).join("");
    }

    function render() {
        const { year, month } = state;
        const arr = computeBalances(ensureMonth(year, month));
        state.data[key(year, month)] = arr;
        document.getElementById("monthLabel").textContent = `${MONTHS[month]} ${year}`;
        document.getElementById("daysLabel").textContent = `${daysInMonth(year, month)} dias no mês`;
        renderStats(arr);
        renderTable(arr);
    }

    // Navigation
    document.getElementById("prevMonth").addEventListener("click", () => {
        if (state.month === 0) { state.month = 11; state.year--; } else state.month--;
        render();
    });
    document.getElementById("nextMonth").addEventListener("click", () => {
        if (state.month === 11) { state.month = 0; state.year++; } else state.month++;
        render();
    });

    // Drawer
    const drawer = document.getElementById("drawer");
    const openDrawer = () => {
        drawer.hidden = false;
        document.getElementById("txDate").value = new Date().toISOString().slice(0, 10);
    };
    const closeDrawer = () => { drawer.hidden = true; };
    document.getElementById("openDrawer").addEventListener("click", openDrawer);
    document.getElementById("closeDrawer").addEventListener("click", closeDrawer);
    document.getElementById("cancelDrawer").addEventListener("click", closeDrawer);
    drawer.addEventListener("click", (e) => { if (e.target === drawer) closeDrawer(); });

    document.querySelectorAll(".type-btn").forEach((b) => {
        b.addEventListener("click", () => {
            document.querySelectorAll(".type-btn").forEach((x) => x.classList.remove("active"));
            b.classList.add("active");
            state.txType = b.dataset.type;
        });
    });

    document.getElementById("txForm").addEventListener("submit", (e) => {
        e.preventDefault();
        const amount = parseFloat(document.getElementById("txValue").value);
        if (!amount) return;
        const d = new Date(document.getElementById("txDate").value);
        if (isNaN(d.getTime())) return;
        const y = d.getFullYear(), m = d.getMonth(), day = d.getDate();
        const arr = ensureMonth(y, m);
        let entry = arr.find((t) => t.day === day);
        if (!entry) { entry = { day, income: 0, expense: 0, daily: 0, savings: 0, card: 0 }; arr.push(entry); arr.sort((a, b) => a.day - b.day); }
        if (state.txType === "Despesa") entry.expense += amount;
        else if (state.txType === "Receita") entry.income += amount;
        else entry.savings += amount;
        state.data[key(y, m)] = arr;
        document.getElementById("txValue").value = "";
        document.getElementById("txDescription").value = "";
        closeDrawer();
        if (y === state.year && m === state.month) render();
    });

    render();
})();
