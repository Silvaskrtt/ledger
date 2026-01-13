// frontend/static/js/budget/budget.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Budget module initializing...');
    
    // 1. INICIALIZAÇÃO DE ELEMENTOS
    const modal = document.getElementById('budgetModal');
    const openBtns = document.querySelectorAll('#openBudgetModal');
    const form = document.getElementById('budgetForm');
    
    // Debug de elementos
    console.log('📋 Elementos encontrados:', {
        modal: !!modal,
        openBtns: openBtns.length,
        form: !!form
    });
    
    // 2. FUNÇÕES AUXILIARES
    function getCurrentMonth() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        return `${year}-${month}`;
    }
    
    function isValidMonth(monthStr) {
        if (!monthStr) return false;
        const regex = /^\d{4}-(0[1-9]|1[0-2])$/;
        return regex.test(monthStr);
    }
    
    function showNotification(message, type = 'info') {
        // Remover notificação existente
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        // Cores por tipo
        const colors = {
            success: '#4CAF50',
            error: '#f44336',
            warning: '#FF9800',
            info: '#2196F3'
        };
        
        // Criar notificação
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.innerHTML = `
            <div class="notification-content" style="
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                z-index: 10000;
                background: ${colors[type] || colors.info};
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    // 3. FUNÇÕES DE MODAL
    function openModal() {
        console.log('📂 Abrindo modal...');
        
        if (!modal) {
            console.error('❌ Modal não encontrado!');
            showNotification('Erro: Não foi possível abrir o formulário', 'error');
            return;
        }
        
        // Mostrar modal
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Resetar formulário
        if (form) {
            form.reset();
            delete form.dataset.editId;
            
            // Atualizar título
            const modalTitle = modal.querySelector('h3');
            if (modalTitle) {
                modalTitle.textContent = 'Nova Meta de Orçamento';
            }
            
            // Atualizar texto do botão
            const submitText = form.querySelector('.btn-text');
            if (submitText) {
                submitText.textContent = 'Salvar Meta';
            }
        }
        
        // Preencher mês atual
        const monthInput = document.getElementById('month');
        if (monthInput) {
            // Verificar se o valor atual é válido
            if (!monthInput.value || !isValidMonth(monthInput.value)) {
                monthInput.value = getCurrentMonth();
            }
        }
        
        // Focar no primeiro campo
        setTimeout(() => {
            const firstField = form?.querySelector('input, select, textarea');
            if (firstField) {
                firstField.focus();
                
                // Se for select com TomSelect, abrir dropdown
                if (firstField.tagName === 'SELECT' && firstField.classList.contains('tom-select')) {
                    const instance = window.tomSelectManager?.getInstance(firstField.id);
                    if (instance) {
                        setTimeout(() => instance.open(), 50);
                    }
                }
            }
        }, 100);
        
        console.log('✅ Modal aberto com sucesso');
    }
    
    function closeModal() {
        console.log('📂 Fechando modal...');
        
        if (!modal) {
            console.error('❌ Modal não encontrado para fechar');
            return;
        }
        
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Não resetar o formulário aqui para evitar conflitos com TomSelect
        console.log('✅ Modal fechado');
    }
    
    // 4. FUNÇÕES DE CRUD
    async function loadBudgets() {
        try {
            console.log('📊 Carregando orçamentos...');
            const response = await fetch('/api/budget-overview/');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('📊 Orçamentos carregados:', result);
            
            if (result.success) {
                // Opcional: atualizar interface dinamicamente
                updateBudgetDisplay(result.data);
            }
            
        } catch (error) {
            console.error('❌ Erro ao carregar orçamentos:', error);
        }
    }
    
    function updateBudgetDisplay(data) {
        // Esta função pode ser usada para atualização dinâmica
        // sem recarregar a página
        console.log('🔄 Atualizando display com:', data);
        // Implemente conforme necessário
    }
    
    async function editBudget(limitId) {
        try {
            console.log('✏️ Editando orçamento ID:', limitId);
            
            const response = await fetch(`/api/budget-category-limits/${limitId}/`);
            if (!response.ok) throw new Error('Erro ao carregar dados');
            
            const data = await response.json();
            console.log('📝 Dados para edição:', data);
            
            // Abrir modal primeiro
            openModal();
            
            // Preencher formulário após o modal estar visível
            setTimeout(() => {
                if (!form) return;
                
                // Preencher campos
                const categorySelect = document.getElementById('category');
                const amountInput = document.getElementById('limit_amount');
                const monthInput = document.getElementById('month');
                
                if (categorySelect && data.category) {
                    // Usar TomSelectManager para definir valor
                    if (window.tomSelectManager) {
                        window.tomSelectManager.setValue('category', data.category);
                    } else {
                        categorySelect.value = data.category;
                    }
                }
                
                if (amountInput && data.limit_amount) {
                    amountInput.value = parseFloat(data.limit_amount).toFixed(2);
                }
                
                if (monthInput && data.month) {
                    monthInput.value = data.month;
                }
                
                // Modificar formulário para modo edição
                form.dataset.editId = limitId;
                
                // Atualizar título
                const modalTitle = modal?.querySelector('h3');
                if (modalTitle) {
                    modalTitle.textContent = 'Editar Meta de Orçamento';
                }
                
                // Atualizar texto do botão
                const submitText = form.querySelector('.btn-text');
                if (submitText) {
                    submitText.textContent = 'Atualizar Meta';
                }
                
            }, 300);
            
        } catch (error) {
            console.error('❌ Erro ao editar orçamento:', error);
            showNotification('Erro ao carregar dados para edição', 'error');
        }
    }
    
    async function deleteBudget(limitId) {
        if (!confirm('Tem certeza que deseja excluir esta meta?')) {
            return;
        }
        
        try {
            console.log('🗑️ Excluindo orçamento ID:', limitId);
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (!csrfToken) {
                throw new Error('Token de segurança não encontrado');
            }
            
            const response = await fetch(`/api/budget-category-limits/${limitId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                showNotification('✅ Meta excluída com sucesso!', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                throw new Error('Erro ao excluir meta');
            }
            
        } catch (error) {
            console.error('❌ Erro ao excluir orçamento:', error);
            showNotification(error.message, 'error');
        }
    }
    
    // 5. EVENT LISTENERS
    // Botões para abrir modal
    openBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            openModal();
        });
    });
    
    // Botões de fechar
    const closeBtn = document.getElementById('closeBudgetModal');
    const cancelBtn = document.getElementById('cancelBudgetModal');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }
    
    // Fechar modal clicando fora
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // Fechar com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
            closeModal();
        }
    });
    
    // Event delegation para botões dinâmicos
    document.addEventListener('click', function(e) {
        // Editar
        const editBtn = e.target.closest('.edit-budget');
        if (editBtn) {
            e.preventDefault();
            const limitId = editBtn.dataset.id;
            if (limitId) editBudget(limitId);
        }
        
        // Excluir
        const deleteBtn = e.target.closest('.delete-budget');
        if (deleteBtn) {
            e.preventDefault();
            const limitId = deleteBtn.dataset.id;
            if (limitId) deleteBudget(limitId);
        }
    });
    
    // Submissão do formulário
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('📤 Enviando formulário...');
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Mostrar estado de loading
            submitBtn.textContent = 'Salvando...';
            submitBtn.disabled = true;
            
            try {
                // 1. Preparar dados
                const formData = new FormData(form);
                let data = {
                    category: formData.get('category'),
                    limit_amount: formData.get('limit_amount'),
                    month: formData.get('month') || ''
                };
                
                console.log('📄 Dados do formulário:', data);
                
                // 2. Validações
                if (!data.category || data.category === '') {
                    throw new Error('❌ Selecione uma categoria');
                }
                
                const amount = parseFloat(data.limit_amount);
                if (isNaN(amount) || amount <= 0) {
                    throw new Error('❌ Valor da meta deve ser maior que zero');
                }
                
                // Formatar valor com 2 casas decimais
                data.limit_amount = amount.toFixed(2);
                
                // Validar mês se fornecido
                if (data.month && !isValidMonth(data.month)) {
                    console.warn('⚠️ Mês inválido, usando mês atual');
                    data.month = getCurrentMonth();
                }
                
                // 3. Obter CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                if (!csrfToken) {
                    throw new Error('❌ Token de segurança não encontrado');
                }
                
                // 4. Determinar URL e método
                const isEdit = form.dataset.editId;
                const url = isEdit 
                    ? `/api/budget-category-limits/${form.dataset.editId}/`
                    : '/api/create-budget-limit/';
                
                const method = isEdit ? 'PUT' : 'POST';
                
                // 5. Enviar requisição
                console.log(`📡 Enviando ${method} para: ${url}`, data);
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(data)
                });
                
                // 6. Processar resposta
                let result;
                try {
                    result = await response.json();
                } catch (parseError) {
                    console.error('❌ Erro ao parsear resposta:', parseError);
                    throw new Error('Resposta inválida do servidor');
                }
                
                console.log('📥 Resposta do servidor:', result);
                
                if (response.ok && (result.success || result.id)) {
                    const message = isEdit 
                        ? '✅ Meta atualizada com sucesso!' 
                        : '✅ Meta criada com sucesso!';
                    
                    showNotification(message, 'success');
                    
                    // Fechar modal e recarregar após delay
                    setTimeout(() => {
                        closeModal();
                        location.reload();
                    }, 1500);
                    
                } else {
                    const errorMsg = result.error || result.detail || result.message || 'Erro desconhecido';
                    throw new Error(`❌ ${errorMsg}`);
                }
                
            } catch (error) {
                console.error('❌ Erro no envio:', error);
                showNotification(error.message, 'error');
                
                // Restaurar botão
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // 6. INICIALIZAÇÃO
    // Carregar dados iniciais
    loadBudgets();
    
    // Adicionar estilos CSS para animações
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    console.log('✅ Budget module initialized successfully');
});

// Funções globais (opcional, se necessário fora do DOMContentLoaded)
window.BudgetManager = {
    openModal: () => {
        const event = new Event('budgetModalOpen');
        document.dispatchEvent(event);
    },
    closeModal: () => {
        const event = new Event('budgetModalClose');
        document.dispatchEvent(event);
    }
};