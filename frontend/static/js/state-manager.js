/**
 * Gerenciador de Estado Global da Aplicação.
 * Implementa o padrão Observer para reatividade e gerencia o estado da sidebar,
 * tema, busca e navegação como fonte única da verdade.
 * 
 * Padrões utilizados:
 * - Observer: Sistema de subscribers para reatividade
 * - Singleton: Instância única global via window.AppState
 * - Facade: Interface simplificada via window.SidebarManager
 * - Command: Ações de toggle, open, close como comandos
 * 
 * @class
 * @since 1.0.0
 * 
 * @example
 * // Uso básico
 * window.AppState.toggleSidebar();
 * window.AppState.subscribe((event, state) => {
 *     console.log(`Evento ${event} disparado`, state);
 * });
 * 
 * @example
 * // API simplificada para sidebar
 * window.SidebarManager.open();
 * window.SidebarManager.close();
 */
class StateManager {
    /** @type {Object} Estado global da aplicação */
    #state;
    
    /** @type {Array<Function>} Subscribers para eventos de estado */
    #subscribers;
    
    /** @type {number} Tempo de transição para animações (ms) */
    #transitionDuration = 300;
    
    /** @type {string} Seletor do elemento sidebar */
    #sidebarSelector = '.sidebar';
    
    /** @type {string} ID do botão toggle */
    #toggleBtnId = 'sidebar-toggle-btn';

    /**
     * Inicializa o estado com valores do localStorage ou padrões.
     * @constructor
     */
    constructor() {
        this.#state = {
            sidebarOpen: false,
            isMobile: false,
            darkMode: localStorage.getItem('darkMode') === 'true',
            searchQuery: '',
            currentPage: window.location.pathname
        };
        
