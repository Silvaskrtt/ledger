/**
 * Gerenciador global de instâncias TomSelect.
 * Implementa o padrão Factory para criação centralizada e gerenciamento do ciclo de vida
 * de todos os selects com classe "tom-select" na aplicação.
 * 
 * Padrões utilizados:
 * - Factory: Cria e configura instâncias TomSelect
 * - Repository: Gerencia e fornece acesso às instâncias
 * - Strategy: Aplica configurações inteligentes baseadas em atributos
 * - Facade: Interface simplificada para operações comuns
 * 
 * @class
 * @since 1.0.0
 * 
 * @example
 * // HTML básico
 * <select id="meu-select" class="tom-select">
 *     <option value="">Selecione...</option>
 * </select>
 * 
 * @example
 * // HTML com configuração customizada
 * <select id="tags" class="tom-select" 
 *         data-tom-config='{"plugins": ["remove_button"]}'
 *         data-placeholder="Escolha tags...">
 *     <option value="">Selecione...</option>
 * </select>
 * 
 * @example
 * // Uso via API
 * window.tomSelectManager.getValue('meu-select');
 * window.tomSelectManager.setValue('meu-select', 'opcao1');
 */
class TomSelectManager {
    /** @type {Map<string, TomSelect>} Mapa de instâncias por ID */
    #instances;
    
    /** @type {Object} Configuração padrão aplicada a todas as instâncias */
    #defaultConfig;
    
    /** @type {number} Tempo máximo de espera para carregamento do TomSelect (ms) */
    #maxLoadAttempts = 5;
    
    /** @type {number} Tentativa atual de carregamento */
    #currentLoadAttempt = 0;

