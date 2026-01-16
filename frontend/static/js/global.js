    // frontend/static/js/global.js

    // Balance Validator
    window.BalanceValidator = {
        showSyncAlert: function(message) {
            const alertDiv = document.getElementById('balance-sync-alert');
            if (alertDiv) {
                const span = alertDiv.querySelector('span');
                if (span) span.textContent = message;
                alertDiv.style.display = 'block';
                
                // Auto-hide após 30 segundos
                setTimeout(() => {
                    alertDiv.style.display = 'none';
                }, 30000);
            }
        },
        
        syncAllBalances: function() {
            console.log('🔄 Sincronizando saldos...');
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfToken) {
                this.showSyncAlert('Erro: Token CSRF não encontrado');
                return;
            }
            
            fetch('/api/accounts/sync-balances/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken.value,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.showSyncAlert(data.message || '✅ Sincronização concluída com sucesso!');
                
                // Recarregar após 2 segundos se necessário
                if (data.reload) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('❌ Erro na sincronização:', error);
                this.showSyncAlert('❌ Erro ao sincronizar saldos. Tente novamente.');
            });
        }
    };

    // Garantir que BalanceValidator existe
    if (typeof window.BalanceValidator === 'undefined') {
        window.BalanceValidator = {
            showSyncAlert: function(message) {
                console.log('Alert:', message);
            },
            syncAllBalances: function() {
                console.log('Fallback sync');
            }
        };
    }

    // Utilitários globais
    window.utils = {
        formatCurrency: function(value) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        },
        
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        },
        
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    };

    // Inicialização quando DOM estiver pronto
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🌐 Ledger System Finance carregado (Bedimcode)');
        
        // Verificar se StateManager foi carregado
        if (!window.AppState) {
            console.warn('⚠️ StateManager não encontrado. Carregando...');
            
            // Tentar carregar dinamicamente se necessário
            const script = document.createElement('script');
            script.src = '/static/js/state-manager.js';
            script.onload = function() {
                console.log('✅ StateManager carregado dinamicamente');
                
                // Notificar todos os componentes que StateManager está pronto
                document.dispatchEvent(new CustomEvent('statemanager:ready', {
                    detail: { AppState: window.AppState }
                }));
            };
            script.onerror = function() {
                console.error('❌ Falha ao carregar StateManager');
            };
            document.head.appendChild(script);
        } else {
            console.log('✅ StateManager já carregado');
            
            // Disparar evento que StateManager está pronto
            document.dispatchEvent(new CustomEvent('statemanager:ready', {
                detail: { AppState: window.AppState }
            }));
        }
        
        // Configurar teclas de atalho globais
        setupGlobalShortcuts();
        
        // Configurar comportamentos comuns
        setupCommonBehaviors();
    });

    // Configurar atalhos de teclado
    function setupGlobalShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + B - Alternar sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                if (window.AppState) {
                    window.AppState.toggleSidebar();
                } else if (window.SidebarManager) {
                    window.SidebarManager.toggle();
                }
            }
            
            // Esc - Fechar modais/sidebar
            if (e.key === 'Escape') {
                // Fechar sidebar em mobile
                if (window.AppState && window.AppState.isMobile() && window.AppState.isSidebarOpen()) {
                    window.AppState.closeSidebar();
                }
                
                // Fechar qualquer modal aberto
                const modals = document.querySelectorAll('.modal.show');
                modals.forEach(modal => {
                    const closeBtn = modal.querySelector('[data-dismiss="modal"]');
                    if (closeBtn) closeBtn.click();
                });
            }
        });
    }

    // Configurar comportamentos comuns
    function setupCommonBehaviors() {
        // Prevenir envio duplo de formulários
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
                    
                    // Reabilitar após 5 segundos (caso haja erro)
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        const originalText = submitBtn.getAttribute('data-original-text') || 'Enviar';
                        submitBtn.innerHTML = originalText;
                    }, 5000);
                }
            });
        });
        
        // Salvar texto original dos botões de submit
        document.querySelectorAll('button[type="submit"]').forEach(btn => {
            if (!btn.hasAttribute('data-original-text')) {
                btn.setAttribute('data-original-text', btn.innerHTML);
            }
        });
        
        // Tooltips nativos (se não usar Bootstrap)
        if (!window.bootstrap) {
            const tooltips = document.querySelectorAll('[title]');
            tooltips.forEach(element => {
                element.addEventListener('mouseenter', function(e) {
                    const title = this.getAttribute('title');
                    if (title) {
                        const tooltip = document.createElement('div');
                        tooltip.className = 'native-tooltip';
                        tooltip.textContent = title;
                        tooltip.style.position = 'absolute';
                        tooltip.style.background = '#333';
                        tooltip.style.color = '#fff';
                        tooltip.style.padding = '5px 10px';
                        tooltip.style.borderRadius = '4px';
                        tooltip.style.fontSize = '12px';
                        tooltip.style.zIndex = '9999';
                        tooltip.style.pointerEvents = 'none';
                        
                        document.body.appendChild(tooltip);
                        
                        const rect = this.getBoundingClientRect();
                        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
                        
                        this.setAttribute('data-tooltip-id', 'tooltip-' + Date.now());
                    }
                });
                
                element.addEventListener('mouseleave', function() {
                    const tooltip = document.querySelector('.native-tooltip');
                    if (tooltip) {
                        tooltip.remove();
                    }
                });
            });
        }
    }

    // Exportar para uso em outros módulos
    window.GlobalUtils = window.utils;

    // frontend/static/js/global.js

