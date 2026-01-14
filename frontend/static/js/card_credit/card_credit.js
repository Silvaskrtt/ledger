// static/js/card_credit/card_credit.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.form-card');
    const submitBtn = document.querySelector('.btn-submit');
    const cardList = document.querySelector('.card-list');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Inicialização
    loadCreditCards();
    
    // Event Listeners
    if (submitBtn) {
        submitBtn.addEventListener('click', handleSubmit);
    }
    
    // Event listeners para botões de faturas
    if (cardList) {
        cardList.addEventListener('click', function(e) {
            // Botão de faturas
            if (e.target.closest('.bills') || e.target.classList.contains('fa-file-invoice-dollar')) {
                e.preventDefault();
                e.stopPropagation();
                const cardItem = e.target.closest('.card-item');
                if (cardItem) {
                    viewCardBills(cardItem);
                }
            }
            
            // Botões existentes de editar/excluir
            if (e.target.closest('.edit')) {
                handleEdit(e.target.closest('.card-item'));
            } else if (e.target.closest('.delete')) {
                handleDelete(e.target.closest('.card-item'));
            }
        });
    }
    
    // Fechar modais
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            closeAllModals();
        });
    });
    
    // Formulário de pagamento
    const payBillForm = document.getElementById('payBillForm');
    if (payBillForm) {
        payBillForm.addEventListener('submit', processPayment);
    }
    
    // Função para abrir modal de visualizar faturas
    async function viewCardBills(cardItem) {
        const cardId = cardItem.dataset.id;
        
        try {
            const response = await fetch(`/api/credit-cards/${cardId}/bills/`);
            const data = await response.json();
            
            if (data.success) {
                showBillsModal(data.bills, cardId);
            } else {
                showToast(data.error || 'Erro ao carregar faturas', 'error');
            }
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro ao carregar faturas', 'error');
        }
    }
    
    // Função para carregar cartões
    async function loadCreditCards() {
        try {
            const response = await fetch('/api/credit-cards/');
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao carregar cartões');
            }
            
            const data = await response.json();
            
            // Verificar se é um array
            if (Array.isArray(data)) {
                renderCards(data);
            } else if (data && typeof data === 'object') {
                // Se for um objeto, verificar se tem resultados
                if (data.results) {
                    renderCards(data.results);
                } else {
                    // Tentar extrair array do objeto
                    const cardsArray = Object.values(data).filter(item => 
                        item && typeof item === 'object' && item.account
                    );
                    if (cardsArray.length > 0) {
                        renderCards(cardsArray);
                    } else {
                        renderCards([]);
                    }
                }
            } else {
                renderCards([]);
            }
            
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro ao carregar cartões: ' + error.message, 'error');
            
            // Mostrar estado de erro
            if (cardList) {
                cardList.innerHTML = `
                    <div class="empty-state error">
                        <p>❌ Erro ao carregar cartões</p>
                        <p>${error.message}</p>
                        <button class="retry-btn" onclick="location.reload()">Tentar novamente</button>
                    </div>
                `;
            }
        }
    }

    // Função para mostrar modal com faturas
    function showBillsModal(bills, cardId) {
        const modal = document.getElementById('viewBillsModal');
        const billsList = document.getElementById('billsList');
        
        if (bills.length === 0) {
            billsList.innerHTML = `
                <div class="empty-state">
                    <p>Nenhuma fatura encontrada para este cartão.</p>
                    <p>As faturas são geradas automaticamente com base nas transações.</p>
                </div>
            `;
        } else {
            let html = '<div class="bills-container">';
            
            bills.forEach(bill => {
                const pendingAmount = bill.pending_amount;
                const statusClass = {
                    'OPEN': 'status-open',
                    'CLOSED': 'status-closed',
                    'PAID': 'status-paid',
                    'OVERDUE': 'status-overdue'
                }[bill.status] || 'status-open';
                
                html += `
                    <div class="bill-item ${statusClass}" data-bill-id="${bill.id}">
                        <div class="bill-header">
                            <h4>Fatura ${bill.end_date}</h4>
                            <span class="bill-status ${statusClass}">${bill.status_display}</span>
                        </div>
                        
                        <div class="bill-details">
                            <div class="detail">
                                <span class="label">Período:</span>
                                <span class="value">${bill.start_date} a ${bill.end_date}</span>
                            </div>
                            <div class="detail">
                                <span class="label">Vencimento:</span>
                                <span class="value ${bill.days_until_due < 0 ? 'overdue' : ''}">
                                    ${bill.due_date} (${bill.days_until_due >= 0 ? `em ${bill.days_until_due} dias` : 'vencida'})
                                </span>
                            </div>
                            <div class="detail">
                                <span class="label">Total:</span>
                                <span class="value">R$ ${bill.total_amount.toFixed(2)}</span>
                            </div>
                            <div class="detail">
                                <span class="label">Pago:</span>
                                <span class="value paid">R$ ${bill.paid_amount.toFixed(2)}</span>
                            </div>
                            <div class="detail">
                                <span class="label">Pendente:</span>
                                <span class="value pending">R$ ${pendingAmount.toFixed(2)}</span>
                            </div>
                            <div class="detail">
                                <span class="label">Transações:</span>
                                <span class="value">${bill.transactions_count}</span>
                            </div>
                        </div>
                        
                        ${pendingAmount > 0 ? `
                            <div class="bill-actions">
                                <button class="btn-pay-bill" data-bill-id="${bill.id}" 
                                        data-card-id="${cardId}" 
                                        data-amount="${pendingAmount}">
                                    <i class="fas fa-credit-card"></i> Pagar Fatura
                                </button>
                                <button class="btn-pay-partial" data-bill-id="${bill.id}" 
                                        data-card-id="${cardId}">
                                    <i class="fas fa-money-bill-wave"></i> Pagar Parcial
                                </button>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            html += '</div>';
            billsList.innerHTML = html;
            
            // Adicionar listeners aos botões de pagamento
            document.querySelectorAll('.btn-pay-bill').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const billId = e.currentTarget.dataset.billId;
                    const cardId = e.currentTarget.dataset.cardId;
                    const amount = parseFloat(e.currentTarget.dataset.amount);
                    openPayBillModal(billId, cardId, amount);
                });
            });
            
            document.querySelectorAll('.btn-pay-partial').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const billId = e.currentTarget.dataset.billId;
                    const cardId = e.currentTarget.dataset.cardId;
                    openPayBillModal(billId, cardId, null); // null para permitir edição do valor
                });
            });
        }
        
        // FECHAR QUALQUER OUTRO MODAL ABERTO ANTES DE ABRIR ESTE
        closeAllModals();
        
        // AGORA ABRIR O MODAL DE FATURAS
        modal.classList.add('active');
    }

    // Função para abrir modal de pagamento
    async function openPayBillModal(billId, cardId, amount = null) {
        const modal = document.getElementById('payBillModal');
        const billIdInput = document.getElementById('billId');
        const creditCardIdInput = document.getElementById('creditCardId');
        const paymentAmountInput = document.getElementById('paymentAmount');
        const paymentAccountSelect = document.getElementById('paymentAccount');
        const billInfo = document.getElementById('billInfo');
        
        // Preencher campos ocultos
        billIdInput.value = billId;
        creditCardIdInput.value = cardId;
        
        // Buscar informações da fatura
        try {
            const response = await fetch(`/api/credit-cards/${cardId}/bills/`);
            const data = await response.json();
            
            if (data.success) {
                const bill = data.bills.find(b => b.id === billId);
                if (bill) {
                    billInfo.innerHTML = `
                        <div class="bill-summary">
                            <h4>Fatura ${bill.end_date}</h4>
                            <p>Período: ${bill.start_date} a ${bill.end_date}</p>
                            <p>Vencimento: ${bill.due_date}</p>
                            <p>Total: <strong>R$ ${bill.total_amount.toFixed(2)}</strong></p>
                            <p>Pago: <strong>R$ ${bill.paid_amount.toFixed(2)}</strong></p>
                            <p>Pendente: <strong class="pending">R$ ${bill.pending_amount.toFixed(2)}</strong></p>
                        </div>
                    `;
                    
                    // Definir valor do pagamento
                    if (amount) {
                        paymentAmountInput.value = amount.toFixed(2);
                        paymentAmountInput.max = bill.pending_amount;
                    } else {
                        paymentAmountInput.value = bill.pending_amount.toFixed(2);
                        paymentAmountInput.max = bill.pending_amount;
                    }
                }
            }
        } catch (error) {
            console.error('Erro ao carregar fatura:', error);
        }
        
        // Carregar contas de pagamento
        try {
            const response = await fetch('/api/accounts/payment-accounts/');
            const data = await response.json();
            
            if (data.success) {
                paymentAccountSelect.innerHTML = '<option value="">Selecione uma conta</option>';
                
                data.accounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;
                    option.textContent = `${account.name} (${account.type_display}) - R$ ${account.balance.toFixed(2)}`;
                    option.dataset.balance = account.balance;
                    paymentAccountSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar contas:', error);
        }
        
        // FECHAR QUALQUER OUTRO MODAL ABERTO ANTES DE ABRIR ESTE
        closeAllModals();
        
        // AGORA ABRIR O MODAL DE PAGAMENTO
        modal.classList.add('active');
        
        // Focar no primeiro campo do formulário
        setTimeout(() => {
            if (amount === null) {
                paymentAmountInput.focus();
            } else {
                paymentAccountSelect.focus();
            }
        }, 100);
    }

    // Função para atualizar resumo do patrimônio
    function updatePatrimonySummary(patrimony) {
        // Atualizar elementos na página se existirem
        const elements = {
            'totalPatrimony': document.getElementById('totalPatrimony'),
            'creditCardDebt': document.getElementById('creditCardDebt'),
            'availablePatrimony': document.getElementById('availablePatrimony')
        };
        
        if (elements.totalPatrimony) {
            elements.totalPatrimony.textContent = `R$ ${patrimony.total_patrimony.toFixed(2)}`;
        }
        
        if (elements.creditCardDebt) {
            elements.creditCardDebt.textContent = `R$ ${patrimony.credit_card_debt_abs.toFixed(2)}`;
        }
        
        if (elements.availablePatrimony) {
            elements.availablePatrimony.textContent = `R$ ${(patrimony.total_patrimony + patrimony.credit_card_debt_abs).toFixed(2)}`;
        }
    }

    // Função para processar pagamento
    async function processPayment(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitBtn = form.querySelector('#payBillBtn');
        const originalText = submitBtn.textContent;
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processando...';
            
            const formData = {
                bill_id: document.getElementById('billId').value,
                payment_account: document.getElementById('paymentAccount').value,
                amount: parseFloat(document.getElementById('paymentAmount').value),
                notes: document.getElementById('paymentNotes').value,
                create_transaction: document.getElementById('createTransaction').checked
            };
            
            // Validações
            if (!formData.payment_account) {
                throw new Error('Selecione uma conta para pagamento');
            }
            
            if (formData.amount <= 0) {
                throw new Error('Valor do pagamento deve ser maior que zero');
            }
            
            const response = await fetch('/api/credit-cards/pay-bill/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || ''
                },
                body: JSON.stringify(formData)
            });
            
            let result;
            try {
                result = await response.json();
            } catch (parseError) {
                console.error('Erro ao parsear resposta:', parseError);
                throw new Error('Resposta do servidor inválida');
            }
            
            if (response.ok) {
                if (result.success) {
                    showToast(result.message, 'success');
                    
                    // Fechar modais
                    closeAllModals();
                    
                    // Recarregar dados
                    await loadCreditCards();
                    
                    // Atualizar patrimônio se necessário
                    if (result.patrimony) {
                        updatePatrimonySummary(result.patrimony);
                    }
                } else {
                    throw new Error(result.error || 'Erro ao processar pagamento');
                }
            } else {
                // Se a resposta não é OK, tentar extrair erro
                if (result && result.detail) {
                    throw new Error(result.detail);
                } else if (result && result.error) {
                    throw new Error(result.error);
                } else {
                    throw new Error(`Erro do servidor: ${response.status} ${response.statusText}`);
                }
            }
            
        } catch (error) {
            console.error('Erro:', error);
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
    
    // Função para renderizar cartões
    function renderCards(cards) {
        if (!cardList) return;
        
        // Verificar se cards é um array
        if (!Array.isArray(cards)) {
            console.error('cards não é um array:', cards);
            cards = [];
        }
        
        cardList.innerHTML = '';
        
        if (cards.length === 0) {
            cardList.innerHTML = `
                <div class="empty-state">
                    <p>📭 Nenhum cartão cadastrado ainda.</p>
                    <p>Adicione seu primeiro cartão!</p>
                </div>
            `;
            return;
        }
        
        cards.forEach(card => {
            try {
                const cardElement = createCardElement(card);
                if (cardElement) {
                    cardList.appendChild(cardElement);
                }
            } catch (error) {
                console.error('Erro ao criar elemento do cartão:', card, error);
            }
        });
    }
    
    // Criar elemento HTML do cartão
    function createCardElement(card) {
        // Validar dados do cartão
        if (!card || !card.account) {
            console.error('Dados inválidos do cartão:', card);
            return null;
        }
        
        const div = document.createElement('div');
        div.className = 'card-item';
        div.dataset.id = card.account;
        
        const balance = parseFloat(card.balance || 0);
        const creditLimit = parseFloat(card.credit_limit || 0);
        const balanceClass = balance < 0 ? 'negative' : 'positive';
        const balanceText = balance < 0 
            ? `-R$ ${Math.abs(balance).toFixed(2)}` 
            : `R$ ${balance.toFixed(2)}`;
        
        // Calcular crédito disponível
        const availableCredit = creditLimit + balance; // balance é negativo para cartões
        const availableCreditText = `R$ ${Math.max(0, availableCredit).toFixed(2)}`;
        
        // Formatar datas de fechamento e vencimento
        const closingDay = card.closing_day || '--';
        const dueDay = card.due_day || '--';
        
        // AGORA INCLUÍMOS O BOTÃO DE FATURAS
        div.innerHTML = `
            <div class="card-info">
                <div class="card-header">
                    <strong>${card.name || 'Cartão sem nome'}</strong>
                    <span class="bank-badge">${card.bank_name || 'Sem banco'}</span>
                </div>
                <div class="card-details">
                    <div class="detail">
                        <span class="label">Limite:</span>
                        <span class="value">R$ ${creditLimit.toFixed(2)}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Disponível:</span>
                        <span class="value positive">${availableCreditText}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Fatura:</span>
                        <span class="value ${balanceClass}">${balanceText}</span>
                    </div>
                    <div class="detail-group">
                        <div class="detail small">
                            <span class="label">Fechamento:</span>
                            <span class="value">dia ${closingDay}</span>
                        </div>
                        <div class="detail small">
                            <span class="label">Vencimento:</span>
                            <span class="value">dia ${dueDay}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card-actions">
                <button class="icon-btn bills" title="Ver Faturas">
                    <i class="fas fa-file-invoice-dollar"></i>
                </button>
                <button class="icon-btn edit" title="Editar">✎</button>
                <button class="icon-btn delete" title="Excluir">🗑</button>
            </div>
        `;
        
        return div;
    }
    
    // Função para submeter formulário
    async function handleSubmit() {
        if (!submitBtn) return;
        
        const formData = collectFormData();
        
        if (!validateForm(formData)) {
            return;
        }
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Salvando...';
            
            const method = formData.id ? 'PUT' : 'POST';
            const url = formData.id 
                ? `/api/credit-cards/${formData.id}/`
                : '/api/credit-cards/';
            
            // Preparar dados para envio
            const dataToSend = {
                name: formData.name,
                bank_name: formData.bank_name || '',
                credit_limit: formData.credit_limit,
                closing_day: formData.closing_day,
                due_day: formData.due_day
            };
            
            console.log('Enviando dados:', dataToSend);
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || ''
                },
                body: JSON.stringify(dataToSend)
            });
            
            const responseData = await response.json();
            
            if (!response.ok) {
                let errorMessage = 'Erro ao salvar cartão';
                if (responseData && typeof responseData === 'object') {
                    // Extrair mensagens de erro do serializer
                    const errors = [];
                    for (const [field, messages] of Object.entries(responseData)) {
                        if (Array.isArray(messages)) {
                            errors.push(...messages);
                        } else if (typeof messages === 'string') {
                            errors.push(messages);
                        }
                    }
                    if (errors.length > 0) {
                        errorMessage = errors.join(', ');
                    }
                }
                throw new Error(errorMessage);
            }
            
            showToast(formData.id ? 'Cartão atualizado!' : 'Cartão adicionado!', 'success');
            resetForm();
            await loadCreditCards();
            
        } catch (error) {
            console.error('Erro:', error);
            showToast(error.message || 'Erro ao salvar cartão', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = formData.id ? 'Atualizar Cartão' : '+ Adicionar Cartão';
            }
        }
    }
    
    // Coletar dados do formulário
    function collectFormData() {
        const data = {
            name: document.getElementById('card-name')?.value || '',
            bank_name: document.getElementById('bank-name')?.value || '',
            credit_limit: document.getElementById('credit-limit')?.value || '0',
            closing_day: document.getElementById('closing-day')?.value || '1',
            due_day: document.getElementById('due-day')?.value || '1'
        };
        
        // Verificar se está editando
        const form = document.querySelector('.form-card');
        if (form && form.dataset.editId) {
            data.id = form.dataset.editId;
        }
        
        // Converter valores
        data.credit_limit = parseFloat(data.credit_limit) || 0;
        data.closing_day = parseInt(data.closing_day) || 1;
        data.due_day = parseInt(data.due_day) || 1;
        
        return data;
    }
    
    // Validar formulário
    function validateForm(data) {
        const errors = [];
        
        if (!data.name || data.name.trim() === '') {
            errors.push('Nome do cartão é obrigatório');
        }
        
        if (data.credit_limit < 0) {
            errors.push('Limite de crédito não pode ser negativo');
        }
        
        if (data.closing_day < 1 || data.closing_day > 31) {
            errors.push('Dia de fechamento deve ser entre 1 e 31');
        }
        
        if (data.due_day < 1 || data.due_day > 31) {
            errors.push('Dia de vencimento deve ser entre 1 e 31');
        }
        
        if (errors.length > 0) {
            showToast(errors.join(', '), 'error');
            return false;
        }
        
        return true;
    }
    
    // Resetar formulário
    function resetForm() {
        // Resetar inputs
        const inputs = [
            document.getElementById('card-name'),
            document.getElementById('bank-name'),
            document.getElementById('credit-limit'),
            document.getElementById('closing-day'),
            document.getElementById('due-day')
        ];
        
        inputs.forEach((input, index) => {
            if (input) {
                if (index === 0 || index === 1) {
                    input.value = ''; // Nome e banco
                } else if (index === 2) {
                    input.value = ''; // Limite
                } else {
                    input.value = '1'; // Dias padrão
                }
            }
        });
        
        // Remover estado de edição
        const form = document.querySelector('.form-card');
        if (form && form.dataset.editId) {
            delete form.dataset.editId;
        }
        
        // Resetar botão
        if (submitBtn) {
            submitBtn.textContent = '+ Adicionar Cartão';
        }
    }
    
    // Editar cartão
    async function handleEdit(cardItem) {
        if (!cardItem) return;
        
        const cardId = cardItem.dataset.id;
        
        try {
            const response = await fetch(`/api/credit-cards/${cardId}/`);
            if (!response.ok) {
                throw new Error('Erro ao buscar dados do cartão');
            }
            
            const card = await response.json();
            
            // Preencher formulário
            document.getElementById('card-name').value = card.name || '';
            document.getElementById('bank-name').value = card.bank_name || '';
            document.getElementById('credit-limit').value = card.credit_limit || '';
            document.getElementById('closing-day').value = card.closing_day || '1';
            document.getElementById('due-day').value = card.due_day || '1';
            
            // Alterar botão e marcar como edição
            if (submitBtn) {
                submitBtn.textContent = 'Atualizar Cartão';
            }
            
            const form = document.querySelector('.form-card');
            if (form) {
                form.dataset.editId = cardId;
            }
            
            // Scroll para o formulário
            form?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
        } catch (error) {
            console.error('Erro ao buscar cartão:', error);
            showToast('Erro ao carregar dados do cartão', 'error');
        }
    }
    
    // Excluir cartão
    async function handleDelete(cardItem) {
        if (!cardItem) return;
        
        const cardId = cardItem.dataset.id;
        const cardName = cardItem.querySelector('strong')?.textContent || 'este cartão';
        
        if (!confirm(`Tem certeza que deseja excluir o cartão "${cardName}"?\n\nEsta ação não pode ser desfeita.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/credit-cards/${cardId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken || ''
                }
            });
            
            if (response.ok) {
                showToast('Cartão excluído com sucesso', 'success');
                await loadCreditCards();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao excluir cartão');
            }
        } catch (error) {
            console.error('Erro:', error);
            showToast(error.message || 'Erro ao excluir cartão', 'error');
        }
    }
    
    // Função para fechar todos os modais
    function closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    // Mostrar notificação
    function showToast(message, type = 'info') {
        // Remover toast anterior
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();
        
        // Criar novo toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Adicionar ícone baseado no tipo
        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Mostrar com animação
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remover após 4 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }
});