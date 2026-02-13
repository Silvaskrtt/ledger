/**
 * Gerenciador de Tema da Aplicação.
 * Responsável pela interface do usuário relacionada à alternância de temas,
 * reagindo às mudanças de estado do AppState e mantendo a UI sincronizada.
 * 
 * Padrões utilizados:
 * - Observer: Reage a mudanças de tema via subscribe
 * - Single Responsibility: UI pura, sem lógica de estado
 * - Composition: Utiliza AppState como fonte da verdade
 * 
 * @class
 * @since 1.0.0
 * 
 * @example
 * // HTML necessário
 * <button id="theme-button">
 *     <i class="ri-moon-clear-fill"></i>
 * </button>
 * 
 * @example
 * // O gerenciador inicializa automaticamente
 * // quando o DOM estiver pronto
 */
class ThemeManager {
    /** @type {HTMLElement|null} Botão de alternância de tema */
    #themeButton;
    
    /** @type {Object} Mapeamento de ícones por tema */
    #icons = {
        dark: 'ri-moon-clear-fill',
        light: 'ri-sun-fill'
    };
    
    /** @type {Object} Rótulos de acessibilidade por tema */
    #labels = {
        dark: 'Alternar para tema claro',
        light: 'Alternar para tema escuro'
    };

    /**
     * Inicializa o gerenciador e configura subscribers.
     * @constructor
     */
    constructor() {
        this.#themeButton = document.getElementById('theme-button');
        
        if (!this.#themeButton) {
            console.warn('[ThemeManager] Botão de tema não encontrado');
            return;
        }
        
        this.#initialize();
    }

    /**
     * Configura listeners e estado inicial.
     * @private
     */
    #initialize() {
        if (!window.AppState) {
            console.warn('[ThemeManager] AppState não disponível');
            return;
        }

        this.#setupEventListeners();
        this.#setupAccessibility();
        
        // Reage a mudanças de tema
        window.AppState.subscribe('theme:toggle', (theme) => {
            this.#updateThemeButton(theme);
        });
        
        // Define estado inicial
        this.#updateThemeButton(window.AppState.getTheme());
    }

    /**
     * Atualiza o ícone e rótulo do botão baseado no tema.
     * @param {string} theme - Tema atual ('dark' | 'light')
     * @private
     */
    #updateThemeButton(theme) {
        if (!this.#themeButton) return;

        const icon = this.#themeButton.querySelector('i');
        if (!icon) return;

        // Remove todas as classes de ícone de tema
        icon.classList.remove(...Object.values(this.#icons));
        
        // Adiciona a classe do ícone atual
        icon.classList.add(this.#icons[theme]);
        
        // Atualiza rótulo de acessibilidade
        this.#themeButton.setAttribute('aria-label', this.#labels[theme]);
        
        // Atualiza estado do tema como atributo de dados
        this.#themeButton.dataset.theme = theme;
    }

    /**
     * Configura os event listeners principais.
     * @private
     */
    #setupEventListeners() {
        if (!this.#themeButton) return;

        // Click handler
        this.#themeButton.addEventListener('click', (e) => {
            e.preventDefault();
            window.AppState?.toggleTheme();
        });

        // Touch handler para dispositivos móveis (otimização)
        this.#themeButton.addEventListener('touchstart', (e) => {
            e.preventDefault(); // Previne double-tap zoom
        }, { passive: false });
    }

    /**
     * Configura atributos e comportamentos de acessibilidade.
     * @private
     */
    #setupAccessibility() {
        if (!this.#themeButton) return;

        // Atributos ARIA
        this.#themeButton.setAttribute('role', 'button');
        this.#themeButton.setAttribute('aria-live', 'polite');
        
        // Foco via teclado
        this.#themeButton.setAttribute('tabindex', '0');

        // Keyboard navigation
        this.#themeButton.addEventListener('keydown', (e) => {
            // Enter ou Espaço ativam o botão
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                window.AppState?.toggleTheme();
            }
            
            // Setas esquerda/direita também ativam (padrão adicional)
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                window.AppState?.toggleTheme();
            }
        });

        // Feedback para leitores de tela
        this.#themeButton.addEventListener('themeChange', (e) => {
            const theme = e.detail;
            this.#themeButton.setAttribute('aria-label', this.#labels[theme]);
        });
    }

    /**
     * Retorna o ícone atual baseado no tema.
     * @param {string} theme - Tema para obter ícone
     * @returns {string} Classe do ícone
     * @public
     */
    getIconForTheme(theme) {
        return this.#icons[theme] || this.#icons.dark;
    }

    /**
     * Retorna o rótulo atual baseado no tema.
     * @param {string} theme - Tema para obter rótulo
     * @returns {string} Rótulo de acessibilidade
     * @public
     */
    getLabelForTheme(theme) {
        return this.#labels[theme] || this.#labels.dark;
    }

    /**
     * Força uma atualização do botão de tema.
     * Útil após mudanças manuais de tema.
     * @public
     */
    refresh() {
        if (!window.AppState) return;
        this.#updateThemeButton(window.AppState.getTheme());
    }

    /**
     * Destrói a instância e limpa event listeners.
     * @public
     */
    destroy() {
        if (!this.#themeButton) return;

        // Remove event listeners clonando o elemento
        const oldButton = this.#themeButton;
        const newButton = oldButton.cloneNode(true);
        oldButton.parentNode?.replaceChild(newButton, oldButton);
        
        this.#themeButton = null;
    }
}

// Inicialização automática
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeThemeManager);
} else {
    initializeThemeManager();
}

/**
 * Inicializa o ThemeManager se o elemento existir.
 * @function
 */
function initializeThemeManager() {
    if (document.getElementById('theme-button') && !window.themeManager) {
        window.themeManager = new ThemeManager();
    }
}

// Suporte para módulos (opcional)
if (typeof exports !== 'undefined') {
    exports.ThemeManager = ThemeManager;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThemeManager };
}