// Balance Validator
window.BalanceValidator = {
    showSyncAlert: function(message) {
        const alertDiv = document.getElementById('balance-sync-alert');
        if (alertDiv) {
            const span = alertDiv.querySelector('span');
            if (span) span.textContent = message;
            alertDiv.style.display = 'block';
            
            // Auto-hide após 30 segundos
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 30000);
        }
    },
    
    syncAllBalances: function() {
        console.log('🔄 Sincronizando saldos...');
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfToken) {
            this.showSyncAlert('Erro: Token CSRF não encontrado');
            return;
        }
        
        fetch('/api/accounts/sync-balances/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken.value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            this.showSyncAlert(data.message || '✅ Sincronização concluída com sucesso!');
            
            // Recarregar após 2 segundos se necessário
            if (data.reload) {
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            }
        })
        .catch(error => {
            console.error('❌ Erro na sincronização:', error);
            this.showSyncAlert('❌ Erro ao sincronizar saldos. Tente novamente.');
        });
    }
};

// Garantir que BalanceValidator existe
if (typeof window.BalanceValidator === 'undefined') {
    window.BalanceValidator = {
        showSyncAlert: function(message) {
            console.log('Alert:', message);
        },
        syncAllBalances: function() {
            console.log('Fallback sync');
        }
    };
}

// Utilitários globais
window.utils = {
    formatCurrency: function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },
    
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    },
    
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Inicialização quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌐 Ledger System Finance carregado');
    
    // Verificar se StateManager foi carregado
    if (!window.AppState) {
        console.warn('⚠️ StateManager não encontrado. Carregando...');
        
        // Tentar carregar dinamicamente se necessário
        const script = document.createElement('script');
        script.src = '/static/js/state-manager.js';
        script.onload = function() {
            console.log('✅ StateManager carregado dinamicamente');
            
            // Notificar todos os componentes que StateManager está pronto
            document.dispatchEvent(new CustomEvent('statemanager:ready', {
                detail: { AppState: window.AppState }
            }));
        };
        script.onerror = function() {
            console.error('❌ Falha ao carregar StateManager');
        };
        document.head.appendChild(script);
    } else {
        console.log('✅ StateManager já carregado');
        
        // Disparar evento que StateManager está pronto
        document.dispatchEvent(new CustomEvent('statemanager:ready', {
            detail: { AppState: window.AppState }
        }));
    }
    
    // Configurar teclas de atalho globais
    setupGlobalShortcuts();
    
    // Configurar comportamentos comuns
    setupCommonBehaviors();
});

// Configurar atalhos de teclado
function setupGlobalShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + B - Alternar sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            if (window.AppState) {
                window.AppState.toggleSidebar();
            } else if (window.SidebarManager) {
                window.SidebarManager.toggle();
            }
        }
        
        // Esc - Fechar modais/sidebar
        if (e.key === 'Escape') {
            // Fechar sidebar em mobile
            if (window.AppState && window.AppState.isMobile() && window.AppState.isSidebarOpen()) {
                window.AppState.closeSidebar();
            }
            
            // Fechar qualquer modal aberto
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const closeBtn = modal.querySelector('[data-dismiss="modal"]');
                if (closeBtn) closeBtn.click();
            });
        }
    });
}

// Configurar comportamentos comuns
function setupCommonBehaviors() {
    // Prevenir envio duplo de formulários
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
                
                // Reabilitar após 5 segundos (caso haja erro)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    const originalText = submitBtn.getAttribute('data-original-text') || 'Enviar';
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });
    
    // Salvar texto original dos botões de submit
    document.querySelectorAll('button[type="submit"]').forEach(btn => {
        if (!btn.hasAttribute('data-original-text')) {
            btn.setAttribute('data-original-text', btn.innerHTML);
        }
    });
    
    // Tooltips nativos (se não usar Bootstrap)
    if (!window.bootstrap) {
        const tooltips = document.querySelectorAll('[title]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', function(e) {
                const title = this.getAttribute('title');
                if (title) {
                    const tooltip = document.createElement('div');
                    tooltip.className = 'native-tooltip';
                    tooltip.textContent = title;
                    tooltip.style.position = 'absolute';
                    tooltip.style.background = '#333';
                    tooltip.style.color = '#fff';
                    tooltip.style.padding = '5px 10px';
                    tooltip.style.borderRadius = '4px';
                    tooltip.style.fontSize = '12px';
                    tooltip.style.zIndex = '9999';
                    tooltip.style.pointerEvents = 'none';
                    
                    document.body.appendChild(tooltip);
                    
                    const rect = this.getBoundingClientRect();
                    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
                    
                    this.setAttribute('data-tooltip-id', 'tooltip-' + Date.now());
                }
            });
            
            element.addEventListener('mouseleave', function() {
                const tooltip = document.querySelector('.native-tooltip');
                if (tooltip) {
                    tooltip.remove();
                }
            });
        });
    }
}

// Exportar para uso em outros módulos
window.GlobalUtils = window.utils;