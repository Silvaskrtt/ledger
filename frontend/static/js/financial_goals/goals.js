// frontend/static/js/financial_goals/goals.js
document.addEventListener('DOMContentLoaded', function() {
    const goalsList = document.getElementById("goalsList");
    const modal = document.getElementById("goalModal");
    const openBtn = document.getElementById("openGoalModal");
    const closeBtn = document.getElementById("closeGoalModal");
    const form = document.getElementById("goalForm");
    
    // Event Listeners
    if (openBtn) {
        openBtn.addEventListener('click', () => modal.classList.remove("hidden"));
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add("hidden");
            form.reset();
        });
    }
    
    // Fechar modal clicando fora
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add("hidden");
            form.reset();
        }
    });
    
    // Fechar modal com ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add("hidden");
            form.reset();
        }
    });
    
    // Carregar metas
    loadGoals();
    
    // Submissão do formulário
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Mostrar loading
            submitBtn.textContent = 'Salvando...';
            submitBtn.disabled = true;
            
            try {
                const formData = new FormData(form);
                const data = {
                    name: formData.get('name'),
                    target_amount: parseFloat(formData.get('target_amount')),
                    deadline: formData.get('deadline'),
                    strategy: formData.get('strategy')
                };
                
                // Validar dados
                if (!data.name || !data.name.trim()) {
                    throw new Error('Nome da meta é obrigatório');
                }
                
                if (!data.target_amount || data.target_amount <= 0) {
                    throw new Error('Valor alvo deve ser maior que zero');
                }
                
                if (!data.deadline) {
                    throw new Error('Data limite é obrigatória');
                }
                
                if (!data.strategy) {
                    throw new Error('Estratégia é obrigatória');
                }
                
                // Obter CSRF token
                const csrfToken = getCookie("csrftoken");
                if (!csrfToken) {
                    throw new Error('Token de segurança não encontrado');
                }
                
                // Enviar requisição
                const response = await fetch("/api/goals/financial-goals/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Sucesso
                    showNotification('Meta criada com sucesso!', 'success');
                    
                    // Fechar modal e limpar formulário
                    modal.classList.add("hidden");
                    form.reset();
                    
                    // Recarregar lista
                    loadGoals();
                } else {
                    // Erro do servidor
                    throw new Error(result.detail || result.message || result.error || 'Erro ao criar meta');
                }
                
            } catch (error) {
                showNotification(error.message, 'error');
                console.error('Erro ao criar meta:', error);
            } finally {
                // Restaurar botão
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});

async function loadGoals() {
    const goalsList = document.getElementById("goalsList");
    
    if (!goalsList) return;
    
    try {
        goalsList.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <p>Carregando metas...</p>
            </div>
        `;
        
        const res = await fetch("/api/goals/financial-goals/");
        
        if (!res.ok) {
            throw new Error(`Erro ${res.status} ao carregar metas`);
        }

        const goals = await res.json();
        
        // Verificar se é uma resposta paginada
        let goalsData = goals;
        if (goals.results) {
            goalsData = goals.results;  // Para respostas paginadas
        }
        
        // Verificar se é um array
        if (!Array.isArray(goalsData)) {
            throw new Error('Formato de dados inválido da API');
        }

        goalsList.innerHTML = "";

        if (goalsData.length === 0) {
            goalsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎯</div>
                    <h3>Nenhuma meta cadastrada</h3>
                    <p>Comece criando sua primeira meta financeira!</p>
                    <button id="openGoalModalEmpty" class="btn-primary" style="margin-top: 16px;">
                        + Criar Primeira Meta
                    </button>
                </div>
            `;
            
            // Adicionar evento ao botão
            const emptyBtn = document.getElementById("openGoalModalEmpty");
            if (emptyBtn) {
                emptyBtn.addEventListener('click', () => {
                    document.getElementById("goalModal").classList.remove("hidden");
                });
            }
            return;
        }

        goalsData.forEach(goal => {
            const card = document.createElement("div");
            card.className = "goal-card";
            
            // Formatar datas
            const deadlineDate = new Date(goal.deadline);
            const formattedDate = deadlineDate.toLocaleDateString('pt-BR');
            
            // Status badge
            const statusText = goal.status === 'ACTIVE' ? 'Ativa' :
                              goal.status === 'COMPLETED' ? 'Concluída' :
                              goal.status === 'CANCELLED' ? 'Cancelada' : 'Expirada';
            
            // Format amounts
            const currentAmount = parseFloat(goal.current_amount || 0).toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
            
            const targetAmount = parseFloat(goal.target_amount || 0).toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
            
            // Calcular percentual
            const percent = goal.percent || 0;
            
            // Strategy text
            const strategyText = goal.strategy === 'SAVE' ? 'Poupar' :
                                goal.strategy === 'INVEST' ? 'Investir' :
                                goal.strategy === 'SPEND' ? 'Gastar' : 'Quitar dívida';

            card.innerHTML = `
                <div class="goal-card-header">
                    <h3>${goal.name}</h3>
                    <span class="goal-status status-${goal.status}">${statusText}</span>
                </div>
                
                <div class="goal-strategy">
                    <span class="strategy-badge">${strategyText}</span>
                </div>
                
                <div class="goal-progress">
                    <div class="progress-bar">
                        <div class="progress" style="width: ${percent}%"></div>
                    </div>
                    <div class="progress-text">${Math.round(percent)}%</div>
                </div>
                
                <div class="goal-amounts">
                    <div class="current-amount">
                        <span class="label">Atual:</span>
                        <span class="value">R$ ${currentAmount}</span>
                    </div>
                    <div class="target-amount">
                        <span class="label">Meta:</span>
                        <span class="value">R$ ${targetAmount}</span>
                    </div>
                </div>
                
                <div class="goal-footer">
                    <div class="deadline">
                        <i class="far fa-calendar"></i>
                        Até ${formattedDate}
                    </div>
                    <button class="btn-icon edit-goal" data-id="${goal.financial_goal || goal.id}">
                        <i class="far fa-edit"></i>
                    </button>
                </div>
            `;

            goalsList.appendChild(card);
        });

    } catch (error) {
        console.error("Erro ao carregar metas:", error);
        goalsList.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h3>Erro ao carregar metas</h3>
                <p>${error.message}</p>
                <button onclick="loadGoals()" class="btn-secondary" style="margin-top: 16px;">
                    Tentar novamente
                </button>
            </div>
        `;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(";").forEach(cookie => {
            const c = cookie.trim();
            if (c.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
    // Remover notificação anterior
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
    
    document.body.appendChild(notification);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Adicionar estilos CSS para notificações
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(notificationStyles);