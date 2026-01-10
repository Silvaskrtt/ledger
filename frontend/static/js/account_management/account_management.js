// Configurações
const API_BASE = '/api';
const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

// Estado da aplicação
let state = {
    accounts: [],
    currentFilter: 'all',
    isEditing: false,
    currentEditId: null
};

// Elementos do DOM
const elements = {
    accountForm: document.getElementById('account-form'),
    accountsList: document.getElementById('accounts-list'),
    accountTypeSelect: document.getElementById('account-type'),
    creditCardFields: document.getElementById('credit-card-fields'),
    formTitle: document.getElementById('form-title'),
    submitBtn: document.getElementById('submit-btn'),
    cancelBtn: document.getElementById('cancel-btn'),
    accountsCount: document.getElementById('accounts-count'),
    totalBalance: document.getElementById('total-balance'),
    creditCardsCount: document.getElementById('credit-cards-count'),
    filters: document.querySelectorAll('.filter-btn'),
    messageContainer: document.getElementById('message-container'),
    iconPreview: document.getElementById('icon-preview')
};

// Templates
const accountTemplate = document.getElementById('account-template');

// Funções utilitárias
function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    
    elements.messageContainer.innerHTML = '';
    elements.messageContainer.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatAccountType(type) {
    const types = {
        'CHECKING': 'Conta Corrente',
        'SAVINGS': 'Poupança',
        'CREDIT_CARD': 'Cartão de Crédito',
        'INVESTMENT': 'Investimentos',
        'CASH': 'Dinheiro',
        'OTHER': 'Outro'
    };
    return types[type] || type;
}

function getIconForType(type) {
    const icons = {
        'CHECKING': 'building-columns',
        'SAVINGS': 'piggy-bank',
        'CREDIT_CARD': 'credit-card',
        'INVESTMENT': 'chart-line',
        'CASH': 'money-bill-wave',
        'OTHER': 'wallet'
    };
    return icons[type] || 'wallet';
}

function updateSummary() {
    const total = state.accounts.reduce((sum, account) => sum + parseFloat(account.balance), 0);
    const creditCards = state.accounts.filter(acc => acc.type === 'CREDIT_CARD').length;
    
    elements.totalBalance.textContent = formatCurrency(total);
    elements.creditCardsCount.textContent = creditCards;
    elements.accountsCount.textContent = state.accounts.length;
}

