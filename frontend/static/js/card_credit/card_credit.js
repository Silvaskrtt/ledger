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
    
    // Delegated events for edit/delete buttons
    if (cardList) {
        cardList.addEventListener('click', function(e) {
            if (e.target.closest('.edit')) {
                handleEdit(e.target.closest('.card-item'));
            } else if (e.target.closest('.delete')) {
                handleDelete(e.target.closest('.card-item'));
            }
        });
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
                            <span class="value">dia ${card.closing_day || '--'}</span>
                        </div>
                        <div class="detail small">
                            <span class="label">Vencimento:</span>
                            <span class="value">dia ${card.due_day || '--'}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card-actions">
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