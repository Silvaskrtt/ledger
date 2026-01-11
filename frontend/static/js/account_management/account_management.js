// Configurações
const API_BASE = '/api';
const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                   document.querySelector('input[name=csrfmiddlewaretoken]')?.value;

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
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

function formatCurrency(value) {
    if (isNaN(value) || value === null || value === undefined) {
        return 'R$ 0,00';
    }
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
    try {
        if (!state.accounts || !Array.isArray(state.accounts)) {
            state.accounts = [];
        }
        
        const total = state.accounts.reduce((sum, account) => {
            const balance = parseFloat(account.balance || 0);
            return sum + balance;
        }, 0);
        
        const creditCards = state.accounts.filter(acc => acc.type === 'CREDIT_CARD').length;
        
        if (elements.totalBalance) {
            elements.totalBalance.textContent = formatCurrency(total);
        }
        if (elements.creditCardsCount) {
            elements.creditCardsCount.textContent = creditCards;
        }
        if (elements.accountsCount) {
            elements.accountsCount.textContent = state.accounts.length;
        }
    } catch (error) {
        console.error('Erro ao atualizar resumo:', error);
    }
}

// Funções de API
async function fetchAccounts() {
    try {
        console.log('Buscando contas...');
        const response = await fetch(`${API_BASE}/accounts/`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN || ''
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Erro na resposta:', response.status, errorText);
            throw new Error(`Erro ${response.status} ao carregar contas`);
        }
        
        const data = await response.json();
        console.log('Dados recebidos da API:', data);
        
        // Verificar o formato dos dados
        let accountsArray = [];
        
        if (Array.isArray(data)) {
            accountsArray = data;
        } else if (data && typeof data === 'object') {
            if (data.results) {
                accountsArray = data.results;
            } else if (data.data) {
                accountsArray = data.data;
            } else if (data.accounts) {
                accountsArray = data.accounts;
            } else {
                // Tentar extrair qualquer array do objeto
                const possibleArrays = Object.values(data).filter(item => Array.isArray(item));
                if (possibleArrays.length > 0) {
                    accountsArray = possibleArrays[0];
                } else {
                    // Se for um objeto simples, verificar se tem campos de conta
                    if (data.id_account || data.name) {
                        accountsArray = [data];
                    } else {
                        accountsArray = [];
                    }
                }
            }
        }
        
        console.log('Contas processadas:', accountsArray);
        state.accounts = accountsArray || [];
        renderAccounts();
        updateSummary();
        
    } catch (error) {
        console.error('Erro ao carregar contas:', error);
        showMessage('Erro ao carregar contas: ' + error.message, 'error');
        
        if (elements.accountsList) {
            elements.accountsList.innerHTML = `
                <div class="message error">
                    <i class="fas fa-exclamation-circle"></i>
                    Erro ao carregar contas. 
                    <button onclick="location.reload()" style="margin-left: 10px; padding: 5px 10px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Recarregar
                    </button>
                </div>
            `;
        }
    }
}