// Funções de API
async function fetchAccounts() {
    try {
        const response = await fetch(`${API_BASE}/accounts/`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar contas');
        
        const accounts = await response.json();
        state.accounts = accounts;
        renderAccounts();
        updateSummary();
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao carregar contas', 'error');
    }
}

async function createAccount(accountData) {
    try {
        const response = await fetch(`${API_BASE}/accounts/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(accountData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || JSON.stringify(error));
        }
        
        const newAccount = await response.json();
        state.accounts.push(newAccount);
        renderAccounts();
        updateSummary();
        showMessage('Conta criada com sucesso!');
        
        return newAccount;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao criar conta', 'error');
        throw error;
    }
}

async function updateAccount(accountId, accountData) {
    try {
        const response = await fetch(`${API_BASE}/accounts/${accountId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(accountData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || JSON.stringify(error));
        }
        
        const updatedAccount = await response.json();
        const index = state.accounts.findIndex(acc => acc.id_account === accountId);
        if (index !== -1) {
            state.accounts[index] = updatedAccount;
        }
        
        renderAccounts();
        updateSummary();
        showMessage('Conta atualizada com sucesso!');
        
        return updatedAccount;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao atualizar conta', 'error');
        throw error;
    }
}

async function deleteAccount(accountId) {
    if (!confirm('Tem certeza que deseja excluir esta conta?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/accounts/${accountId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao excluir conta');
        }
        
        const index = state.accounts.findIndex(acc => acc.id_account === accountId);
        if (index !== -1) {
            state.accounts[index].is_active = false;
        }
        
        renderAccounts();
        updateSummary();
        showMessage('Conta excluída com sucesso!');
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao excluir conta', 'error');
    }
}

async function toggleAccountStatus(accountId, isActive) {
    try {
        const response = await fetch(`${API_BASE}/accounts/${accountId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ is_active: isActive })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao alterar status da conta');
        }
        
        const updatedAccount = await response.json();
        const index = state.accounts.findIndex(acc => acc.id_account === accountId);
        if (index !== -1) {
            state.accounts[index] = updatedAccount;
        }
        
        renderAccounts();
        updateSummary();
        showMessage(`Conta ${isActive ? 'reativada' : 'ocultada'} com sucesso!`);
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao alterar status da conta', 'error');
    }
}

// Renderização
function renderAccounts() {
    if (!elements.accountsList) return;
    
    // Filtrar contas
    let filteredAccounts = state.accounts;
    if (state.currentFilter !== 'all') {
        filteredAccounts = state.accounts.filter(acc => acc.type === state.currentFilter);
    }
    
    if (filteredAccounts.length === 0) {
        elements.accountsList.innerHTML = `
            <div class="message info">
                <i class="fas fa-info-circle"></i>
                Nenhuma conta encontrada. ${state.currentFilter !== 'all' ? 'Tente outro filtro.' : 'Adicione sua primeira conta!'}
            </div>
        `;
        return;
    }
    
    let html = '';
    filteredAccounts.forEach(account => {
        html += renderAccountItem(account);
    });
    
    elements.accountsList.innerHTML = html;
    attachAccountEventListeners();
}

function renderAccountItem(account) {
    const balance = parseFloat(account.balance);
    const initialBalance = parseFloat(account.initial_balance);
    const isCreditCard = account.type === 'CREDIT_CARD';
    const isActive = account.is_active !== false;
    const icon = account.icon || getIconForType(account.type);
    
    // Cores para o ícone
    const iconBg = account.color ? `${account.color}20` : '#3B82F620';
    const iconColor = account.color || '#3B82F6';
    
    // Para cartões de crédito, o saldo é geralmente negativo (gasto)
    const balanceClass = balance >= 0 ? 'positive' : 'negative';
    const balanceDisplay = formatCurrency(Math.abs(balance));
    
    return `
        <div class="account-item ${!isActive ? 'inactive' : ''}" 
             data-id="${account.id_account}" 
             data-type="${account.type}">
            <div class="account-main">
                <div class="account-icon" style="background-color: ${iconBg}; color: ${iconColor};">
                    <i class="fas fa-${icon}"></i>
                </div>
                <div class="account-details">
                    <div class="name-line">
                        <strong class="account-name">${account.name}</strong>
                        <span class="type-badge ${account.type}">
                            ${formatAccountType(account.type)}
                        </span>
                        ${!isActive ? '<span class="inactive-badge">Inativa</span>' : ''}
                    </div>
                    <div class="info-line">
                        ${account.bank_name ? `
                            <span class="bank-name">${account.bank_name}</span>
                            <span class="dot">•</span>
                        ` : ''}
                        <span class="balance-text">Saldo: 
                            <span class="balance-value ${balanceClass}">
                                ${isCreditCard && balance < 0 ? '-' : ''}${balanceDisplay}
                            </span>
                        </span>
                        <span class="dot">•</span>
                        <span class="initial-balance-text">Inicial: 
                            <span class="initial-value">${formatCurrency(initialBalance)}</span>
                        </span>
                    </div>
                    <div class="extra-info">
                        ${account.description ? `
                            <span class="description-text">${account.description}</span>
                        ` : ''}
                        ${isCreditCard && account.credit_limit ? `
                            <span class="credit-limit-text">
                                <i class="fas fa-credit-card"></i> 
                                Limite: <span class="limit-value">${formatCurrency(account.credit_limit)}</span>
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
            <div class="item-actions">
                <button class="action-btn edit" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn ${isActive ? 'delete' : 'hide'}" 
                        title="${isActive ? 'Excluir' : 'Reativar'}">
                    <i class="fas fa-${isActive ? 'trash' : 'eye'}"></i>
                </button>
                ${isActive ? `
                    <button class="action-btn hide" title="Ocultar">
                        <i class="fas fa-eye-slash"></i>
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

// Event Listeners
function attachAccountEventListeners() {
    // Botões de edição
    document.querySelectorAll('.action-btn.edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const accountItem = this.closest('.account-item');
            const accountId = accountItem.dataset.id;
            const account = state.accounts.find(acc => acc.id_account === accountId);
            
            if (account) {
                editAccount(account);
            }
        });
    });
    
    // Botões de exclusão/reativação
    document.querySelectorAll('.action-btn.delete, .action-btn.hide').forEach(btn => {
        btn.addEventListener('click', function() {
            const accountItem = this.closest('.account-item');
            const accountId = accountItem.dataset.id;
            const account = state.accounts.find(acc => acc.id_account === accountId);
            
            if (account) {
                if (this.classList.contains('delete')) {
                    deleteAccount(accountId);
                } else if (this.classList.contains('hide')) {
                    const isActive = account.is_active !== false;
                    toggleAccountStatus(accountId, !isActive);
                }
            }
        });
    });
}

// Formulário
function setupFormListeners() {
    // Mostrar/ocultar campos de cartão de crédito
    if (elements.accountTypeSelect) {
        elements.accountTypeSelect.addEventListener('change', function() {
            const isCreditCard = this.value === 'CREDIT_CARD';
            elements.creditCardFields.style.display = isCreditCard ? 'block' : 'none';
            
            // Atualizar campos obrigatórios
            const creditLimit = document.getElementById('credit-limit');
            const closingDay = document.getElementById('closing-day');
            const dueDay = document.getElementById('due-day');
            
            if (isCreditCard) {
                creditLimit.required = true;
                closingDay.required = true;
                dueDay.required = true;
            } else {
                creditLimit.required = false;
                closingDay.required = false;
                dueDay.required = false;
            }
            
            // Atualizar ícone baseado no tipo
            if (elements.iconPreview) {
                const icon = getIconForType(this.value);
                elements.iconPreview.className = `fas fa-${icon}`;
                document.getElementById('account-icon').value = icon;
            }
        });
    }
    
    // Seletor de ícone
    const iconSelect = document.getElementById('account-icon');
    if (iconSelect && elements.iconPreview) {
        iconSelect.addEventListener('change', function() {
            elements.iconPreview.className = `fas fa-${this.value}`;
        });
    }
    
    // Submeter formulário
    if (elements.accountForm) {
        elements.accountForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const accountData = {
                name: formData.get('name'),
                type: formData.get('type'),
                initial_balance: parseFloat(formData.get('initial_balance')),
                bank_name: formData.get('bank_name') || '',
                description: formData.get('description') || '',
                icon: formData.get('icon') || 'wallet',
                color: formData.get('color') || '#3B82F6'
            };
            
            // Campos específicos de cartão de crédito
            if (accountData.type === 'CREDIT_CARD') {
                accountData.credit_limit = parseFloat(formData.get('credit_limit'));
                accountData.closing_day = parseInt(formData.get('closing_day'));
                accountData.due_day = parseInt(formData.get('due_day'));
            }
            
            try {
                if (state.isEditing && state.currentEditId) {
                    await updateAccount(state.currentEditId, accountData);
                    resetForm();
                } else {
                    await createAccount(accountData);
                    this.reset();
                    // Resetar ícone
                    if (elements.iconPreview) {
                        elements.iconPreview.className = 'fas fa-wallet';
                    }
                }
            } catch (error) {
                console.error('Erro ao salvar conta:', error);
            }
        });
    }
    
    // Botão cancelar
    if (elements.cancelBtn) {
        elements.cancelBtn.addEventListener('click', resetForm);
    }
}

