// MyLedger - Main Application
// Gestão Financeira Pessoal com Interface Moderna

// ===== DATA MODELS =====

// Dados de transações (mock/inicial)
const transactions = [
    { id: 1, type: 'expense', desc: 'Supermercado', cat: '🍔 Alimentação', value: 342.50, date: '2025-06-15', color: '#ef4444' },
    { id: 2, type: 'income', desc: 'Salário', cat: '💼 Trabalho', value: 5000, date: '2025-06-01', color: '#10b981' },
    { id: 3, type: 'expense', desc: 'Uber', cat: '🚗 Transporte', value: 28.90, date: '2025-06-14', color: '#ef4444' },
    { id: 4, type: 'expense', desc: 'Netflix', cat: '🎮 Lazer', value: 39.90, date: '2025-06-10', color: '#ef4444' },
    { id: 5, type: 'income', desc: 'Freelance', cat: '💼 Trabalho', value: 1200, date: '2025-06-08', color: '#10b981' },
];

// Categorias pré-definidas
const categories = [
    { name: 'Alimentação', icon: '🍔', color: '#8A4FFF' },
    { name: 'Transporte', icon: '🚗', color: '#5E2C9A' },
    { name: 'Lazer', icon: '🎮', color: '#c084fc' },
    { name: 'Moradia', icon: '🏠', color: '#6366f1' },
    { name: 'Trabalho', icon: '💼', color: '#10b981' },
    { name: 'Educação', icon: '📚', color: '#ec4899' },
];

// ===== STATE MANAGEMENT =====
let currentScreen = 'login';
let isRegister = false;
let txFilter = 'all';
let nextTransactionId = 6; // Próximo ID disponível
let currentEditingTransaction = null;

// ===== HELPER FUNCTIONS =====

// Formatar valor monetário
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Calcular saldo total
function calculateBalance() {
    const totalIncome = transactions
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + t.value, 0);

    const totalExpense = transactions
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + t.value, 0);

    return { total: totalIncome - totalExpense, income: totalIncome, expense: totalExpense };
}

// Atualizar dashboard com dados reais
function updateDashboardStats() {
    const balance = calculateBalance();

    const balanceEl = document.querySelector('#screen-dashboard .text-3xl.font-bold');
    if (balanceEl) balanceEl.textContent = formatCurrency(balance.total);

    const incomeEl = document.querySelector('#screen-dashboard .text-emerald-400');
    if (incomeEl) incomeEl.textContent = formatCurrency(balance.income);

    const expenseEl = document.querySelector('#screen-dashboard .text-red-400');
    if (expenseEl) expenseEl.textContent = formatCurrency(balance.expense);
}

// ===== RENDER FUNCTIONS =====

// Renderizar card de transação
function txCard(tx, showActions = false) {
    const sign = tx.type === 'income' ? '+' : '-';
    const col = tx.type === 'income' ? 'text-emerald-400' : 'text-red-400';
    const valueFormatted = formatCurrency(tx.value);

    let actions = '';
    if (showActions) {
        actions = `
      <div class="swipe-actions ml-2 flex-shrink-0">
        <button class="w-8 h-8 rounded-lg bg-vivid/20 flex items-center justify-center" onclick="editTransaction(${tx.id})" title="Editar">
          <i data-lucide="edit-2" class="w-3.5 h-3.5 text-vivid"></i>
        </button>
        <button class="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center" onclick="deleteTransaction(${tx.id})" title="Excluir">
          <i data-lucide="trash-2" class="w-3.5 h-3.5 text-red-400"></i>
        </button>
      </div>
    `;
    }

    const catIcon = tx.cat.split(' ')[0];
    const catName = tx.cat.split(' ').slice(1).join(' ');

    return `
    <div class="glass rounded-2xl p-4 flex items-center gap-3 fade-up" data-tx-id="${tx.id}">
      <div class="w-10 h-10 rounded-xl glass flex items-center justify-center text-lg flex-shrink-0">${catIcon}</div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium truncate">${escapeHtml(tx.desc)}</p>
        <p class="text-[10px] text-white/40">${catName} · ${formatDate(tx.date)}</p>
      </div>
      <p class="text-sm font-bold ${col} flex-shrink-0">${sign} ${valueFormatted}</p>
      ${actions}
    </div>
  `;
}