    /**
     * Inicializa o gerenciador com configurações padrão.
     * @constructor
     */
    constructor() {
        this.#instances = new Map();
        this.#defaultConfig = {
            create: false,
            allowEmptyOption: true,
            placeholder: 'Selecione uma opção',
            render: {
                option: (data, escape) => {
                    const text = escape(data.text);
                    return `<div class="tom-option">${text}</div>`;
                },
                item: (data, escape) => {
                    const text = escape(data.text);
                    return `<div class="tom-item">${text}</div>`;
                }
            }
        };
    }

    /**
     * Inicializa todos os selects com classe "tom-select".
     * Aguarda a biblioteca TomSelect estar disponível se necessário.
     * @public
     */
    init() {
        if (typeof TomSelect === 'undefined') {
            this.#retryInit();
            return;
        }

        const selectors = 'select.tom-select:not([data-tom-initialized])';
        const selectElements = document.querySelectorAll(selectors);
        
        if (selectElements.length === 0) {
            return;
        }

        selectElements.forEach((select) => {
            this.#initializeSelect(select);
        });

        // Marca todos os selects processados
        document.querySelectorAll('select.tom-select').forEach(select => {
            select.setAttribute('data-tom-initialized', 'true');
        });
    }

    /**
     * Tenta novamente a inicialização se TomSelect não estiver carregado.
     * @private
     */
    #retryInit() {
        if (this.#currentLoadAttempt >= this.#maxLoadAttempts) {
            console.error('[TomSelectManager] Falha ao carregar TomSelect após múltiplas tentativas');
            return;
        }

        this.#currentLoadAttempt++;
        
        setTimeout(() => {
            this.init();
        }, 500 * this.#currentLoadAttempt); // Exponential backoff
    }

    /**
     * Inicializa um select específico com TomSelect.
     * @param {HTMLSelectElement} selectElement - Elemento select a ser inicializado
     * @private
     */
    #initializeSelect(selectElement) {
        const selectId = selectElement.id || selectElement.name;
        
        if (!selectId) {
            console.warn('[TomSelectManager] Select sem id ou name ignorado:', selectElement);
            return;
        }

        if (this.#instances.has(selectId)) {
            return;
        }

        try {
            const config = this.#buildConfig(selectElement);
            const instance = new TomSelect(selectElement, config);
            
            this.#instances.set(selectId, instance);
            
            // Armazena referência no elemento para acesso direto
            selectElement.__tomSelect = instance;
            
        } catch (error) {
            console.error(`[TomSelectManager] Erro ao inicializar ${selectId}:`, error);
        }
    }

    /**
     * Constrói a configuração combinando padrão, data-attributes e regras inteligentes.
     * @param {HTMLSelectElement} selectElement - Elemento select
     * @returns {Object} Configuração final
     * @private
     */
    #buildConfig(selectElement) {
        // Configuração base
        const config = { ...this.#defaultConfig };
        
        // Configuração customizada via data-attribute
        this.#applyCustomConfig(selectElement, config);
        
        // Configurações inteligentes baseadas em atributos
        this.#applySmartConfig(selectElement, config);
        
        return config;
    }

    /**
     * Aplica configuração customizada do data-tom-config.
     * @param {HTMLSelectElement} selectElement - Elemento select
     * @param {Object} config - Configuração a ser modificada
     * @private
     */
    #applyCustomConfig(selectElement, config) {
        const customConfigAttr = selectElement.dataset.tomConfig;
        if (!customConfigAttr) return;

        try {
            const customConfig = JSON.parse(customConfigAttr);
            Object.assign(config, customConfig);
        } catch (error) {
            console.warn(`[TomSelectManager] Erro ao parsear data-tom-config:`, error);
        }
    }

    /**
     * Aplica configurações inteligentes baseadas em atributos HTML.
     * @param {HTMLSelectElement} selectElement - Elemento select
     * @param {Object} config - Configuração a ser modificada
     * @private
     */
    #applySmartConfig(selectElement, config) {
        // Multipla seleção
        if (selectElement.hasAttribute('multiple')) {
            config.plugins = {
                ...config.plugins,
                remove_button: {}
            };
            config.placeholder = selectElement.dataset.placeholder || 'Selecione uma ou mais opções';
            config.maxItems = parseInt(selectElement.dataset.maxItems, 10) || 10;
        }

        // Campo obrigatório
        if (selectElement.hasAttribute('required')) {
            config.allowEmptyOption = false;
            
            // Validação customizada
            config.onChange = (value) => {
                if (!value || value.length === 0) {
                    selectElement.setCustomValidity('Este campo é obrigatório');
                } else {
                    selectElement.setCustomValidity('');
                }
            };
        }

        // Placeholder personalizado
        if (selectElement.dataset.placeholder) {
            config.placeholder = selectElement.dataset.placeholder;
        }

        // Ordenação
        if (selectElement.dataset.sortField) {
            config.sortField = {
                field: selectElement.dataset.sortField,
                direction: selectElement.dataset.sortDirection || 'asc'
            };
        }

        // Modo busca (para listas grandes)
        if (selectElement.classList.contains('tom-select-search')) {
            config.maxOptions = 50;
            config.searchField = selectElement.dataset.searchField || ['text'];
            config.searchConjunction = 'and';
        }

        // Opções criáveis
        if (selectElement.dataset.creatable === 'true') {
            config.create = true;
            config.createOnBlur = true;
        }
    }

    /* ========= PUBLIC API ========= */

    /**
     * Obtém uma instância TomSelect pelo ID do select.
     * @param {string} selectId - ID ou name do select
     * @returns {TomSelect|null} Instância do TomSelect ou null
     * @public
     */
    getInstance(selectId) {
        return this.#instances.get(selectId) || null;
    }

    /**
     * Obtém o valor atual de um select.
     * @param {string} selectId - ID ou name do select
     * @returns {string|string[]|null} Valor atual
     * @public
     */
    getValue(selectId) {
        const instance = this.getInstance(selectId);
        return instance ? instance.getValue() : null;
    }

    /**
     * Define o valor de um select.
     * @param {string} selectId - ID ou name do select
     * @param {string|string[]} value - Novo valor
     * @public
     */
    setValue(selectId, value) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.setValue(value, true);
        }
    }

    /**
     * Limpa o valor de um select.
     * @param {string} selectId - ID ou name do select
     * @public
     */
    clear(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.clear();
        }
    }

    /**
     * Desabilita um select.
     * @param {string} selectId - ID ou name do select
     * @public
     */
    disable(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.disable();
        }
    }

    /**
     * Habilita um select previamente desabilitado.
     * @param {string} selectId - ID ou name do select
     * @public
     */
    enable(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.enable();
        }
    }

    /**
     * Adiciona uma nova opção dinamicamente.
     * @param {string} selectId - ID ou name do select
     * @param {Object} option - Objeto com value e text
     * @param {string} option.value - Valor da opção
     * @param {string} option.text - Texto da opção
     * @public
     */
    addOption(selectId, option) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.addOption(option);
        }
    }

    /**
     * Remove uma opção existente.
     * @param {string} selectId - ID ou name do select
     * @param {string} value - Valor da opção a remover
     * @public
     */
    removeOption(selectId, value) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.removeOption(value);
        }
    }

    /**
     * Limpa todas as opções de um select.
     * @param {string} selectId - ID ou name do select
     * @public
     */
    clearOptions(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.clearOptions();
        }
    }

    /**
     * Atualiza as opções de um select.
     * @param {string} selectId - ID ou name do select
     * @param {Array<Object>} options - Array de opções {value, text}
     * @public
     */
    updateOptions(selectId, options) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.clearOptions();
            options.forEach(opt => instance.addOption(opt));
        }
    }

    /**
     * Destrói uma instância específica.
     * @param {string} selectId - ID ou name do select
     * @public
     */
    destroy(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.destroy();
            this.#instances.delete(selectId);
        }
    }

    /**
     * Destrói todas as instâncias e reinicializa.
     * @public
     */
    reinitialize() {
        this.#instances.forEach((instance, selectId) => {
            try {
                instance.destroy();
            } catch (error) {
                console.warn(`[TomSelectManager] Erro ao destruir ${selectId}:`, error);
            }
        });
        
        this.#instances.clear();
        this.#currentLoadAttempt = 0;
        
        // Remove marcação de inicialização
        document.querySelectorAll('select.tom-select').forEach(select => {
            select.removeAttribute('data-tom-initialized');
        });
        
        this.init();
    }

    /**
     * Obtém informações de diagnóstico.
     * @returns {Object} Informações de debug
     * @public
     */
    getDiagnostics() {
        return {
            totalInstances: this.#instances.size,
            instances: Array.from(this.#instances.keys()),
            libraryLoaded: typeof TomSelect !== 'undefined',
            defaultConfig: this.#defaultConfig
        };
    }
}

// Inicialização automática
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeManager);
} else {
    initializeManager();
}

/**
 * Inicializa o gerenciador e expõe globalmente.
 * @function
 */
function initializeManager() {
    if (!window.tomSelectManager) {
        window.tomSelectManager = new TomSelectManager();
        window.tomSelectManager.init();
    }
}

// Suporte para módulos (ES6, CommonJS, AMD)
if (typeof exports !== 'undefined') {
    exports.TomSelectManager = TomSelectManager;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TomSelectManager };
}

if (typeof define === 'function' && define.amd) {
    define([], () => ({ TomSelectManager }));
}