async function createAccount(accountData) {
    try {
        console.log('Criando conta:', accountData);
        
        // Validar dados obrigatórios
        if (!accountData.name || !accountData.type) {
            throw new Error('Nome e tipo são obrigatórios');
        }
        
        // Converter initial_balance para número
        if (accountData.initial_balance !== undefined && accountData.initial_balance !== null) {
            accountData.initial_balance = parseFloat(accountData.initial_balance) || 0;
        } else {
            accountData.initial_balance = 0;
        }
        
        // Para cartões de crédito, converter campos específicos
        if (accountData.type === 'CREDIT_CARD') {
            if (accountData.credit_limit !== undefined && accountData.credit_limit !== null) {
                accountData.credit_limit = parseFloat(accountData.credit_limit) || 0;
            }
            if (accountData.closing_day !== undefined && accountData.closing_day !== null) {
                accountData.closing_day = parseInt(accountData.closing_day) || 1;
            }
            if (accountData.due_day !== undefined && accountData.due_day !== null) {
                accountData.due_day = parseInt(accountData.due_day) || 1;
            }
        } else {
            // Para outros tipos, remover campos específicos de cartão
            delete accountData.credit_limit;
            delete accountData.closing_day;
            delete accountData.due_day;
        }
        
        // Remover campos vazios
        Object.keys(accountData).forEach(key => {
            if (accountData[key] === '' || accountData[key] === null || accountData[key] === undefined) {
                delete accountData[key];
            }
        });
        
        console.log('Dados a serem enviados:', accountData);
        
        const response = await fetch(`${API_BASE}/accounts/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN || ''
            },
            body: JSON.stringify(accountData)
        });
        
        console.log('Resposta do servidor:', response.status);
        
        // Ler a resposta apenas UMA vez
        const responseText = await response.text();
        
        if (!response.ok) {
            let errorMessage = 'Erro ao criar conta';
            try {
                const errorData = JSON.parse(responseText);
                console.error('Erro detalhado:', errorData);
                
                // Extrair mensagens de erro do serializer
                if (typeof errorData === 'object') {
                    const errors = [];
                    for (const [field, messages] of Object.entries(errorData)) {
                        if (Array.isArray(messages)) {
                            errors.push(...messages.map(msg => `${field}: ${msg}`));
                        } else if (typeof messages === 'string') {
                            errors.push(`${field}: ${messages}`);
                        } else if (typeof messages === 'object') {
                            errors.push(`${field}: ${JSON.stringify(messages)}`);
                        }
                    }
                    if (errors.length > 0) {
                        errorMessage = errors.join(', ');
                    }
                }
            } catch (e) {
                // Se não for JSON, usar o texto direto
                errorMessage = responseText || 'Erro desconhecido';
            }
            throw new Error(errorMessage);
        }
        
        // Se a resposta foi OK, parsear como JSON
        const newAccount = JSON.parse(responseText);
        console.log('Conta criada:', newAccount);
        
        state.accounts.push(newAccount);
        renderAccounts();
        updateSummary();
        showMessage('Conta criada com sucesso!');
        
        return newAccount;
        
    } catch (error) {
        console.error('Erro ao criar conta:', error);
        showMessage('Erro ao criar conta: ' + error.message, 'error');
        throw error;
    }
}

async function updateAccount(accountId, accountData) {
    try {
        console.log('Atualizando conta:', accountId, accountData);
        
        // Preparar dados para atualização
        const dataToSend = { ...accountData };
        
        // Converter valores
        if (dataToSend.initial_balance !== undefined && dataToSend.initial_balance !== null) {
            dataToSend.initial_balance = parseFloat(dataToSend.initial_balance) || 0;
        }
        
        if (dataToSend.type === 'CREDIT_CARD') {
            if (dataToSend.credit_limit !== undefined && dataToSend.credit_limit !== null) {
                dataToSend.credit_limit = parseFloat(dataToSend.credit_limit) || 0;
            }
            if (dataToSend.closing_day !== undefined && dataToSend.closing_day !== null) {
                dataToSend.closing_day = parseInt(dataToSend.closing_day) || 1;
            }
            if (dataToSend.due_day !== undefined && dataToSend.due_day !== null) {
                dataToSend.due_day = parseInt(dataToSend.due_day) || 1;
            }
        } else {
            // Para outros tipos, remover campos específicos de cartão
            delete dataToSend.credit_limit;
            delete dataToSend.closing_day;
            delete dataToSend.due_day;
        }
        
        // Remover campos vazios
        Object.keys(dataToSend).forEach(key => {
            if (dataToSend[key] === '' || dataToSend[key] === null || dataToSend[key] === undefined) {
                delete dataToSend[key];
            }
        });
        
        console.log('Dados para atualização:', dataToSend);
        
        const response = await fetch(`${API_BASE}/accounts/${accountId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN || ''
            },
            body: JSON.stringify(dataToSend)
        });
        
        if (!response.ok) {
            let errorMessage = 'Erro ao atualizar conta';
            try {
                const errorData = await response.json();
                console.error('Erro detalhado:', errorData);
                
                if (typeof errorData === 'object') {
                    const errors = [];
                    for (const [field, messages] of Object.entries(errorData)) {
                        if (Array.isArray(messages)) {
                            errors.push(...messages.map(msg => `${field}: ${msg}`));
                        } else if (typeof messages === 'string') {
                            errors.push(`${field}: ${messages}`);
                        }
                    }
                    if (errors.length > 0) {
                        errorMessage = errors.join(', ');
                    }
                }
            } catch (e) {
                const text = await response.text();
                errorMessage = text || 'Erro desconhecido';
            }
            throw new Error(errorMessage);
        }
        
        const updatedAccount = await response.json();
        console.log('Conta atualizada:', updatedAccount);
        
        const index = state.accounts.findIndex(acc => acc.id_account === accountId);
        if (index !== -1) {
            state.accounts[index] = updatedAccount;
        } else {
            state.accounts.push(updatedAccount);
        }
        
        renderAccounts();
        updateSummary();
        showMessage('Conta atualizada com sucesso!');
        
        return updatedAccount;
        
    } catch (error) {
        console.error('Erro ao atualizar conta:', error);
        showMessage('Erro ao atualizar conta: ' + error.message, 'error');
        throw error;
    }
}

