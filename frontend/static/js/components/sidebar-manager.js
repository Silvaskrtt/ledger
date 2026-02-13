/**
 * Gerencia a interface da sidebar e suas interações com o usuário.
 * Esta classe é responsável exclusivamente pela UI da sidebar,
 * delegando o gerenciamento de estado para o AppState.
 * 
 * Padrões utilizados:
 * - Observer: Reage a mudanças de estado via subscribe
 * - Single Responsibility: UI pura, sem lógica de estado
 * - Composition: Utiliza AppState como fonte de verdade
 * 
 * @class
 * @since 1.0.0
 */
class SidebarManager {
    /** @type {HTMLElement} Elemento DOM da sidebar */
    #sidebar;
    
    /** @type {HTMLElement} Botão de toggle da sidebar */
    #toggleBtn;
    
    /** @type {NodeListOf<Element>} Links de navegação da sidebar */
    #links;

    /**
     * Inicializa o gerenciador e configura subscribers.
     * @constructor
     */
    constructor() {
        this.#sidebar = document.getElementById('sidebar');
        this.#toggleBtn = document.getElementById('header-toggle');
        this.#links = document.querySelectorAll('.sidebar__link');
        
        this.#initialize();
    }

    /**
     * Configura listeners e estado inicial.
     * @private
     */
    #initialize() {
        if (!window.AppState) {
            this.#setupFallback();
            return;
        }

        const initialState = window.AppState.getSidebarState();

        this.#setupEventListeners();
        this.#setupAccessibility();
        
        // Reage a todas as mudanças de estado da sidebar
        window.AppState.subscribe('sidebar:*', (sidebarState) => {
            this.#updateUI(sidebarState);
        });
        
        this.#updateUI(initialState);
    }

    /**
     * Fallback para quando AppState não está disponível.
     * Mantém funcionalidade básica sem persistência de estado.
     * @private
     */
    #setupFallback() {
        if (!this.#sidebar || !this.#toggleBtn) return;

        this.#toggleBtn.addEventListener('click', () => {
            this.#sidebar.classList.toggle('show-sidebar');
        });
    }

    /**
     * Atualiza a interface baseado no estado atual.
     * @param {Object} sidebarState - Estado atual da sidebar
     * @param {boolean} sidebarState.isMobile - Se está em modo mobile
     * @param {boolean} sidebarState.isOpen - Se está aberta (mobile)
     * @param {boolean} sidebarState.isReduced - Se está reduzida (desktop)
     * @private
     */
    #updateUI(sidebarState) {
        if (!this.#sidebar) return;

        // Mobile: comportamente de show/hide
        if (sidebarState.isMobile) {
            if (sidebarState.isOpen) {
                this.#sidebar.classList.add('show-sidebar');
                this.#sidebar.classList.remove('reduced', 'hidden');
            } else {
                this.#sidebar.classList.remove('show-sidebar', 'reduced');
                this.#sidebar.classList.add('hidden');
            }
        } 
        // Desktop: sempre visível, alterna entre expandido/reduzido
        else {
            this.#sidebar.classList.add('show-sidebar');
            this.#sidebar.classList.remove('hidden');
            
            if (sidebarState.isReduced) {
                this.#sidebar.classList.add('reduced');
            } else {
                this.#sidebar.classList.remove('reduced');
            }
        }

        this.#updateToggleButton(sidebarState);

        if (sidebarState.isMobile) {
            this.#updateMobileOverlay(sidebarState);
        }
    }

    /**
     * Atualiza o ícone e acessibilidade do botão toggle.
     * @param {Object} sidebarState - Estado atual da sidebar
     * @private
     */
    #updateToggleButton(sidebarState) {
        if (!this.#toggleBtn) return;

        const icon = this.#toggleBtn.querySelector('i');
        if (!icon) return;

        if (sidebarState.isMobile) {
            icon.className = sidebarState.isOpen ? 'ri-close-line' : 'ri-menu-line';
            this.#toggleBtn.setAttribute('aria-label', 
                sidebarState.isOpen ? 'Fechar menu' : 'Abrir menu'
            );
        } else {
            icon.className = sidebarState.isReduced ? 'ri-arrow-right-line' : 'ri-arrow-left-line';
            this.#toggleBtn.setAttribute('aria-label', 
                sidebarState.isReduced ? 'Expandir menu' : 'Reduzir menu'
            );
        }

        this.#toggleBtn.setAttribute('aria-expanded', 
            sidebarState.isMobile ? sidebarState.isOpen.toString() : 'true'
        );
    }

    /**
     * Gerencia o overlay semitransparente em mobile.
     * @param {Object} sidebarState - Estado atual da sidebar
     * @private
     */
    #updateMobileOverlay(sidebarState) {
        const selector = '.sidebar-overlay';
        const existingOverlay = document.querySelector(selector);
        
        if (sidebarState.isOpen && !existingOverlay) {
            this.#createOverlay(selector);
        } else if (!sidebarState.isOpen && existingOverlay) {
            this.#removeOverlay(existingOverlay);
        }
    }

    /**
     * Cria e insere o overlay no DOM.
     * @param {string} selector - Seletor CSS para o overlay
     * @private
     */
    #createOverlay(selector) {
        const overlay = document.createElement('div');
        overlay.className = selector.substring(1);
        overlay.setAttribute('role', 'presentation');
        overlay.setAttribute('aria-hidden', 'true');
        
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: calc(var(--z-fixed) - 1);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        `;
        
        overlay.addEventListener('click', () => {
            window.AppState?.closeSidebar();
        });
        
        document.body.appendChild(overlay);
        
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            overlay.style.visibility = 'visible';
        });
    }

    /**
     * Remove o overlay com animação.
     * @param {HTMLElement} overlay - Elemento overlay a ser removido
     * @private
     */
    #removeOverlay(overlay) {
        overlay.style.opacity = '0';
        overlay.style.visibility = 'hidden';
        
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }

    /**
     * Configura os event listeners principais.
     * @private
     */
    #setupEventListeners() {
        this.#toggleBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.AppState?.toggleSidebar();
        });

        this.#links.forEach(link => {
            link.addEventListener('click', () => {
                this.#setActiveLink(link);
                window.AppState?.setCurrentPage(link.getAttribute('href'));
            });
        });

        // Fecha sidebar mobile ao clicar fora
        document.addEventListener('click', (e) => {
            const sidebarState = window.AppState?.getSidebarState();
            if (!sidebarState?.isMobile || !sidebarState.isOpen) return;

            const isClickInsideSidebar = this.#sidebar?.contains(e.target);
            const isClickOnToggle = this.#toggleBtn?.contains(e.target);
            
            if (!isClickInsideSidebar && !isClickOnToggle) {
                window.AppState?.closeSidebar();
            }
        });
    }

    /**
     * Marca um link como ativo e remove dos demais.
     * @param {Element} activeLink - Link a ser marcado como ativo
     * @private
     */
    #setActiveLink(activeLink) {
        this.#links.forEach(link => {
            link.classList.remove('active-link');
        });
        activeLink.classList.add('active-link');
    }

    /**
     * Configura atributos de acessibilidade.
     * @private
     */
    #setupAccessibility() {
        this.#sidebar?.setAttribute('role', 'navigation');
        this.#sidebar?.setAttribute('aria-label', 'Menu principal');
        
        this.#sidebar?.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                window.AppState?.closeSidebar();
                this.#toggleBtn?.focus();
            }
        });
    }
}

// Inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

/**
 * Inicializa o SidebarManager se o elemento existir.
 * @function
 */
function initialize() {
    if (document.getElementById('sidebar')) {
        new SidebarManager();
    }
}