// Escapar HTML para prevenir XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function parseLocalDate(dateString) {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day);
}

// Formatar data para exibição
function formatDate(dateString) {
    const date = parseLocalDate(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Renderizar transações recentes no dashboard
function renderRecent() {
    const recentContainer = document.getElementById('recent-tx');
    if (!recentContainer) return;

    const recentTransactions = [...transactions]
        .sort((a, b) => parseLocalDate(b.date) - parseLocalDate(a.date))
        .slice(0, 4);

    recentContainer.innerHTML = recentTransactions.map(t => txCard(t, false)).join('');
    lucide.createIcons();
}

// Renderizar lista completa de transações
function renderFullTx() {
    const searchInput = document.getElementById('tx-search');
    const search = searchInput?.value?.toLowerCase() || '';

    let filtered = [...transactions];

    if (txFilter === 'income') {
        filtered = filtered.filter(t => t.type === 'income');
    } else if (txFilter === 'expense') {
        filtered = filtered.filter(t => t.type === 'expense');
    }

    if (search) {
        filtered = filtered.filter(t =>
            t.desc.toLowerCase().includes(search) ||
            t.cat.toLowerCase().includes(search)
        );
    }

    // Ordenar por data (mais recente primeiro)
    filtered.sort((a, b) => parseLocalDate(b.date) - parseLocalDate(a.date));

    const container = document.getElementById('tx-list-full');
    if (!container) return;

    if (filtered.length === 0) {
        container.innerHTML = `
      <div class="glass rounded-2xl p-8 text-center fade-up">
        <i data-lucide="inbox" class="w-12 h-12 text-white/20 mx-auto mb-3"></i>
        <p class="text-white/40 text-sm">Nenhuma transação encontrada</p>
      </div>
    `;
    } else {
        container.innerHTML = filtered.map(t => txCard(t, true)).join('');
    }

    lucide.createIcons();
}

// Renderizar categorias
function renderCats() {
    const container = document.getElementById('cat-list');
    if (!container) return;

    container.innerHTML = categories.map(c => `
    <div class="glass rounded-2xl p-4 flex items-center gap-3 fade-up">
      <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg" style="background: ${c.color}30">${c.icon}</div>
      <span class="text-sm font-medium flex-1">${c.name}</span>
      <button class="w-8 h-8 rounded-lg glass flex items-center justify-center" onclick="editCategory('${c.name}')">
        <i data-lucide="edit-2" class="w-3.5 h-3.5 text-white/50"></i>
      </button>
      <button class="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center" onclick="deleteCategory('${c.name}')">
        <i data-lucide="trash-2" class="w-3.5 h-3.5 text-red-400"></i>
      </button>
    </div>
  `).join('');

    lucide.createIcons();
}

// ===== CRUD OPERATIONS =====

// Salvar nova transação
function saveTransaction() {
    const type = document.getElementById('tog-income').classList.contains('active') ? 'income' : 'expense';
    const valueInput = document.getElementById('tx-value');
    const dateInput = document.getElementById('tx-date');
    const catSelect = document.getElementById('tx-cat');
    const descTextarea = document.getElementById('tx-desc');

    // Validação
    if (!valueInput.value || parseFloat(valueInput.value) <= 0) {
        showToast('Por favor, insira um valor válido', 'error');
        return;
    }

    if (!dateInput.value) {
        showToast('Por favor, selecione uma data', 'error');
        return;
    }

    if (!descTextarea.value.trim()) {
        showToast('Por favor, insira uma descrição', 'error');
        return;
    }

    const newTransaction = {
        id: nextTransactionId++,
        type: type,
        desc: descTextarea.value.trim(),
        cat: catSelect.value,
        value: parseFloat(valueInput.value),
        date: dateInput.value,
        color: type === 'income' ? '#10b981' : '#ef4444'
    };

    transactions.push(newTransaction);

    // Limpar formulário
    valueInput.value = '';
    dateInput.value = '';
    descTextarea.value = '';

    showToast('Transação salva com sucesso!', 'success');

    // Atualizar interfaces
    updateDashboardStats();
    renderRecent();

    if (currentScreen === 'transactions') {
        renderFullTx();
    }

    // Voltar para dashboard
    goTo('dashboard');
}

// Função wrapper para manter compatibilidade
function saveTx() {
    saveTransaction();
}

// Editar transação
function editTransaction(id) {
    const transaction = transactions.find(t => t.id === id);
    if (!transaction) return;

    currentEditingTransaction = transaction;

    // Preencher formulário de edição
    const type = transaction.type;
    document.getElementById('tog-income').classList.toggle('active', type === 'income');
    document.getElementById('tog-expense').classList.toggle('active', type === 'expense');
    document.getElementById('tx-value').value = transaction.value;
    document.getElementById('tx-date').value = transaction.date;
    document.getElementById('tx-cat').value = transaction.cat;
    document.getElementById('tx-desc').value = transaction.desc;

    // Mudar botão para "Atualizar"
    const saveBtn = document.querySelector('#screen-add .btn-gradient');
    if (saveBtn) {
        saveBtn.textContent = 'Atualizar';
        saveBtn.setAttribute('onclick', 'updateTransaction()');
    }

    goTo('add');
}

// Atualizar transação existente
function updateTransaction() {
    if (!currentEditingTransaction) return;

    const type = document.getElementById('tog-income').classList.contains('active') ? 'income' : 'expense';
    const value = parseFloat(document.getElementById('tx-value').value);
    const date = document.getElementById('tx-date').value;
    const cat = document.getElementById('tx-cat').value;
    const desc = document.getElementById('tx-desc').value.trim();

    if (!value || value <= 0 || !date || !desc) {
        showToast('Por favor, preencha todos os campos', 'error');
        return;
    }

    currentEditingTransaction.type = type;
    currentEditingTransaction.value = value;
    currentEditingTransaction.date = date;
    currentEditingTransaction.cat = cat;
    currentEditingTransaction.desc = desc;

    showToast('Transação atualizada com sucesso!', 'success');

    updateDashboardStats();
    renderRecent();

    if (currentScreen === 'transactions') {
        renderFullTx();
    }

    currentEditingTransaction = null;

    // Restaurar botão
    const saveBtn = document.querySelector('#screen-add .btn-gradient');
    if (saveBtn) {
        saveBtn.textContent = 'Salvar';
        saveBtn.setAttribute('onclick', 'saveTx()');
    }

    goTo('dashboard');
}

// Excluir transação
function deleteTransaction(id) {
    if (confirm('Tem certeza que deseja excluir esta transação?')) {
        const index = transactions.findIndex(t => t.id === id);
        if (index !== -1) {
            transactions.splice(index, 1);
            showToast('Transação excluída com sucesso!', 'success');

            updateDashboardStats();
            renderRecent();

            if (currentScreen === 'transactions') {
                renderFullTx();
            }
        }
    }
}

// ===== CATEGORY MANAGEMENT =====

// Editar categoria
function editCategory(catName) {
    const category = categories.find(c => c.name === catName);
    if (!category) return;

    document.getElementById('cat-name').value = category.name;
    document.getElementById('cat-color').value = category.color;
    showCatModal();
}

// Excluir categoria
function deleteCategory(catName) {
    if (confirm(`Tem certeza que deseja excluir a categoria "${catName}"?`)) {
        const index = categories.findIndex(c => c.name === catName);
        if (index !== -1) {
            categories.splice(index, 1);
            renderCats();
            showToast('Categoria excluída com sucesso!', 'success');
        }
    }
}

// ===== UI HELPER FUNCTIONS =====

// Exibir toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-24 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-xl text-sm font-medium z-50 fade-up ${type === 'success' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
        }`;
    toast.style.zIndex = '9999';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Filtrar transações
function filterTx() {
    renderFullTx();
}

// Set filter para transações
function setTxFilter(filter, btn) {
    txFilter = filter;
    const parent = btn.parentElement;
    if (parent) {
        parent.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    }
    btn.classList.add('active');
    renderFullTx();
}

// Set tipo de transação (income/expense)
function setTxType(type) {
    const incomeBtn = document.getElementById('tog-income');
    const expenseBtn = document.getElementById('tog-expense');

    if (incomeBtn && expenseBtn) {
        incomeBtn.classList.toggle('active', type === 'income');
        expenseBtn.classList.toggle('active', type === 'expense');
    }
}

// Toggle entre login e registro
function toggleRegister() {
    isRegister = !isRegister;

    const registerField = document.getElementById('register-name-field');
    const loginSubtitle = document.getElementById('login-subtitle');
    const loginBtnText = document.getElementById('login-btn-text');
    const toggleBtn = document.getElementById('toggle-register');

    if (registerField) registerField.classList.toggle('hidden', !isRegister);
    if (loginSubtitle) loginSubtitle.textContent = isRegister ? 'Crie sua conta' : 'Entre na sua conta';
    if (loginBtnText) loginBtnText.textContent = isRegister ? 'Registrar' : 'Entrar';
    if (toggleBtn) toggleBtn.textContent = isRegister ? 'Já tenho conta' : 'Registrar-se';
}

// ===== MODAL MANAGEMENT =====

function showCatModal() {
    const modal = document.getElementById('cat-modal');
    if (modal) modal.classList.remove('hidden');
}

function hideCatModal() {
    const modal = document.getElementById('cat-modal');
    if (modal) modal.classList.add('hidden');
}

// ===== NAVIGATION =====

function goTo(screen) {
    // Esconder todas as telas
    document.querySelectorAll('.screen').forEach(s => {
        s.classList.remove('active');
    });

    // Mostrar tela selecionada
    const targetScreen = document.getElementById('screen-' + screen);
    if (targetScreen) {
        targetScreen.classList.add('active');
    }

    currentScreen = screen;

    // Gerenciar barra de navegação
    const nav = document.getElementById('bottom-nav');
    if (nav) {
        nav.style.display = screen === 'login' ? 'none' : 'block';
    }

    // Atualizar estado ativo da navegação
    const navMap = {
        dashboard: 'home',
        transactions: 'repeat',
        categories: 'tag',
        reports: 'bar-chart-3',
        profile: 'user'
    };

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const icon = navMap[screen];
    if (icon) {
        document.querySelectorAll('.nav-item').forEach(n => {
            if (n.querySelector(`[data-lucide="${icon}"]`)) {
                n.classList.add('active');
            }
        });
    }

    // Renderizar conteúdo específico
    if (screen === 'dashboard') {
        updateDashboardStats();
        renderRecent();
    } else if (screen === 'transactions') {
        renderFullTx();
    } else if (screen === 'categories') {
        renderCats();
    }

    // Recriar ícones
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// ===== INITIALIZATION =====

// Atualizar dashboard quando necessário
function refreshDashboard() {
    updateDashboardStats();
    renderRecent();
}

// Exportar funções para escopo global
window.goTo = goTo;
window.toggleRegister = toggleRegister;
window.setTxType = setTxType;
window.saveTx = saveTx;
window.filterTx = filterTx;
window.setTxFilter = setTxFilter;
window.showCatModal = showCatModal;
window.hideCatModal = hideCatModal;
window.editTransaction = editTransaction;
window.deleteTransaction = deleteTransaction;
window.editCategory = editCategory;
window.deleteCategory = deleteCategory;
window.updateTransaction = updateTransaction;
window.refreshDashboard = refreshDashboard;

// Inicializar ícones quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Inicializar dashboard com dados
    updateDashboardStats();
    renderRecent();
});

// ===== ELEMENT SDK INTEGRATION =====

const defaultConfig = {
    greeting_name: 'Carlos',
    balance_label: 'Saldo Total',
    background_color: '#0A0A0A',
    surface_color: 'rgba(255,255,255,0.06)',
    text_color: '#FFFFFF',
    primary_action: '#8A4FFF',
    secondary_action: '#5E2C9A',
    font_family: 'DM Sans',
    font_size: 14,
};

async function onConfigChange(config) {
    const name = config.greeting_name || defaultConfig.greeting_name;
    const balLabel = config.balance_label || defaultConfig.balance_label;
    const font = config.font_family || defaultConfig.font_family;
    const baseSize = config.font_size || defaultConfig.font_size;
    const bg = config.background_color || defaultConfig.background_color;
    const txt = config.text_color || defaultConfig.text_color;
    const primary = config.primary_action || defaultConfig.primary_action;
    const secondary = config.secondary_action || defaultConfig.secondary_action;

    const dashGreeting = document.getElementById('dash-greeting');
    const profileName = document.getElementById('profile-name');
    const balanceLabel = document.getElementById('balance-label-el');

    if (dashGreeting) dashGreeting.textContent = name;
    if (profileName) profileName.textContent = name;
    if (balanceLabel) balanceLabel.textContent = balLabel;

    document.body.style.fontFamily = `${font}, sans-serif`;
    document.body.style.fontSize = `${baseSize}px`;
    document.body.style.backgroundColor = bg;
    document.body.style.color = txt;

    document.querySelectorAll('.btn-gradient, .fab').forEach(el => {
        el.style.background = `linear-gradient(135deg, ${secondary}, ${primary})`;
    });

    document.querySelectorAll('.nav-item.active, .text-vivid, .toggle-btn.active').forEach(el => {
        el.style.color = primary;
    });
}

if (typeof window.elementSdk !== 'undefined') {
    window.elementSdk.init({
        defaultConfig,
        onConfigChange,
        mapToCapabilities: (config) => ({
            recolorables: [
                { get: () => config.background_color || defaultConfig.background_color, set: v => { config.background_color = v; window.elementSdk.setConfig({ background_color: v }); } },
                { get: () => config.surface_color || defaultConfig.surface_color, set: v => { config.surface_color = v; window.elementSdk.setConfig({ surface_color: v }); } },
                { get: () => config.text_color || defaultConfig.text_color, set: v => { config.text_color = v; window.elementSdk.setConfig({ text_color: v }); } },
                { get: () => config.primary_action || defaultConfig.primary_action, set: v => { config.primary_action = v; window.elementSdk.setConfig({ primary_action: v }); } },
                { get: () => config.secondary_action || defaultConfig.secondary_action, set: v => { config.secondary_action = v; window.elementSdk.setConfig({ secondary_action: v }); } },
            ],
            borderables: [],
            fontEditable: { get: () => config.font_family || defaultConfig.font_family, set: v => { config.font_family = v; window.elementSdk.setConfig({ font_family: v }); } },
            fontSizeable: { get: () => config.font_size || defaultConfig.font_size, set: v => { config.font_size = v; window.elementSdk.setConfig({ font_size: v }); } },
        }),
        mapToEditPanelValues: (config) => new Map([
            ['greeting_name', config.greeting_name || defaultConfig.greeting_name],
            ['balance_label', config.balance_label || defaultConfig.balance_label],
        ]),
    });
}

console.log('MyLedger - Aplicação inicializada com sucesso!');