async function deleteAccount(accountId) {
    if (!confirm('Tem certeza que deseja excluir esta conta?\n\nEsta ação não pode ser desfeita.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/accounts/${accountId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': CSRF_TOKEN || ''
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao excluir conta');
        }
        
        // Soft delete: marca como inativa localmente
        const index = state.accounts.findIndex(acc => acc.id_account === accountId);
        if (index !== -1) {
            state.accounts[index].is_active = false;
        }
        
        renderAccounts();
        updateSummary();
        showMessage('Conta excluída com sucesso!');
        
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao excluir conta: ' + error.message, 'error');
    }
}

async function toggleAccountStatus(accountId, isActive) {
    try {
        const response = await fetch(`${API_BASE}/accounts/${accountId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN || ''
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
        showMessage('Erro ao alterar status da conta: ' + error.message, 'error');
    }
}

// Renderização
function renderAccounts() {
    if (!elements.accountsList) {
        console.error('Elemento accountsList não encontrado');
        return;
    }
    
    // Verificar se state.accounts é um array
    if (!Array.isArray(state.accounts)) {
        console.error('state.accounts não é um array:', state.accounts);
        state.accounts = [];
    }
    
    // Filtrar contas
    let filteredAccounts = [...state.accounts];
    if (state.currentFilter !== 'all') {
        filteredAccounts = state.accounts.filter(acc => acc.type === state.currentFilter);
    }
    
    // Filtrar apenas contas ativas (opcional)
    filteredAccounts = filteredAccounts.filter(acc => acc.is_active !== false);
    
    // Verificar se filteredAccounts é um array
    if (!Array.isArray(filteredAccounts)) {
        console.error('filteredAccounts não é um array:', filteredAccounts);
        filteredAccounts = [];
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
        try {
            if (account && typeof account === 'object') {
                html += renderAccountItem(account);
            }
        } catch (error) {
            console.error('Erro ao renderizar conta:', account, error);
        }
    });
    
    elements.accountsList.innerHTML = html;
    attachAccountEventListeners();
}

function renderAccountItem(account) {
    try {
        if (!account || typeof account !== 'object') {
            console.error('Conta inválida:', account);
            return '';
        }
        
        const balance = parseFloat(account.balance || 0);
        const initialBalance = parseFloat(account.initial_balance || 0);
        const isCreditCard = account.type === 'CREDIT_CARD';
        const isActive = account.is_active !== false;
        const icon = account.icon || getIconForType(account.type);
        
        // Cores para o ícone
        const iconBg = account.color ? `${account.color}20` : '#3B82F620';
        const iconColor = account.color || '#3B82F6';
        
        // Para cartões de crédito, o saldo é geralmente negativo (gasto)
        const balanceClass = balance >= 0 ? 'positive' : 'negative';
        const balanceDisplay = formatCurrency(Math.abs(balance));
        
        // Limite de crédito para cartões
        const creditLimit = parseFloat(account.credit_limit || 0);
        const creditLimitDisplay = formatCurrency(creditLimit);
        
        const bankNameHtml = account.bank_name ? `
            <span class="bank-name">${account.bank_name}</span>
            <span class="dot">•</span>
        ` : '';
        
        const descriptionHtml = account.description ? `
            <span class="description-text">${account.description}</span>
        ` : '';
        
        const creditLimitHtml = isCreditCard && creditLimit > 0 ? `
            <span class="credit-limit-text">
                <i class="fas fa-credit-card"></i> 
                Limite: <span class="limit-value">${creditLimitDisplay}</span>
            </span>
        ` : '';
        
        const inactiveBadge = !isActive ? '<span class="inactive-badge">Inativa</span>' : '';
        
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
                            <strong class="account-name">${account.name || 'Sem nome'}</strong>
                            <span class="type-badge ${account.type}">
                                ${formatAccountType(account.type)}
                            </span>
                            ${inactiveBadge}
                        </div>
                        <div class="info-line">
                            ${bankNameHtml}
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
                            ${descriptionHtml}
                            ${creditLimitHtml}
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
    } catch (error) {
        console.error('Erro ao criar HTML da conta:', account, error);
        return `<div class="message error">Erro ao carregar conta: ${error.message}</div>`;
    }
}

// Event Listeners
function attachAccountEventListeners() {
    // Botões de edição
    document.querySelectorAll('.action-btn.edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const accountItem = this.closest('.account-item');
            if (!accountItem) return;
            
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
            if (!accountItem) return;
            
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
            if (elements.creditCardFields) {
                elements.creditCardFields.style.display = isCreditCard ? 'block' : 'none';
            }
            
            // Atualizar campos obrigatórios
            const creditLimit = document.getElementById('credit-limit');
            const closingDay = document.getElementById('closing-day');
            const dueDay = document.getElementById('due-day');
            
            if (isCreditCard) {
                if (creditLimit) creditLimit.required = true;
                if (closingDay) closingDay.required = true;
                if (dueDay) dueDay.required = true;
            } else {
                if (creditLimit) creditLimit.required = false;
                if (closingDay) closingDay.required = false;
                if (dueDay) dueDay.required = false;
            }
            
            // Atualizar ícone baseado no tipo
            if (elements.iconPreview) {
                const icon = getIconForType(this.value);
                elements.iconPreview.className = `fas fa-${icon}`;
                const iconSelect = document.getElementById('account-icon');
                if (iconSelect) iconSelect.value = icon;
            }
        });
    }
    
    // Seletor de ícone
    const iconSelect = document.getElementById('account-icon');
    if (iconSelect && elements.iconPreview) {
        iconSelect.addEventListener('change', function() {
            elements.iconPreview.className = `fas fa-${this.value || 'wallet'}`;
        });
        
        // Definir valor inicial
        iconSelect.value = 'wallet';
        elements.iconPreview.className = 'fas fa-wallet';
    }
    
    // Submeter formulário
    if (elements.accountForm) {
        elements.accountForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (elements.submitBtn) {
                elements.submitBtn.disabled = true;
                elements.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
            }
            
            try {
                const formData = new FormData(this);
                const accountData = {
                    name: formData.get('name') || '',
                    type: formData.get('type') || '',
                    initial_balance: formData.get('initial_balance') || '0',
                    bank_name: formData.get('bank_name') || '',
                    description: formData.get('description') || '',
                    icon: formData.get('icon') || 'wallet',
                    color: formData.get('color') || '#3B82F6'
                };
                
                // Campos específicos de cartão de crédito
                if (accountData.type === 'CREDIT_CARD') {
                    accountData.credit_limit = formData.get('credit_limit') || '0';
                    accountData.closing_day = formData.get('closing_day') || '1';
                    accountData.due_day = formData.get('due_day') || '1';
                }
                
                console.log('Dados do formulário:', accountData);
                
                if (state.isEditing && state.currentEditId) {
                    await updateAccount(state.currentEditId, accountData);
                    resetForm();
                } else {
                    await createAccount(accountData);
                    resetForm();
                }
            } catch (error) {
                console.error('Erro ao salvar conta:', error);
                // A mensagem de erro já foi mostrada na função createAccount/updateAccount
            } finally {
                if (elements.submitBtn) {
                    elements.submitBtn.disabled = false;
                    if (state.isEditing) {
                        elements.submitBtn.innerHTML = '<i class="fas fa-save"></i> Salvar Alterações';
                    } else {
                        elements.submitBtn.innerHTML = '<i class="fas fa-plus"></i> Adicionar Conta';
                    }
                }
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
    if (elements.filters && elements.filters.length > 0) {
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
}

// Editar conta
function editAccount(account) {
    try {
        state.isEditing = true;
        state.currentEditId = account.id_account;
        
        // Atualizar formulário
        const accountIdField = document.getElementById('account-id');
        if (accountIdField) accountIdField.value = account.id_account;
        
        const nameField = document.getElementById('account-name');
        if (nameField) nameField.value = account.name || '';
        
        const typeField = document.getElementById('account-type');
        if (typeField) {
            typeField.value = account.type || '';
            // Disparar evento change para mostrar campos de cartão se necessário
            const event = new Event('change');
            typeField.dispatchEvent(event);
        }
        
        const balanceField = document.getElementById('initial-balance');
        if (balanceField) balanceField.value = account.initial_balance || 0;
        
        const bankField = document.getElementById('bank-name');
        if (bankField) bankField.value = account.bank_name || '';
        
        const descField = document.getElementById('account-description');
        if (descField) descField.value = account.description || '';
        
        const iconField = document.getElementById('account-icon');
        if (iconField) iconField.value = account.icon || 'wallet';
        
        const colorField = document.getElementById('account-color');
        if (colorField) colorField.value = account.color || '#3B82F6';
        
        // Atualizar ícone preview
        if (elements.iconPreview) {
            elements.iconPreview.className = `fas fa-${account.icon || 'wallet'}`;
        }
        
        // Campos de cartão de crédito
        if (account.type === 'CREDIT_CARD') {
            const limitField = document.getElementById('credit-limit');
            if (limitField) limitField.value = account.credit_limit || '';
            
            const closingField = document.getElementById('closing-day');
            if (closingField) closingField.value = account.closing_day || '';
            
            const dueField = document.getElementById('due-day');
            if (dueField) dueField.value = account.due_day || '';
        }
        
        // Atualizar interface
        if (elements.formTitle) {
            elements.formTitle.innerHTML = '<i class="fas fa-edit"></i> Editar Conta';
        }
        if (elements.submitBtn) {
            elements.submitBtn.innerHTML = '<i class="fas fa-save"></i> Salvar Alterações';
        }
        if (elements.cancelBtn) {
            elements.cancelBtn.style.display = 'block';
        }
        
        // Scroll para o formulário
        const formCard = document.querySelector('.account-form-card');
        if (formCard) {
            formCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    } catch (error) {
        console.error('Erro ao editar conta:', error);
        showMessage('Erro ao carregar dados da conta', 'error');
    }
}

function resetForm() {
    try {
        state.isEditing = false;
        state.currentEditId = null;
        
        // Resetar formulário
        if (elements.accountForm) {
            elements.accountForm.reset();
        }
        
        const accountIdField = document.getElementById('account-id');
        if (accountIdField) accountIdField.value = '';
        
        // Resetar tipo para padrão
        const typeField = document.getElementById('account-type');
        if (typeField) {
            typeField.value = '';
            const event = new Event('change');
            typeField.dispatchEvent(event);
        }
        
        if (elements.creditCardFields) {
            elements.creditCardFields.style.display = 'none';
        }
        
        // Resetar ícone
        if (elements.iconPreview) {
            elements.iconPreview.className = 'fas fa-wallet';
        }
        
        // Resetar seletor de ícone
        const iconSelect = document.getElementById('account-icon');
        if (iconSelect) iconSelect.value = 'wallet';
        
        // Atualizar interface
        if (elements.formTitle) {
            elements.formTitle.innerHTML = '<i class="fas fa-plus"></i> Adicionar Nova Conta';
        }
        if (elements.submitBtn) {
            elements.submitBtn.innerHTML = '<i class="fas fa-plus"></i> Adicionar Conta';
        }
        if (elements.cancelBtn) {
            elements.cancelBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Erro ao resetar formulário:', error);
    }
}

// Debug function
async function debugApi() {
    try {
        console.log('=== DEBUG API ===');
        const response = await fetch(`${API_BASE}/accounts/`);
        console.log('Status:', response.status);
        console.log('Headers:', Object.fromEntries(response.headers.entries()));
        
        const text = await response.text();
        console.log('Response text:', text);
        
        try {
            const json = JSON.parse(text);
            console.log('Parsed JSON:', json);
            console.log('Type:', typeof json);
            console.log('Is Array?', Array.isArray(json));
            
            if (json && typeof json === 'object') {
                console.log('Keys:', Object.keys(json));
            }
        } catch (e) {
            console.log('Not valid JSON');
        }
    } catch (error) {
        console.error('Debug error:', error);
    }
}

// Teste de conexão
async function testConnection() {
    try {
        const response = await fetch(`${API_BASE}/accounts/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        console.log('Teste de conexão:', response.status, response.statusText);
        return response.ok;
    } catch (error) {
        console.error('Erro no teste de conexão:', error);
        return false;
    }
}

// Inicialização
async function init() {
    console.log('Inicializando gerenciamento de contas...');
    
    // Verificar elementos do DOM
    console.log('Elementos do DOM:', {
        accountForm: !!elements.accountForm,
        accountsList: !!elements.accountsList,
        accountTypeSelect: !!elements.accountTypeSelect,
        creditCardFields: !!elements.creditCardFields,
        submitBtn: !!elements.submitBtn,
        filters: elements.filters?.length || 0,
        csrfToken: !!CSRF_TOKEN
    });
    
    // Testar conexão
    const connected = await testConnection();
    console.log('Conexão com API:', connected ? 'OK' : 'FALHA');
    
    if (!connected) {
        showMessage('Não foi possível conectar ao servidor. Verifique sua conexão.', 'error');
    }
    
    // Adicionar debug ao window
    window.debugAccounts = debugApi;
    
    // Configurar listeners
    setupFormListeners();
    setupFilters();
    
    // Carregar contas
    await fetchAccounts();
    
    console.log('Gerenciamento de contas inicializado');
}

// Iniciar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOM já carregado
    setTimeout(init, 100); // Pequeno delay para garantir que tudo está carregado
}