// static/js/card_credit/card_credit.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.form-card');
    const submitBtn = document.querySelector('.btn-submit');
    const cardList = document.querySelector('.card-list');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Inicialização
    loadCreditCards();
    
    // Event Listeners
    if (submitBtn) {
        submitBtn.addEventListener('click', handleSubmit);
    }
    
    // Delegated events for edit/delete buttons
    cardList.addEventListener('click', function(e) {
        if (e.target.closest('.edit')) {
            handleEdit(e.target.closest('.card-item'));
        } else if (e.target.closest('.delete')) {
            handleDelete(e.target.closest('.card-item'));
        }
    });
    
    // Função para carregar cartões
    async function loadCreditCards() {
        try {
            const response = await fetch('/api/credit-cards/');
            if (!response.ok) throw new Error('Erro ao carregar cartões');
            
            const cards = await response.json();
            renderCards(cards);
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro ao carregar cartões', 'error');
        }
    }
    
    // Função para renderizar cartões
    function renderCards(cards) {
        cardList.innerHTML = '';
        
        if (cards.length === 0) {
            cardList.innerHTML = `
                <div class="empty-state">
                    <p>Nenhum cartão cadastrado ainda.</p>
                    <p>Adicione seu primeiro cartão!</p>
                </div>
            `;
            return;
        }
        
        cards.forEach(card => {
            const cardElement = createCardElement(card);
            cardList.appendChild(cardElement);
        });
    }
    
    // Criar elemento HTML do cartão
    function createCardElement(card) {
        const div = document.createElement('div');
        div.className = 'card-item';
        div.dataset.id = card.id_account;
        
        const balanceClass = card.balance < 0 ? 'negative' : 'positive';
        const balanceText = card.balance < 0 ? `-R$ ${Math.abs(card.balance).toFixed(2)}` : `R$ ${card.balance.toFixed(2)}`;
        
        div.innerHTML = `
            <div class="card-info">
                <div class="card-header">
                    <strong>${card.name}</strong>
                    <span class="bank-badge">${card.bank_name || 'Sem banco'}</span>
                </div>
                <div class="card-details">
                    <div class="detail">
                        <span class="label">Limite:</span>
                        <span class="value">R$ ${parseFloat(card.credit_limit || 0).toFixed(2)}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Fatura atual:</span>
                        <span class="value ${balanceClass}">${balanceText}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Fechamento:</span>
                        <span class="value">dia ${card.closing_day || '--'}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Vencimento:</span>
                        <span class="value">dia ${card.due_day || '--'}</span>
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
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || JSON.stringify(errorData));
            }
            
            showToast(formData.id ? 'Cartão atualizado!' : 'Cartão adicionado!', 'success');
            resetForm();
            loadCreditCards();
            
        } catch (error) {
            console.error('Erro:', error);
            showToast(error.message || 'Erro ao salvar cartão', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = formData.id ? 'Atualizar Cartão' : '+ Adicionar Cartão';
        }
    }
    
    // Coletar dados do formulário
    function collectFormData() {
        const fields = {
            name: document.querySelector('input[name="name"]'),
            bank_name: document.querySelector('input[name="bank_name"]'),
            credit_limit: document.querySelector('input[name="credit_limit"]'),
            closing_day: document.querySelector('input[name="closing_day"]'),
            due_day: document.querySelector('input[name="due_day"]')
        };
        
        const data = {};
        for (const [key, element] of Object.entries(fields)) {
            if (element) {
                data[key] = element.value;
            }
        }
        
        // Converter valores
        if (data.credit_limit && data.credit_limit !== '') {
            data.credit_limit = parseFloat(data.credit_limit);
        } else {
            data.credit_limit = 0;  // Valor padrão
        }
        
        if (data.closing_day && data.closing_day !== '') {
            data.closing_day = parseInt(data.closing_day);
        }
        
        if (data.due_day && data.due_day !== '') {
            data.due_day = parseInt(data.due_day);
        }
        
        return data;
    }
    
    // Validar formulário
    function validateForm(data) {
        const errors = [];
        
        if (!data.name || data.name.trim() === '') {
            errors.push('Nome do cartão é obrigatório');
        }
        
        if (data.credit_limit !== undefined && data.credit_limit < 0) {
            errors.push('Limite de crédito não pode ser negativo');
        }
        
        if (data.closing_day !== undefined && (data.closing_day < 1 || data.closing_day > 31)) {
            errors.push('Dia de fechamento deve ser entre 1 e 31');
        }
        
        if (data.due_day !== undefined && (data.due_day < 1 || data.due_day > 31)) {
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
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            if (input.name === 'closing_day' || input.name === 'due_day') {
                input.value = '1';  // Valor padrão
            } else if (input.name === 'credit_limit') {
                input.value = '';
            } else if (input.name === 'name' || input.name === 'bank_name') {
                input.value = '';
            }
        });
        
        submitBtn.textContent = '+ Adicionar Cartão';
        if (form.dataset.editId) {
            delete form.dataset.editId;
        }
    }
    
    // Editar cartão
    function handleEdit(cardItem) {
        const cardId = cardItem.dataset.id;
        
        // Buscar dados do cartão
        fetch(`/api/credit-cards/${cardId}/`)
            .then(response => response.json())
            .then(card => {
                // Preencher formulário
                const fields = {
                    name: card.name,
                    bank_name: card.bank_name || '',
                    credit_limit: card.credit_limit || '',
                    closing_day: card.closing_day || '1',
                    due_day: card.due_day || '1'
                };
                
                // Usar os names dos inputs
                for (const [key, value] of Object.entries(fields)) {
                    const input = document.querySelector(`input[name="${key}"]`);
                    if (input) input.value = value;
                }
                
                // Alterar botão
                submitBtn.textContent = 'Atualizar Cartão';
                form.dataset.editId = cardId;
                
                // Scroll para o formulário
                form.scrollIntoView({ behavior: 'smooth' });
            })
            .catch(error => {
                console.error('Erro ao buscar cartão:', error);
                showToast('Erro ao carregar dados do cartão', 'error');
            });
    }
    
    // Excluir cartão
    async function handleDelete(cardItem) {
        const cardId = cardItem.dataset.id;
        const cardName = cardItem.querySelector('strong').textContent;
        
        if (!confirm(`Tem certeza que deseja excluir o cartão "${cardName}"?`)) {
            return;
        }
        
        try {
            // CORRIGIDO: URL correta
            const response = await fetch(`/api/credit-cards/${cardId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (response.ok) {
                showToast('Cartão excluído com sucesso', 'success');
                loadCreditCards();
            } else {
                throw new Error('Erro ao excluir cartão');
            }
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro ao excluir cartão', 'error');
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
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Mostrar
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remover após 3 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});