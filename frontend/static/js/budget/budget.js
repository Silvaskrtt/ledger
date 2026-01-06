// frontend/static/js/budget/budget.js
document.addEventListener('DOMContentLoaded', function() {
    // Elementos
    const modal = document.getElementById('budgetModal');
    const openBtn = document.getElementById('openBudgetModal');
    const closeBtn = document.getElementById('closeBudgetModal');
    const cancelBtn = document.getElementById('cancelBudgetModal');
    const form = document.getElementById('budgetForm');
    
    // Valores atuais para preencher o campo de mês
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = String(now.getMonth() + 1).padStart(2, '0');
    
    // Função para abrir modal
    function openModal() {
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Previne scroll da página
            
            // Preenche o mês atual por padrão
            const monthInput = document.getElementById('month');
            if (monthInput && !monthInput.value) {
                monthInput.value = `${currentYear}-${currentMonth}`;
            }
            
            // Foca no primeiro campo
            const firstInput = form.querySelector('input, select');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }
    
    // Função para fechar modal
    function closeModal() {
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restaura scroll
            form.reset(); // Limpa o formulário
        }
    }
    
    // Event Listeners
    if (openBtn) {
        openBtn.addEventListener('click', openModal);
    }
    
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
    
    // Fechar modal com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
            closeModal();
        }
    });
    
    // Submissão do formulário
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Botão de submit
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.querySelector('.btn-text')?.textContent || submitBtn.textContent;
            
            // Mostrar loading
            if (submitBtn.querySelector('.btn-text')) {
                submitBtn.querySelector('.btn-text').textContent = 'Salvando...';
            } else {
                submitBtn.textContent = 'Salvando...';
            }
            submitBtn.disabled = true;
            
            try {
                // Preparar dados
                const formData = new FormData(form);
                const data = {
                    id_category: formData.get('id_category'),
                    limit_amount: parseFloat(formData.get('limit_amount')),
                    month: formData.get('month')
                };
                
                // Validar dados
                if (!data.id_category) {
                    throw new Error('Selecione uma categoria');
                }
                
                if (!data.limit_amount || data.limit_amount <= 0) {
                    throw new Error('Valor da meta deve ser maior que zero');
                }
                
                // Obter CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                if (!csrfToken) {
                    throw new Error('Token de segurança não encontrado');
                }
                
                // Enviar requisição
                const response = await fetch('/api/budget-category-limits/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Sucesso
                    showNotification('Meta salva com sucesso!', 'success');
                    setTimeout(() => {
                        closeModal();
                        location.reload(); // Recarregar para mostrar nova meta
                    }, 1500);
                } else {
                    // Erro do servidor
                    throw new Error(result.detail || result.message || 'Erro ao salvar meta');
                }
                
            } catch (error) {
                // Mostrar erro
                showNotification(error.message, 'error');
                console.error('Erro:', error);
                
                // Restaurar botão
                if (submitBtn.querySelector('.btn-text')) {
                    submitBtn.querySelector('.btn-text').textContent = originalText;
                } else {
                    submitBtn.textContent = originalText;
                }
                submitBtn.disabled = false;
            }
        });
    }
    
    // Função para mostrar notificações
    function showNotification(message, type = 'info') {
        // Remove notificação anterior se existir
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // Cria nova notificação
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Estilos básicos
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
        `;
        
        if (type === 'success') {
            notification.style.background = '#4CAF50';
        } else if (type === 'error') {
            notification.style.background = '#f44336';
        } else {
            notification.style.background = '#2196F3';
        }
        
        document.body.appendChild(notification);
        
        // Remove após 5 segundos
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    // Adicionar estilos CSS para animações
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    console.log('Budget module initialized');
});