// Filtros
function setupFilters() {
    elements.filters.forEach(filter => {
        filter.addEventListener('click', function() {
            // Atualizar filtro ativo
            elements.filters.forEach(f => f.classList.remove('active'));
            this.classList.add('active');
            
            // Atualizar estado e renderizar
            state.currentFilter = this.dataset.filter;
            renderAccounts();
        });
    });
}

// Editar conta
function editAccount(account) {
    state.isEditing = true;
    state.currentEditId = account.id_account;
    
    // Atualizar formulário
    document.getElementById('account-id').value = account.id_account;
    document.getElementById('account-name').value = account.name;
    document.getElementById('account-type').value = account.type;
    document.getElementById('initial-balance').value = account.initial_balance;
    document.getElementById('bank-name').value = account.bank_name || '';
    document.getElementById('account-description').value = account.description || '';
    document.getElementById('account-icon').value = account.icon || 'wallet';
    document.getElementById('account-color').value = account.color || '#3B82F6';
    
    // Atualizar ícone preview
    if (elements.iconPreview) {
        elements.iconPreview.className = `fas fa-${account.icon || 'wallet'}`;
    }
    
    // Campos de cartão de crédito
    if (account.type === 'CREDIT_CARD') {
        elements.creditCardFields.style.display = 'block';
        document.getElementById('credit-limit').value = account.credit_limit || '';
        document.getElementById('closing-day').value = account.closing_day || '';
        document.getElementById('due-day').value = account.due_day || '';
    }
    
    // Atualizar interface
    elements.formTitle.innerHTML = '<i class="fas fa-edit"></i> Editar Conta';
    elements.submitBtn.innerHTML = '<i class="fas fa-save"></i> Salvar Alterações';
    elements.cancelBtn.style.display = 'block';
    
    // Scroll para o formulário
    document.querySelector('.account-form-card').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
    });
}

function resetForm() {
    state.isEditing = false;
    state.currentEditId = null;
    
    // Resetar formulário
    elements.accountForm.reset();
    document.getElementById('account-id').value = '';
    elements.creditCardFields.style.display = 'none';
    
    // Resetar ícone
    if (elements.iconPreview) {
        elements.iconPreview.className = 'fas fa-wallet';
    }
    
    // Atualizar interface
    elements.formTitle.innerHTML = '<i class="fas fa-plus"></i> Adicionar Nova Conta';
    elements.submitBtn.innerHTML = '<i class="fas fa-plus"></i> Adicionar Conta';
    elements.cancelBtn.style.display = 'none';
}

// Inicialização
function init() {
    setupFormListeners();
    setupFilters();
    fetchAccounts();
}

// Iniciar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', init);