        this.#subscribers = [];
        this.#initialize();
    }

    /**
     * Configura listeners e estado inicial.
     * @private
     */
    #initialize() {
        this.#checkDevice();
        this.#loadPersistedState();
        this.#setupToggleButton();
        this.#setupResponsiveListener();
        this.#setupClickOutsideListener();
        this.#setupKeyboardListener();
        this.#updateUI();
        this.#trackNavigation();
        
        // Aplica tema inicial se darkMode ativo
        if (this.#state.darkMode) {
            document.body.classList.add('dark-mode');
        }
    }

    /**
     * Carrega estado persistido do localStorage.
     * @private
     */
    #loadPersistedState() {
        const savedSidebarState = localStorage.getItem('sidebarOpen');
        
        if (savedSidebarState !== null) {
            this.#state.sidebarOpen = savedSidebarState === 'true';
        } else {
            // Estado padrão: fechado em mobile, aberto em desktop
            this.#state.sidebarOpen = !this.#state.isMobile;
            this.#persistSidebarState();
        }
    }

    /**
     * Persiste estado da sidebar no localStorage.
     * @private
     */
    #persistSidebarState() {
        localStorage.setItem('sidebarOpen', this.#state.sidebarOpen.toString());
    }

    /**
     * Configura o botão de toggle da sidebar.
     * @private
     */
    #setupToggleButton() {
        const toggleBtn = document.getElementById(this.#toggleBtnId);
        if (!toggleBtn) return;

        // Remove event listeners anteriores clonando o elemento
        const newToggleBtn = toggleBtn.cloneNode(true);
        toggleBtn.parentNode?.replaceChild(newToggleBtn, toggleBtn);
        
        newToggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleSidebar();
        });
    }

    /**
     * Verifica se o dispositivo é mobile baseado na largura da tela.
     * @private
     */
    #checkDevice() {
        const wasMobile = this.#state.isMobile;
        this.#state.isMobile = window.innerWidth <= 768;
        
        if (wasMobile !== this.#state.isMobile) {
            this.#notifySubscribers('deviceChange');
        }
    }

    /**
     * Configura listener para redimensionamento da janela.
     * @private
     */
    #setupResponsiveListener() {
        let resizeTimeout;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const wasMobile = this.#state.isMobile;
                this.#checkDevice();
                
                // Ajusta sidebar conforme mudança de dispositivo
                if (wasMobile && !this.#state.isMobile && !this.#state.sidebarOpen) {
                    this.openSidebar();
                } else if (!wasMobile && this.#state.isMobile && this.#state.sidebarOpen) {
                    this.closeSidebar();
                }
            }, 100);
        });
    }

    /**
     * Configura listener para clique fora da sidebar (mobile).
     * @private
     */
    #setupClickOutsideListener() {
        document.addEventListener('click', (event) => {
            if (!this.#state.isMobile || !this.#state.sidebarOpen) return;
            
            const sidebar = document.querySelector(this.#sidebarSelector);
            const toggleBtn = document.getElementById(this.#toggleBtnId);
            
            if (!sidebar || !toggleBtn) return;
            
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnToggleBtn = toggleBtn.contains(event.target);
            
            if (!isClickInsideSidebar && !isClickOnToggleBtn) {
                this.closeSidebar();
            }
        });
    }

    /**
     * Configura listener para tecla ESC (mobile).
     * @private
     */
    #setupKeyboardListener() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.#state.isMobile && this.#state.sidebarOpen) {
                this.closeSidebar();
                
                // Retorna foco ao botão toggle
                const toggleBtn = document.getElementById(this.#toggleBtnId);
                toggleBtn?.focus();
            }
        });
    }

    /* ========= SIDEBAR METHODS ========= */

    /**
     * Alterna o estado da sidebar (abrir/fechar).
     * @public
     */
    toggleSidebar() {
        this.#state.sidebarOpen = !this.#state.sidebarOpen;
        this.#persistSidebarState();
        this.#notifySubscribers('sidebarToggle');
        this.#updateUI();

        // Acessibilidade: foco no primeiro link quando abre
        if (this.#state.sidebarOpen) {
            this.#focusFirstLink();
        }
    }

    /**
     * Abre a sidebar se estiver fechada.
     * @public
     */
    openSidebar() {
        if (!this.#state.sidebarOpen) {
            this.#state.sidebarOpen = true;
            this.#persistSidebarState();
            this.#notifySubscribers('sidebarOpen');
            this.#updateUI();
            this.#focusFirstLink();
        }
    }

    /**
     * Fecha a sidebar se estiver aberta.
     * @public
     */
    closeSidebar() {
        if (this.#state.sidebarOpen) {
            this.#state.sidebarOpen = false;
            this.#persistSidebarState();
            this.#notifySubscribers('sidebarClose');
            this.#updateUI();
            
            // Acessibilidade: retornar foco ao botão toggle
            const toggleBtn = document.getElementById(this.#toggleBtnId);
            toggleBtn?.focus();
        }
    }

    /**
     * Foca no primeiro link da sidebar para acessibilidade.
     * @private
     */
    #focusFirstLink() {
        setTimeout(() => {
            const firstLink = document.querySelector(`${this.#sidebarSelector} .nav-list a`);
            firstLink?.focus();
        }, 100);
    }

    /**
     * Atualiza a interface baseado no estado atual.
     * @private
     */
    #updateUI() {
        const sidebar = document.querySelector(this.#sidebarSelector);
        const toggleBtn = document.getElementById(this.#toggleBtnId);
        
        this.#updateSidebarElement(sidebar);
        this.#updateToggleButton(toggleBtn);
        this.#updateMobileOverlay();
    }

    /**
     * Atualiza o elemento da sidebar.
     * @param {HTMLElement|null} sidebar - Elemento sidebar
     * @private
     */
    #updateSidebarElement(sidebar) {
        if (!sidebar) return;

        if (this.#state.sidebarOpen) {
            sidebar.classList.add('open');
            sidebar.setAttribute('aria-expanded', 'true');
        } else {
            sidebar.classList.remove('open');
            sidebar.setAttribute('aria-expanded', 'false');
        }
    }

    /**
     * Atualiza o botão toggle e seu ícone.
     * @param {HTMLElement|null} toggleBtn - Botão toggle
     * @private
     */
    #updateToggleButton(toggleBtn) {
        if (!toggleBtn) return;

        const icon = toggleBtn.querySelector('i');
        
        if (icon) {
            if (this.#state.sidebarOpen) {
                icon.classList.replace('bx-menu', 'bx-menu-alt-right');
                toggleBtn.setAttribute('aria-label', 'Fechar menu de navegação');
            } else {
                icon.classList.replace('bx-menu-alt-right', 'bx-menu');
                toggleBtn.setAttribute('aria-label', 'Abrir menu de navegação');
            }
        }

        toggleBtn.setAttribute('aria-expanded', this.#state.sidebarOpen.toString());
    }

    /**
     * Gerencia overlay para mobile.
     * @private
     */
    #updateMobileOverlay() {
        if (!this.#state.isMobile) return;

        const selector = '.sidebar-overlay';
        const existingOverlay = document.querySelector(selector);
        
        if (this.#state.sidebarOpen && !existingOverlay) {
            this.#createOverlay(selector);
        } else if (!this.#state.sidebarOpen && existingOverlay) {
            this.#removeOverlay(existingOverlay);
        }
    }

    /**
     * Cria overlay para mobile.
     * @param {string} selector - Seletor do overlay
     * @private
     */
    #createOverlay(selector) {
        const overlay = document.createElement('div');
        overlay.className = selector.substring(1);
        overlay.setAttribute('aria-hidden', 'true');
        overlay.setAttribute('role', 'presentation');
        
        overlay.style.cssText = `
            position: fixed;
            top: var(--header-height, 60px);
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 998;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        `;
        
        overlay.addEventListener('click', () => this.closeSidebar());
        
        const mainLayout = document.querySelector('.main-layout');
        if (mainLayout) {
            mainLayout.appendChild(overlay);
            
            requestAnimationFrame(() => {
                overlay.style.opacity = '1';
                overlay.style.visibility = 'visible';
            });
        }
    }

    /**
     * Remove overlay com animação.
     * @param {HTMLElement} overlay - Elemento overlay
     * @private
     */
    #removeOverlay(overlay) {
        overlay.style.opacity = '0';
        overlay.style.visibility = 'hidden';
        
        setTimeout(() => {
            overlay.remove();
        }, this.#transitionDuration);
    }

    /* ========= THEME METHODS ========= */

    /**
     * Alterna entre modo dark e light.
     * @public
     */
    toggleDarkMode() {
        this.#state.darkMode = !this.#state.darkMode;
        localStorage.setItem('darkMode', this.#state.darkMode.toString());
        this.#notifySubscribers('darkModeToggle');
        
        if (this.#state.darkMode) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }

    /* ========= SEARCH METHODS ========= */

    /**
     * Define a query de busca atual.
     * @param {string} query - Texto da busca
     * @public
     */
    setSearchQuery(query) {
        this.#state.searchQuery = query;
        this.#notifySubscribers('searchChange');
    }

    /* ========= NAVIGATION METHODS ========= */

    /**
     * Define a página atual.
     * @param {string} page - Caminho da página
     * @public
     */
    setCurrentPage(page) {
        this.#state.currentPage = page;
        this.#notifySubscribers('pageChange');

        // Em mobile, fecha sidebar ao navegar
        if (this.#state.isMobile && this.#state.sidebarOpen) {
            setTimeout(() => this.closeSidebar(), this.#transitionDuration);
        }
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
     * Registra um subscriber para eventos de estado.
     * @param {Function} callback - Função chamada em mudanças de estado
     * @returns {Function} Função para cancelar inscrição
     * @public
     */
    subscribe(callback) {
        this.#subscribers.push(callback);
        
        // Notifica imediatamente com estado atual
        queueMicrotask(() => {
            try {
                callback('init', this.#state);
            } catch (error) {
                console.error('[StateManager] Erro na notificação inicial:', error);
            }
        });

        // Retorna função para cancelar inscrição
        return () => {
            const index = this.#subscribers.indexOf(callback);
            if (index > -1) {
                this.#subscribers.splice(index, 1);
            }
        };
    }

    /**
     * Notifica todos os subscribers sobre um evento.
     * @param {string} event - Nome do evento
     * @private
     */
    #notifySubscribers(event) {
        this.#subscribers.forEach(callback => {
            try {
                callback(event, this.#state);
            } catch (error) {
                console.error('[StateManager] Erro no subscriber:', error);
            }
        });
    }

    /* ========= PUBLIC GETTERS ========= */

    /**
     * Retorna se a sidebar está aberta.
     * @returns {boolean}
     * @public
     */
    isSidebarOpen() {
        return this.#state.sidebarOpen;
    }

    /**
     * Retorna se está em modo mobile.
     * @returns {boolean}
     * @public
     */
    isMobile() {
        return this.#state.isMobile;
    }

    /**
     * Retorna a página atual.
     * @returns {string}
     * @public
     */
    getCurrentPage() {
        return this.#state.currentPage;
    }

    /**
     * Retorna a query de busca atual.
     * @returns {string}
     * @public
     */
    getSearchQuery() {
        return this.#state.searchQuery;
    }

    /**
     * Retorna uma cópia do estado completo.
     * @returns {Object}
     * @public
     */
    getState() {
        return { ...this.#state };
    }

    /* ========= UTILITY METHODS ========= */

    /**
     * Reseta o estado da sidebar para o padrão.
     * @public
     */
    reset() {
        this.#state.sidebarOpen = !this.#state.isMobile;
        this.#persistSidebarState();
        this.#updateUI();
        this.#notifySubscribers('reset');
    }

    /**
     * Obtém informações de diagnóstico.
     * @returns {Object}
     * @public
     */
    getDiagnostics() {
        return {
            sidebarOpen: this.#state.sidebarOpen,
            isMobile: this.#state.isMobile,
            darkMode: this.#state.darkMode,
            currentPage: this.#state.currentPage,
            subscribersCount: this.#subscribers.length,
            persistedState: localStorage.getItem('sidebarOpen')
        };
    }
}

// Instância global única
if (!window.AppState) {
    window.AppState = new StateManager();
    
    /**
     * API pública simplificada para compatibilidade.
     * Fornece interface focada apenas em operações da sidebar.
     */
    window.SidebarManager = {
        /** Alterna a sidebar */
        toggle: () => window.AppState.toggleSidebar(),
        
        /** Abre a sidebar */
        open: () => window.AppState.openSidebar(),
        
        /** Fecha a sidebar */
        close: () => window.AppState.closeSidebar(),
        
        /** Verifica se a sidebar está aberta */
        isOpen: () => window.AppState.isSidebarOpen(),
        
        /** Verifica se está em modo mobile */
        isMobile: () => window.AppState.isMobile()
    };
}

// Suporte para módulos (opcional)
if (typeof exports !== 'undefined') {
    exports.StateManager = StateManager;
}