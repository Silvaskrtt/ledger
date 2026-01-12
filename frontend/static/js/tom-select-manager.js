/**
 * TomSelectManager - Gerenciador global de instâncias TomSelect
 * 
 * Responsável por:
 * - Inicializar automaticamente todos os selects com classe "tom-select"
 * - Gerenciar instâncias para acesso posterior
 * - Aplicar configurações padrão consistentes
 * - Suportar configurações customizadas via data-attributes
 * 
 * Uso:
 * 1. Adicione classe "tom-select" ao select HTML
 * 2. Opcionalmente, adicione data-tom-config para customização
 * 3. TomSelectManager inicializa automaticamente após página carregar
 * 
 * Exemplo HTML:
 * <select id="meu-select" class="tom-select">
 *     <option value="">Selecione...</option>
 * </select>
 * 
 * Exemplo com config customizada:
 * <select id="tags" class="tom-select" data-tom-config='{"plugins": ["remove_button"]}'>
 *     <option value="">Selecione...</option>
 * </select>
 */

class TomSelectManager {
    constructor() {
        this.instances = {};
        this.defaultConfig = {
            create: false,
            allowEmptyOption: true,
            placeholder: 'Selecione uma opção',
            render: {
                option: (data, escape) => `<div>${escape(data.text)}</div>`,
                item: (data, escape) => `<div>${escape(data.text)}</div>`
            }
        };
    }

    /**
     * Inicializa todos os selects com classe "tom-select"
     * Chamado automaticamente após página carregar
     */
    init() {
        // Aguardar TomSelect estar disponível
        if (typeof TomSelect === 'undefined') {
            console.warn('TomSelect não carregado. Aguardando...');
            setTimeout(() => this.init(), 500);
            return;
        }

        const selectElements = document.querySelectorAll('select.tom-select');
        
        if (selectElements.length === 0) {
            console.log('Nenhum select com classe tom-select encontrado');
            return;
        }

        selectElements.forEach((select) => {
            this.initializeSelect(select);
        });

        console.log(`TomSelectManager: ${selectElements.length} select(s) inicializado(s)`);
    }

    /**
     * Inicializa um select específico
     * @param {HTMLSelectElement} selectElement - Elemento select
     */
    initializeSelect(selectElement) {
        const selectId = selectElement.id || selectElement.name;
        
        if (!selectId) {
            console.warn('Select sem id ou name:', selectElement);
            return;
        }

        // Evitar duplicação
        if (this.instances[selectId]) {
            console.log(`TomSelect ${selectId} já inicializado`);
            return;
        }

        try {
            // Obter configuração customizada via data-attribute
            let config = { ...this.defaultConfig };
            
            if (selectElement.dataset.tomConfig) {
                try {
                    const customConfig = JSON.parse(selectElement.dataset.tomConfig);
                    config = { ...config, ...customConfig };
                } catch (e) {
                    console.warn(`Erro ao parsear data-tom-config para ${selectId}:`, e);
                }
            }

            // Aplicar configurações específicas baseado no tipo
            this.applySmartConfig(selectElement, config);

            // Inicializar TomSelect
            this.instances[selectId] = new TomSelect(selectElement, config);
            
            console.log(`✓ TomSelect inicializado: ${selectId}`);
        } catch (error) {
            console.error(`✗ Erro ao inicializar TomSelect ${selectId}:`, error);
        }
    }

    /**
     * Aplica configurações inteligentes baseado em atributos do select
     * @param {HTMLSelectElement} selectElement - Elemento select
     * @param {Object} config - Configuração a ser modificada
     */
    applySmartConfig(selectElement, config) {
        // Se é múltipla seleção
        if (selectElement.hasAttribute('multiple')) {
            config.plugins = { ...config.plugins, remove_button: {} };
            config.placeholder = config.placeholder || 'Selecione uma ou mais opções';
            config.maxItems = selectElement.dataset.maxItems || 10;
        }

        // Se é obrigatório
        if (selectElement.hasAttribute('required')) {
            config.allowEmptyOption = false;
        }

        // Se tem placeholder data-attribute
        if (selectElement.dataset.placeholder) {
            config.placeholder = selectElement.dataset.placeholder;
        }

        // Se tem data-sortField
        if (selectElement.dataset.sortField) {
            config.sortField = {
                field: selectElement.dataset.sortField,
                direction: selectElement.dataset.sortDirection || 'asc'
            };
        }

        // Se é tipo search (busca em listas grandes)
        if (selectElement.classList.contains('tom-select-search')) {
            config.maxOptions = 50;
            config.searchField = selectElement.dataset.searchField || 'text';
        }
    }

    /**
     * Obtém uma instância TomSelect pelo ID
     * @param {string} selectId - ID do select
     * @returns {TomSelect|null}
     */
    getInstance(selectId) {
        return this.instances[selectId] || null;
    }

    /**
     * Obtém o valor de um select TomSelect
     * @param {string} selectId - ID do select
     * @returns {string|string[]|null}
     */
    getValue(selectId) {
        const instance = this.getInstance(selectId);
        return instance ? instance.getValue() : null;
    }

    /**
     * Define o valor de um select TomSelect
     * @param {string} selectId - ID do select
     * @param {string|string[]} value - Novo valor
     */
    setValue(selectId, value) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.setValue(value);
        }
    }

    /**
     * Limpa um select TomSelect
     * @param {string} selectId - ID do select
     */
    clear(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.clear();
        }
    }

    /**
     * Limpa e desabilita um select
     * @param {string} selectId - ID do select
     */
    disable(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.disable();
        }
    }

    /**
     * Habilita um select desabilitado
     * @param {string} selectId - ID do select
     */
    enable(selectId) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.enable();
        }
    }

    /**
     * Adiciona opção dinamicamente
     * @param {string} selectId - ID do select
     * @param {Object} option - {value: 'x', text: 'Opção X'}
     */
    addOption(selectId, option) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.addOption(option);
        }
    }

    /**
     * Remove opção dinamicamente
     * @param {string} selectId - ID do select
     * @param {string} value - Valor da opção a remover
     */
    removeOption(selectId, value) {
        const instance = this.getInstance(selectId);
        if (instance) {
            instance.removeOption(value);
        }
    }

    /**
     * Reinicializa todas as instâncias
     */
    reinitialize() {
        this.instances = {};
        this.init();
    }

    /**
     * Obtém informações de debug
     * @returns {Object}
     */
    getDebugInfo() {
        return {
            totalInstances: Object.keys(this.instances).length,
            instances: Object.keys(this.instances),
            defaultConfig: this.defaultConfig
        };
    }
}

// Inicializar automaticamente quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.tomSelectManager = new TomSelectManager();
        window.tomSelectManager.init();
    });
} else {
    window.tomSelectManager = new TomSelectManager();
    window.tomSelectManager.init();
}

// Exportar para uso em módulos (se aplicável)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TomSelectManager;
}
