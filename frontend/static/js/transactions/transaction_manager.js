class TransactionManager {
    constructor() {
        this.currentTransactionId = null;
        this.isEditMode = false;
        this.tomSelectInstances = {};
        this.init();
    }

    init() {
        this.bindEvents();
        // Não inicializar TomSelects aqui - será feito apenas no modal
    }

    bindEvents() {
        // Botão nova transação
        document.getElementById('newTransactionBtn')?.addEventListener('click', () => {
            this.openModal('create');
        });

        // Botão adicionar primeira transação
        document.getElementById('addFirstTransaction')?.addEventListener('click', () => {
            this.openModal('create');
        });

        // Botões de editar
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const transactionId = e.currentTarget.dataset.id;
                this.openModal('edit', transactionId);
            });
        });

        // Botões de excluir
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const transactionId = e.currentTarget.dataset.id;
                this.openDeleteModal(transactionId);
            });
        });

        // Fechar modais
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeAllModals();
            });
        });

        // Confirmar exclusão
        document.getElementById('confirmDeleteBtn')?.addEventListener('click', () => {
            this.deleteTransaction();
        });

        // Submeter formulário
        document.getElementById('transactionForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTransaction();
        });

        // Fechar modal ao clicar fora
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeAllModals();
                }
            });
        });
    }

    async openModal(mode, transactionId = null) {
        this.isEditMode = mode === 'edit';
        this.currentTransactionId = transactionId;

        const modal = document.getElementById('transactionModal');
        const modalTitle = document.getElementById('modalTitle');
        const deleteBtn = document.getElementById('deleteTransactionBtn');
        const formContainer = document.getElementById('formContainer');

        // Atualizar título
        modalTitle.textContent = this.isEditMode ? 'Editar Transação' : 'Nova Transação';
        
        // Mostrar/ocultar botão excluir
        deleteBtn.style.display = this.isEditMode ? 'block' : 'none';
        deleteBtn.onclick = () => this.openDeleteModal(transactionId);

        // Limpar instâncias anteriores do TomSelect
        this.destroyTomSelects();

        // Mostrar loading
        formContainer.innerHTML = '<div class="loading">Carregando formulário...</div>';
        modal.classList.add('active');

        try {
            // Carregar formulário via AJAX
            const url = this.isEditMode 
                ? `/api/transactions/${transactionId}/form/`
                : '/api/transactions/form/';

            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar formulário');
            }

            const html = await response.text();
            formContainer.innerHTML = html;

            // Inicializar componentes do formulário
            this.initFormComponents();
            
        } catch (error) {
            console.error('Erro:', error);
            formContainer.innerHTML = `
                <div class="error-message">
                    <p>Erro ao carregar formulário. Por favor, recarregue a página.</p>
                </div>
            `;
        }
    }

    destroyTomSelects() {
        // Destruir todas as instâncias existentes do TomSelect
        Object.values(this.tomSelectInstances).forEach(instance => {
            if (instance && instance.destroy) {
                instance.destroy();
            }
        });
        this.tomSelectInstances = {};
    }

    initFormComponents() {
        // Inicializar TomSelect no formulário - APENAS se ainda não foi inicializado
        if (typeof TomSelect !== 'undefined') {
            document.querySelectorAll('#transactionForm select').forEach(select => {
                // Verificar se o select já tem uma instância do TomSelect
                if (!select.tomselect) {
                    try {
                        const instance = new TomSelect(select, {
                            create: false,
                            placeholder: select.getAttribute('placeholder') || 'Selecione...',
                            allowEmptyOption: false,
                            plugins: ['remove_button']
                        });
                        
                        const id = select.id;
                        if (id) {
                            this.tomSelectInstances[id] = instance;
                        }
                    } catch (error) {
                        console.warn(`Erro ao inicializar TomSelect para ${select.id}:`, error);
                    }
                }
            });
        }

        // Configurar data atual se vazio
        const dateInput = document.getElementById('occurred_at');
        if (dateInput && !dateInput.value) {
            const now = new Date();
            dateInput.value = now.toISOString().slice(0, 16);
        }

        // Configurar moeda padrão
        const currencySelect = document.getElementById('currency');
        if (currencySelect && this.tomSelectInstances['currency']) {
            this.tomSelectInstances['currency'].setValue('BRL');
        }

        // Configurar eventos para campos dinâmicos
        this.setupDynamicFields();

        // Preencher dados de edição se necessário
        this.prefillEditData();
    }

    prefillEditData() {
        if (!this.isEditMode) return;

        // Campos dinâmicos já devem estar preenchidos pelo template
        // Apenas garantir que a lógica de exibição funcione
        const originSelect = this.tomSelectInstances['origin'];
        if (originSelect) {
            const currentValue = originSelect.getValue();
            if (currentValue) {
                this.toggleDynamicFields(currentValue);
            }
        }
    }

    setupDynamicFields() {
        const originSelect = this.tomSelectInstances['origin'];
        if (originSelect) {
            originSelect.on('change', (value) => {
                this.toggleDynamicFields(value);
            });
            
            // Inicializar estado
            const currentValue = originSelect.getValue();
            if (currentValue) {
                this.toggleDynamicFields(currentValue);
            }
        }
    }

    toggleDynamicFields(origin) {
        // Esconder todos os campos dinâmicos
        document.querySelectorAll('.dynamic-field').forEach(field => {
            field.style.display = 'none';
        });

        // Mostrar campos específicos
        if (origin === 'RECURRENT') {
            document.querySelectorAll('[data-field="recurrent"]').forEach(field => {
                field.style.display = 'flex';
            });
        } else if (origin === 'INSTALLMENT') {
            document.querySelectorAll('[data-field="installment"]').forEach(field => {
                field.style.display = 'flex';
            });
        }
    }

    openDeleteModal(transactionId) {
        this.currentTransactionId = transactionId;
        document.getElementById('confirmDeleteModal').classList.add('active');
    }

    closeAllModals() {
        // Destruir TomSelects antes de fechar
        this.destroyTomSelects();
        
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
        
        // Resetar estado
        this.currentTransactionId = null;
        this.isEditMode = false;
        
        // Limpar formulário
        const formContainer = document.getElementById('formContainer');
        if (formContainer) {
            formContainer.innerHTML = '';
        }
        
        const transactionIdInput = document.getElementById('transactionId');
        if (transactionIdInput) {
            transactionIdInput.value = '';
        }
    }

    async saveTransaction() {
        const form = document.getElementById('transactionForm');
        if (!form) return;

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        try {
            // Desabilitar botão
            submitBtn.disabled = true;
            submitBtn.textContent = 'Salvando...';

            // Coletar dados do formulário
            const formData = this.collectFormData();

            // Validar dados básicos
            if (!this.validateFormData(formData)) {
                throw new Error('Preencha todos os campos obrigatórios');
            }

            // Determinar URL e método
            const url = this.isEditMode
                ? `/api/transactions/${this.currentTransactionId}/`
                : '/api/transactions/';
            
            const method = this.isEditMode ? 'PUT' : 'POST';

            // Enviar requisição
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                // Sucesso
                alert(result.message || 'Transação salva com sucesso!');
                this.closeAllModals();
                
                // Recarregar página para ver mudanças
                window.location.reload();
            } else {
                // Erro
                throw new Error(result.detail || result.message || JSON.stringify(result));
            }

        } catch (error) {
            console.error('Erro ao salvar transação:', error);
            alert('Erro ao salvar transação: ' + error.message);
        } finally {
            // Reabilitar botão
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    }

    validateFormData(data) {
        const requiredFields = ['amount', 'direction', 'currency', 'origin', 'category', 'payment_method', 'account'];
        
        for (const field of requiredFields) {
            if (!data[field]) {
                alert(`O campo ${this.getFieldLabel(field)} é obrigatório`);
                return false;
            }
        }

        // Validar valor
        if (isNaN(data.amount) || data.amount <= 0) {
            alert('O valor deve ser maior que zero');
            return false;
        }

        // Validações específicas por origem
        if (data.origin === 'INSTALLMENT') {
            if (!data.installments || data.installments < 2) {
                alert('Para parcelamento, informe o número de parcelas (mínimo 2)');
                return false;
            }
        }

        if (data.origin === 'RECURRENT') {
            if (!data.recurrence_frequency) {
                alert('Para transação recorrente, selecione uma frequência');
                return false;
            }
        }

        return true;
    }

    getFieldLabel(fieldId) {
        const labels = {
            'amount': 'Valor',
            'direction': 'Tipo de Transação',
            'currency': 'Moeda',
            'origin': 'Origem',
            'category': 'Categoria',
            'payment_method': 'Método de Pagamento',
            'account': 'Conta'
        };
        return labels[fieldId] || fieldId;
    }

    collectFormData() {
        const form = document.getElementById('transactionForm');
        const data = {};

        // Coletar campos básicos
        data.amount = parseFloat(form.querySelector('#amount').value);
        data.direction = form.querySelector('input[name="direction"]:checked')?.value;
        data.currency = this.getTomSelectValue('currency');
        data.origin = this.getTomSelectValue('origin');
        data.category = this.getTomSelectValue('category');
        data.payment_method = this.getTomSelectValue('payment_method');
        data.account = this.getTomSelectValue('account');
        
        // Data e hora
        const occurredAt = form.querySelector('#occurred_at');
        if (occurredAt) {
            data.occurred_at = occurredAt.value;
        }

        // Descrição
        const description = form.querySelector('#description');
        if (description && description.value.trim()) {
            data.description = description.value.trim();
        }

        // Tags
        const tags = this.getTomSelectValue('tags');
        if (tags) {
            data.tags = Array.isArray(tags) ? tags : [tags];
        }

        // Campos dinâmicos
        const origin = data.origin;
        if (origin === 'RECURRENT') {
            data.recurrence_frequency = this.getTomSelectValue('recurrence_frequency');
            
            const maxRecurrences = form.querySelector('#max_recurrences');
            if (maxRecurrences && maxRecurrences.value) {
                data.max_recurrences = parseInt(maxRecurrences.value);
            }
        } else if (origin === 'INSTALLMENT') {
            const installments = form.querySelector('#installments');
            if (installments && installments.value) {
                data.installments = parseInt(installments.value);
            }

            const interestRate = form.querySelector('#interest_rate');
            if (interestRate) {
                data.interest_rate = interestRate.value ? parseFloat(interestRate.value) : 0;
            }
        }

        return data;
    }

    getTomSelectValue(selectId) {
        const instance = this.tomSelectInstances[selectId];
        if (instance) {
            const value = instance.getValue();
            return value && value !== '' ? value : null;
        }
        
        // Fallback para elemento normal
        const element = document.getElementById(selectId);
        if (!element) return null;
        
        // Para selects múltiplos
        if (element.multiple) {
            return Array.from(element.selectedOptions).map(option => option.value);
        }
        
        return element.value || null;
    }

    async deleteTransaction() {
        if (!this.currentTransactionId) return;

        if (!confirm('Tem certeza que deseja excluir esta transação? Esta ação não pode ser desfeita.')) {
            return;
        }

        try {
            const response = await fetch(`/api/transactions/${this.currentTransactionId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                alert('Transação excluída com sucesso!');
                this.closeAllModals();
                window.location.reload();
            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Erro ao excluir transação');
            }
        } catch (error) {
            console.error('Erro ao excluir transação:', error);
            alert('Erro: ' + error.message);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.transactionManager = new TransactionManager();
});