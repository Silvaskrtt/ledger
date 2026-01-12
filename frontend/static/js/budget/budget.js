// frontend/static/js/budget/budget.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Budget module initializing...');
    
    // Elementos
    const modal = document.getElementById('budgetModal');
    const openBtn = document.getElementById('openBudgetModal');
    const closeBtn = document.getElementById('closeBudgetModal');
    const cancelBtn = document.getElementById('cancelBudgetModal');
    const form = document.getElementById('budgetForm');
    
    // Valores atuais
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = String(now.getMonth() + 1).padStart(2, '0');
    
    // Carregar orçamentos
    loadBudgets();
    
    // Abrir modal
    if (openBtn) {
        openBtn.addEventListener('click', function() {
            openModal();
        });
    }
    
    // Fechar modal
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
    
    // Delegar eventos para botões dinâmicos
    document.addEventListener('click', function(e) {
        // Editar
        if (e.target.closest('.edit-budget')) {
            const btn = e.target.closest('.edit-budget');
            const limitId = btn.dataset.id;
            editBudget(limitId);
        }
        
        // Excluir
        if (e.target.closest('.delete-budget')) {
            const btn = e.target.closest('.delete-budget');
            const limitId = btn.dataset.id;
            deleteBudget(limitId);
        }
    });
    
    // Submissão do formulário
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Mostrar loading
            submitBtn.textContent = 'Salvando...';
            submitBtn.disabled = true;
            
            try {
                // Preparar dados
                const formData = new FormData(form);
                const data = {
                    category: formData.get('category'),
                    limit_amount: formData.get('limit_amount'),
                    month: formData.get('month')
                };
                
                console.log('Form data:', data);
                
                // Validar
                if (!data.category) {
                    throw new Error('Selecione uma categoria');
                }
                
                if (!data.limit_amount || parseFloat(data.limit_amount) <= 0) {
                    throw new Error('Valor da meta deve ser maior que zero');
                }
                
                // CSRF Token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                if (!csrfToken) {
                    throw new Error('Token de segurança não encontrado');
                }
                
                // Enviar requisição
                const response = await fetch('/api/create-budget-limit/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                console.log('Response:', result);
                
                if (response.ok && result.success) {
                    showNotification(result.message || 'Meta salva com sucesso!', 'success');
                    setTimeout(() => {
                        closeModal();
                        location.reload();
                    }, 1500);
                } else {
                    throw new Error(result.error || result.detail || 'Erro ao salvar meta');
                }
                
            } catch (error) {
                console.error('Error:', error);
                showNotification(error.message, 'error');
                
                // Restaurar botão
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // Inicializar TomSelect se disponível
    if (typeof TomSelect !== 'undefined') {
        const selectElement = document.getElementById('category');
        if (selectElement) {
            new TomSelect(selectElement, {
                create: false,
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });
        }
    }
});

// Funções
function openModal() {
    const modal = document.getElementById('budgetModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Preencher mês atual
        const monthInput = document.getElementById('month');
        if (monthInput && !monthInput.value) {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            monthInput.value = `${year}-${month}`;
        }
        
        // Focar no primeiro campo
        setTimeout(() => {
            const firstInput = document.querySelector('#budgetForm input, #budgetForm select');
            if (firstInput) firstInput.focus();
        }, 100);
    }
}

function closeModal() {
    const modal = document.getElementById('budgetModal');
    const form = document.getElementById('budgetForm');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        if (form) form.reset();
    }
}

async function loadBudgets() {
    try {
        const response = await fetch('/api/budget-overview/');
        const result = await response.json();
        
        if (response.ok && result.success) {
            console.log('Budgets loaded:', result.data);
            // Aqui você pode atualizar a interface com os dados
            updateBudgetDisplay(result.data);
        } else {
            console.error('Failed to load budgets:', result.error);
        }
    } catch (error) {
        console.error('Error loading budgets:', error);
    }
}

function updateBudgetDisplay(data) {
    // Função para atualizar a interface com dados da API
    // Pode ser usada para atualização dinâmica sem recarregar a página
    console.log('Updating display with:', data);
}

async function editBudget(limitId) {
    try {
        // Buscar dados atuais
        const response = await fetch(`/api/budget-category-limits/${limitId}/`);
        if (!response.ok) throw new Error('Erro ao carregar dados');
        
        const data = await response.json();
        console.log('Edit data:', data);
        
        // Preencher modal com dados
        openModal();
        
        // Preencher formulário
        setTimeout(() => {
            const categorySelect = document.getElementById('category');
            const amountInput = document.getElementById('limit_amount');
            
            if (categorySelect && data.category) {
                categorySelect.value = data.category;
            }
            
            if (amountInput && data.limit_amount) {
                amountInput.value = data.limit_amount;
            }
            
            // Mudar título do modal
            const modalTitle = document.querySelector('#budgetModal h3');
            if (modalTitle) {
                modalTitle.textContent = 'Editar Meta';
            }
            
            // Mudar ação do formulário para PUT
            const form = document.getElementById('budgetForm');
            if (form) {
                form.dataset.editId = limitId;
                const submitBtn = form.querySelector('button[type="submit"] .btn-text');
                if (submitBtn) {
                    submitBtn.textContent = 'Atualizar Meta';
                }
            }
        }, 300);
        
    } catch (error) {
        console.error('Error editing budget:', error);
        showNotification('Erro ao carregar dados para edição', 'error');
    }
}

async function deleteBudget(limitId) {
    if (!confirm('Tem certeza que deseja excluir esta meta?')) {
        return;
    }
    
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        const response = await fetch(`/api/budget-category-limits/${limitId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            showNotification('Meta excluída com sucesso!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error('Erro ao excluir meta');
        }
    } catch (error) {
        showNotification(error.message, 'error');
        console.error('Error:', error);
    }
}

function showNotification(message, type = 'info') {
    // Remover notificação existente
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    // Criar notificação
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    // Adicionar estilos de animação se não existirem
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
    
    document.body.appendChild(notification);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}