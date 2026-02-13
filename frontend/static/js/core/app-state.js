/**
 * Gerenciador Central de Estado da Aplicação.
 * Implementa o padrão Singleton para fornecer uma fonte única da verdade
 * para o estado global da aplicação.
 * 
 * Padrões utilizados:
 * - Singleton: Instância única global via window.AppState
 * - Observer: Sistema de eventos para reatividade
 * - State: Encapsulamento e gerenciamento centralizado de estado
 * - Command: Ações de toggle, open, close como comandos
 * 
 * @class
 * @since 1.0.0
 */
class AppState {
    /** @type {Object} Estado global da aplicação */
    #state;
    
    /** @type {Array<Object>} Lista de observers registrados */
    #observers;

    /**
     * Inicializa o estado com valores do localStorage ou padrões.
     * @constructor
     */
    constructor() {
        this.#state = {
            sidebar: {
                isOpen: localStorage.getItem('sidebarOpen') === 'true' || false,
                isReduced: localStorage.getItem('sidebarReduced') === 'true' || false,
                isMobile: window.innerWidth <= 768
            },
            theme: localStorage.getItem('theme') || 'dark',
            currentPage: window.location.pathname,
            user: null
        };
        
        this.#observers = [];
        this.#initialize();
    }

    /**
     * Configura listeners globais e estado inicial.
     * @private
     */
    #initialize() {
        this.#setupResponsive();
        this.#applyTheme();
        this.#setupGlobalListeners();
    }

    /* ========= SIDEBAR METHODS ========= */

    /**
     * Alterna o estado da sidebar baseado no dispositivo.
     * Mobile: show/hide
     * Desktop: expandido/reduzido (nunca fecha)
     * @public
     */
    toggleSidebar() {
        const { isMobile, isOpen, isReduced } = this.#state.sidebar;

        if (isMobile) {
            this.#state.sidebar.isOpen = !isOpen;
            this.#state.sidebar.isReduced = false;
        } else {
            // Desktop: sempre aberto, alterna entre expandido/reduzido
            if (isOpen && !isReduced) {
                this.#state.sidebar.isReduced = true;
            } else if (isOpen && isReduced) {
                this.#state.sidebar.isReduced = false;
            } else if (!isOpen) {
                this.#state.sidebar.isOpen = true;
                this.#state.sidebar.isReduced = false;
            }
            this.#state.sidebar.isOpen = true;
        }

        this.#persistState('sidebar');
        this.#notify('sidebar:toggle', this.#state.sidebar);
    }

    /**
     * Abre a sidebar (mobile) ou expande (desktop).
     * @public
     */
    openSidebar() {
        if (!this.#state.sidebar.isOpen) {
            this.#state.sidebar.isOpen = true;
            
            if (!this.#state.sidebar.isMobile) {
                this.#state.sidebar.isReduced = false;
            }
            
            this.#persistState('sidebar');
            this.#notify('sidebar:open', this.#state.sidebar);
        }
    }

    /**
     * Fecha a sidebar (mobile) ou reduz (desktop).
     * @public
     */
    closeSidebar() {
        if (this.#state.sidebar.isMobile) {
            if (this.#state.sidebar.isOpen) {
                this.#state.sidebar.isOpen = false;
                this.#state.sidebar.isReduced = false;
                this.#persistState('sidebar');
                this.#notify('sidebar:close', this.#state.sidebar);
            }
        } else {
            // Desktop: reduz em vez de fechar
            if (!this.#state.sidebar.isReduced) {
                this.#state.sidebar.isReduced = true;
                this.#notify('sidebar:reduced', this.#state.sidebar);
            }
        }
    }

    /**
     * Alterna apenas o estado reduzido da sidebar (desktop).
     * @public
     */
    toggleSidebarReduced() {
        this.#state.sidebar.isReduced = !this.#state.sidebar.isReduced;
        localStorage.setItem('sidebarReduced', this.#state.sidebar.isReduced);
        this.#notify('sidebar:reduced', this.#state.sidebar);
    }

    /* ========= THEME METHODS ========= */

    /**
     * Alterna entre tema dark e light.
     * @public
     */
    toggleTheme() {
        this.#state.theme = this.#state.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.#state.theme);
        this.#applyTheme();
        this.#notify('theme:toggle', this.#state.theme);
    }

    /**
     * Aplica o tema atual ao documento.
     * @private
     */
    #applyTheme() {
        document.documentElement.setAttribute('data-theme', this.#state.theme);
    }

    /* ========= PAGE NAVIGATION ========= */

    /**
     * Atualiza a página atual e notifica observers.
     * @param {string} page - Caminho da página
     * @public
     */
    setCurrentPage(page) {
        this.#state.currentPage = page;
        this.#notify('page:change', page);

        // Auto-close sidebar em mobile após navegação
        if (this.#state.sidebar.isMobile && this.#state.sidebar.isOpen) {
            setTimeout(() => this.closeSidebar(), 300);
        }
    }

    /* ========= UTILITY METHODS ========= */

    /**
     * Configura detecção de dispositivo responsivo.
     * @private
     */
    #setupResponsive() {
        const checkMobile = () => {
            const wasMobile = this.#state.sidebar.isMobile;
            this.#state.sidebar.isMobile = window.innerWidth <= 768;

            if (wasMobile !== this.#state.sidebar.isMobile) {
                if (this.#state.sidebar.isMobile) {
                    this.#state.sidebar.isOpen = false;
                    this.#state.sidebar.isReduced = false;
                } else {
                    this.#state.sidebar.isOpen = true;
                    this.#state.sidebar.isReduced = false;
                }

                this.#persistState('sidebar');
                this.#notify('device:change', this.#state.sidebar);
            }
        };

        // Debounce para performance em resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(checkMobile, 100);
        });

        checkMobile();
    }

    /**
     * Configura listeners globais da aplicação.
     * @private
     */
    #setupGlobalListeners() {
        // Fecha sidebar com ESC (apenas mobile)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && 
                this.#state.sidebar.isMobile && 
                this.#state.sidebar.isOpen) {
                this.closeSidebar();
            }
        });

        this.#trackNavigation();
    }

    /**
     * Monitora mudanças na URL via History API.
     * @private
     */
    #trackNavigation() {
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = (...args) => {
            originalPushState.apply(this, args);
            window.dispatchEvent(new Event('locationchange'));
        };

        history.replaceState = (...args) => {
            originalReplaceState.apply(this, args);
            window.dispatchEvent(new Event('locationchange'));
        };

        window.addEventListener('popstate', () => {
            window.dispatchEvent(new Event('locationchange'));
        });

        window.addEventListener('locationchange', () => {
            this.setCurrentPage(window.location.pathname);
        });
    }

    /* ========= OBSERVER PATTERN ========= */

    /**
     * Registra um observer para receber notificações de eventos.
     * @param {string} event - Nome do evento ou padrão (ex: 'sidebar:*')
     * @param {Function} callback - Função a ser chamada quando o evento ocorrer
     * @returns {Function} Função para cancelar a inscrição
     * @public
     */
    subscribe(event, callback) {
        const observer = { event, callback };
        this.#observers.push(observer);

        // Notificação inicial para eventos relacionados ao estado atual
        if (event === 'sidebar:*') {
            queueMicrotask(() => {
                try {
                    callback(this.#state.sidebar);
                } catch (error) {
                    console.error(`[AppState] Erro na notificação inicial:`, error);
                }
            });
        } else if (event === 'theme:*') {
            queueMicrotask(() => {
                try {
                    callback(this.#state.theme);
                } catch (error) {
                    console.error(`[AppState] Erro na notificação inicial:`, error);
                }
            });
        }

        // Retorna função para cancelar inscrição
        return () => {
            const index = this.#observers.indexOf(observer);
            if (index > -1) {
                this.#observers.splice(index, 1);
            }
        };
    }

    /**
     * Notifica todos os observers relevantes sobre um evento.
     * @param {string} event - Nome do evento ocorrido
     * @param {*} [data=null] - Dados associados ao evento
     * @private
     */
    #notify(event, data = null) {
        this.#observers.forEach(observer => {
            if (observer.event === event || observer.event === '*') {
                this.#safeExecute(observer.callback, data || this.#state);
            } else if (observer.event.endsWith(':*')) {
                const baseEvent = observer.event.replace(':*', '');
                if (event.startsWith(baseEvent)) {
                    this.#safeExecute(observer.callback, data || this.#state);
                }
            }
        });
    }

    /**
     * Executa callback de forma segura, capturando erros.
     * @param {Function} callback - Função a ser executada
     * @param {*} data - Dados para a função
     * @private
     */
    #safeExecute(callback, data) {
        try {
            callback(data);
        } catch (error) {
            console.error(`[AppState] Erro em observer:`, error);
        }
    }

    /**
     * Persiste estado no localStorage.
     * @param {string} key - Chave do estado a persistir
     * @private
     */
    #persistState(key) {
        if (key === 'sidebar') {
            localStorage.setItem('sidebarOpen', this.#state.sidebar.isOpen);
        }
    }

    /* ========= PUBLIC API ========= */

    /**
     * Retorna uma cópia do estado atual da sidebar.
     * @returns {Object} Estado da sidebar
     * @public
     */
    getSidebarState() {
        return { ...this.#state.sidebar };
    }

    /**
     * Retorna o tema atual.
     * @returns {string} 'dark' | 'light'
     * @public
     */
    getTheme() {
        return this.#state.theme;
    }

    /**
     * Retorna a página atual.
     * @returns {string} Caminho da URL
     * @public
     */
    getCurrentPage() {
        return this.#state.currentPage;
    }

    /**
     * Retorna uma cópia do estado completo (imutável).
     * @returns {Object} Estado completo da aplicação
     * @public
     */
    getState() {
        return JSON.parse(JSON.stringify(this.#state));
    }
}

// Instância global única
window.AppState = new AppState();