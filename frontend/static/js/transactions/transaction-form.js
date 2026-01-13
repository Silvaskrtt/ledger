// frontend/static/js/transactions/transaction-form.js
class TransactionForm {
    constructor() {
        this.form = document.getElementById('transactionForm');
        if (!this.form) {
            console.error('Formulário não encontrado');
            return;
        }

        this.tomSelectInstances = {};
        this.dynamicFields = {};
        this.init();
    }

    init() {
        this.initTomSelects();
        this.setDefaults();
        this.bindEvents();
        this.setupOriginDependencies();
    }

    initTomSelects() {
        // Aguardar o TomSelectManager estar disponível e ter inicializado
        if (typeof window.tomSelectManager === 'undefined') {
            console.warn('TomSelectManager não está disponível ainda. Aguardando...');
            setTimeout(() => this.initTomSelects(), 300);
            return;
        }

        // Obter instâncias do TomSelectManager global
        const selectIds = [
            'account',
            'category', 
            'payment_method',
            'currency',
            'origin',
            'tags'
        ];

        selectIds.forEach(id => {
            const instance = window.tomSelectManager.getInstance(id);
            if (instance) {
                this.tomSelectInstances[id] = instance;
            }
        });

        // Configurar onChange para origin
        const originInstance = this.tomSelectInstances['origin'];
        if (originInstance) {
            originInstance.on('change', (value) => this.onOriginChange(value));
        }
    }

    onOriginChange(value) {
        this.hideDynamicFields();
        
        if (value === 'RECURRENT') {
            this.showRecurrenceFields();
        } else if (value === 'INSTALLMENT') {
            this.showInstallmentFields();
        }
    }

    setupOriginDependencies() {
        // Container para campos dinâmicos
        this.dynamicFieldsContainer = document.getElementById('dynamicFieldsContainer');
        if (!this.dynamicFieldsContainer) {
            console.error('Container de campos dinâmicos não encontrado');
            return;
        }
        
        // Criar campos dinâmicos
        this.createDynamicFields();
    }

    createDynamicFields() {
        // Campos para recorrência
        this.createRecurrenceField('recurrence_frequency', 'Frequência', [
            {value: 'DAILY', text: 'Diário'},
            {value: 'WEEKLY', text: 'Semanal'},
            {value: 'BIWEEKLY', text: 'Quinzenal'},
            {value: 'MONTHLY', text: 'Mensal'},
            {value: 'QUARTERLY', text: 'Trimestral'},
            {value: 'SEMIANNUAL', text: 'Semestral'},
            {value: 'ANNUAL', text: 'Anual'}
        ]);

        this.createDynamicField('max_recurrences', 'Número Máximo de Recorrências', 'number', {
            min: '1',
            max: '999',
            placeholder: 'Deixe em branco para ilimitado'
        });

        // Campos para parcelamento
        this.createDynamicField('installments', 'Número de Parcelas', 'number', {
            min: '2',
            max: '360',
            placeholder: 'Ex: 12'
        });

        this.createDynamicField('interest_rate', 'Taxa de Juros Mensal (%)', 'number', {
            min: '0',
            max: '100',
            step: '0.01',
            placeholder: '0 para sem juros',
            value: '0'
        });

        // Esconder todos inicialmente
        this.hideDynamicFields();
    }

    createRecurrenceField(name, label, options) {
        const container = document.createElement('div');
        container.id = `${name}_container`;
        container.className = 'fields dynamic-field';
        container.style.display = 'none';
        
        const labelEl = document.createElement('label');
        labelEl.htmlFor = name;
        labelEl.textContent = `${label}:`;
        
        const select = document.createElement('select');
        select.id = name;
        select.name = name;
        select.className = 'tom-select';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = `Selecione ${label.toLowerCase()}`;
        select.appendChild(defaultOption);
        
        if (options) {
            options.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                select.appendChild(opt);
            });
        }

        container.appendChild(labelEl);
        container.appendChild(select);
        this.dynamicFieldsContainer.appendChild(container);
        
        // Armazenar referência
        this.dynamicFields[name] = { element: container, type: 'select' };
    }

    createDynamicField(name, label, type = 'text', attributes = {}) {
        const container = document.createElement('div');
        container.id = `${name}_container`;
        container.className = 'fields dynamic-field';
        container.style.display = 'none';
        
        const labelEl = document.createElement('label');
        labelEl.htmlFor = name;
        labelEl.textContent = `${label}:`;
        
        const input = document.createElement('input');
        input.type = type;
        input.id = name;
        input.name = name;
        input.className = 'dynamic-input';
        
        // Aplicar atributos
        Object.keys(attributes).forEach(key => {
            input.setAttribute(key, attributes[key]);
            if (key === 'value') {
                input.value = attributes[key];
            }
        });

        container.appendChild(labelEl);
        container.appendChild(input);
        this.dynamicFieldsContainer.appendChild(container);
        
        // Armazenar referência
        this.dynamicFields[name] = { element: container, type: 'input' };
    }

    showRecurrenceFields() {
        this.showField('recurrence_frequency');
        this.showField('max_recurrences');
        
        // Inicializar TomSelect para frequência
        const frequencySelect = document.getElementById('recurrence_frequency');
        if (frequencySelect && !this.tomSelectInstances['recurrence_frequency']) {
            try {
                this.tomSelectInstances['recurrence_frequency'] = new TomSelect(frequencySelect, {
                    create: false,
                    placeholder: 'Selecione a frequência',
                    allowEmptyOption: false
                });
            } catch (error) {
                console.error('Erro ao inicializar TomSelect para frequência:', error);
            }
        }
    }

    showInstallmentFields() {
        this.showField('installments');
        this.showField('interest_rate');
    }

    showField(fieldName) {
        const field = this.dynamicFields[fieldName];
        if (field) {
            field.element.style.display = 'flex';
        }
    }

    hideDynamicFields() {
        Object.values(this.dynamicFields).forEach(field => {
            field.element.style.display = 'none';
        });
    }

    setDefaults() {
        // Data e hora atual
        const dateTimeInput = document.getElementById('occurred_at');
        if (dateTimeInput && !dateTimeInput.value) {
            const now = new Date();
            const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
                .toISOString()
                .slice(0, 16);
            dateTimeInput.value = localDateTime;
        }
        
        // Moeda padrão BRL
        const currencySelect = document.getElementById('currency');
        if (currencySelect) {
            this.tomSelectInstances['currency'].setValue('BRL');
        }
    }

    bindEvents() {
        // Botão cancelar
        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                window.location.href = '/transactions/list/';
            });
        }
        
        // Submit do formulário
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitForm();
        });
    }

    

    validateForm() {
        const errors = [];

        // Validar valor
        const amount = parseFloat(document.getElementById('amount').value);
        if (isNaN(amount) || amount <= 0) {
            errors.push('O valor deve ser maior que zero');
        }

        // Validar campos obrigatórios
        const requiredFields = [
            'category',
            'payment_method', 
            'account',
            'origin',
            'currency'
        ];
        
        requiredFields.forEach(fieldId => {
            const value = this.getTomSelectValue(fieldId);
            if (!value) {
                const fieldName = this.getFieldLabel(fieldId);
                errors.push(`${fieldName} é obrigatório`);
            }
        });

        // Validar origem específica
        const origin = this.getTomSelectValue('origin');
        if (origin === 'RECURRENT') {
            const frequency = this.getTomSelectValue('recurrence_frequency');
            if (!frequency) {
                errors.push('Para transação recorrente, selecione uma frequência');
            }
        } else if (origin === 'INSTALLMENT') {
            const installments = document.getElementById('installments');
            if (!installments || !installments.value || parseInt(installments.value) < 2) {
                errors.push('Para parcelamento, informe o número de parcelas (mínimo 2)');
            }
        }

        return { isValid: errors.length === 0, errors };
    }

    getFieldLabel(fieldId) {
        const labels = {
            'category': 'Categoria',
            'payment_method': 'Método de Pagamento',
            'account': 'Conta',
            'origin': 'Origem',
            'currency': 'Moeda'
        };
        return labels[fieldId] || fieldId;
    }

    async validateAccountBalance(accountId, amount, direction) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/`, {
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`Erro ao buscar conta: ${response.status}`);
            }
            
            const account = await response.json();
            
            // ✅ DEBUG detalhado
            console.log('🔍 Dados da conta recebidos:', account);
            console.log('📋 Campos disponíveis:', Object.keys(account));
            
            // ✅ CONVERTER todos os valores para número (segurança)
            const validatedAmount = Number(amount);
            const balance = Number(account.balance) || 0;
            const availableCredit = Number(account.available_credit) || 0;
            const creditLimit = Number(account.credit_limit) || 0;
            
            // ✅ DETERMINAR se é cartão (usando múltiplas fontes para compatibilidade)
            const isCreditCard = Boolean(
                account.is_credit_card === true || 
                account.type === 'CREDIT_CARD'
            );
            
            console.log('💰 Valores convertidos:', {
                isCreditCard,
                balance,
                availableCredit,
                creditLimit,
                validatedAmount,
                direction
            });
            
            // ✅ VALIDAÇÃO para saídas (OUT)
            if (direction === 'OUT') {
                if (isCreditCard) {
                    // Cartão de crédito: verificar limite disponível
                    console.log(`💳 Validação cartão: ${validatedAmount} <= ${availableCredit} ?`);
                    
                    if (validatedAmount > availableCredit) {
                        return {
                            valid: false,
                            message: this.formatCreditCardErrorMessage(
                                account.name,
                                availableCredit,
                                validatedAmount
                            )
                        };
                    }
                } else {
                    // Conta normal: verificar saldo
                    console.log(`🏦 Validação conta normal: ${validatedAmount} <= ${balance} ?`);
                    
                    if (validatedAmount > balance) {
                        return {
                            valid: false,
                            message: this.formatNormalAccountErrorMessage(
                                account.name,
                                balance,
                                validatedAmount
                            )
                        };
                    }
                }
            }
            
            // ✅ Entradas (IN) sempre são válidas
            return { valid: true };
            
        } catch (error) {
            console.error('❌ Erro na validação de saldo:', error);
            
            // Em caso de erro, não bloqueia mas registra o erro
            return {
                valid: true,
                warning: '⚠️ Não foi possível validar o saldo. Continue com cautela.'
            };
        }
    }

    // ✅ Funções auxiliares para mensagens
    formatCreditCardErrorMessage(accountName, availableCredit, amount) {
        return `❌ Limite de crédito insuficiente!\n\n` +
            `Cartão: ${accountName}\n` +
            `Crédito disponível: R$${availableCredit.toFixed(2)}\n` +
            `Valor da transação: R$${amount.toFixed(2)}\n\n` +
            `Dica: Pague parte da fatura para liberar mais crédito.`;
    }

    formatNormalAccountErrorMessage(accountName, currentBalance, amount) {
        return `❌ Saldo insuficiente!\n\n` +
            `Conta: ${accountName}\n` +
            `Saldo atual: R$${currentBalance.toFixed(2)}\n` +
            `Valor da transação: R$${amount.toFixed(2)}\n\n` +
            `Dica: Transfira dinheiro para esta conta primeiro.`;
    }

    async submitForm() {
        const validation = this.validateForm();
        if (!validation.isValid) {
            alert('❌ ' + validation.errors.join('\n'));
            return;
        }

        try {
            const formData = this.collectFormData();

            // ✅ Variáveis definidas antes de usar
            const accountId = formData.account;
            const amount = parseFloat(formData.amount);
            const direction = formData.direction;

            // ✅ DEBUG no console para ver todos os dados
            console.log('=== DEBUG TRANSAÇÃO ===');
            console.log('📤 Dados do formulário:', {
                account: accountId,
                amount: amount,
                direction: direction,
                currency: formData.currency,
                origin: formData.origin,
                payment_method: formData.payment_method,
                category: formData.category,
                occurred_at: formData.occurred_at,
                tags: formData.tags || []
            });
            console.log('=====================');

            const balanceValidation = await this.validateAccountBalance(
                accountId, 
                amount, 
                direction
            );

            if (!balanceValidation.valid) {
                alert('❌ ' + balanceValidation.message);
                return;
            }

            // Se tiver warning (mas é válida), mostrar alerta
            if (balanceValidation.warning) {
                const proceed = confirm(`⚠️ ${balanceValidation.warning}\n\nDeseja continuar mesmo assim?`);
                if (!proceed) return;
            }

            const response = await fetch('/api/transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(formData)
            });

            // DEBUG da resposta
            console.log('📥 Resposta do servidor:', {
                status: response.status,
                ok: response.ok
            });

            const responseText = await response.text();

            let responseData;
            try {
                responseData = JSON.parse(responseText);
            } catch (e) {
                console.error('Erro ao parsear resposta:', e);
                responseData = { detail: responseText };
            }
            
            if (response.ok) {
                console.log('✅ Transação criada com sucesso:', responseData);
                alert('✅ ' + (responseData.message || 'Transação criada com sucesso!'));
                window.location.href = '/transactions/list/';
            } else {
                console.error('❌ Erro do servidor:', responseData);
                this.handleApiError(responseData);
            }
        } catch (error) {
            console.error('❌ Erro ao enviar transação:', error);
            alert('❌ Erro de conexão. Verifique sua internet e tente novamente.');
        }
    }

    getTomSelectValue(selectId) {
        const tomSelect = this.tomSelectInstances[selectId];
        if (tomSelect) {
            const value = tomSelect.getValue();
            
            if (Array.isArray(value) && value.length === 0) return null;
            if (value === '' || value === null || value === undefined) return null;
            return value;
        }
        
        const element = document.getElementById(selectId);
        if (element) {
            const value = element.value;
            return value && value !== '' ? value : null;
        }
        
        return null;
    }

    collectFormData() {
        const account_value = this.getTomSelectValue('account');
        const category_value = this.getTomSelectValue('category');
        const payment_method_value = this.getTomSelectValue('payment_method');
        const tags_value = this.getTomSelectValue('tags') || [];
        
        const payload = {
            amount: parseFloat(document.getElementById('amount').value),
            occurred_at: document.getElementById('occurred_at').value,
            direction: document.querySelector('input[name="direction"]:checked').value,
            currency: this.getTomSelectValue('currency'),
            origin: this.getTomSelectValue('origin'),
            category: category_value,
            payment_method: payment_method_value,
            account: account_value,
            tags: tags_value
        };

        // Descrição
        const description = document.getElementById('description');
        if (description && description.value.trim()) {
            payload.description = description.value.trim();
        }

        // Campos específicos por origem
        const origin = payload.origin;
        
        if (origin === 'RECURRENT') {
            const frequency = this.getTomSelectValue('recurrence_frequency');
            if (frequency) {
                payload.recurrence_frequency = frequency;
            }

            const maxRecurrences = document.getElementById('max_recurrences');
            if (maxRecurrences && maxRecurrences.value) {
                payload.max_recurrences = parseInt(maxRecurrences.value);
            }
        } else if (origin === 'INSTALLMENT') {
            const installments = document.getElementById('installments');
            if (installments && installments.value) {
                payload.installments = parseInt(installments.value);
            }
            
            const interestRate = document.getElementById('interest_rate');
            if (interestRate) {
                payload.interest_rate = interestRate.value ? parseFloat(interestRate.value) : 0;
            }
        }

        return payload;
    }

    handleApiError(responseData) {
        let errorMessage = '❌ Erro ao salvar transação';
        
        if (responseData.detail) {
            errorMessage = '❌ ' + responseData.detail;
        } else if (responseData.non_field_errors) {
            errorMessage = '❌ ' + responseData.non_field_errors.join(', ');
        } else if (typeof responseData === 'object') {
            const fieldErrors = Object.entries(responseData)
                .map(([field, errors]) => {
                    const fieldName = this.getFieldLabel(field) || field;
                    return `${fieldName}: ${Array.isArray(errors) ? errors.join(', ') : errors}`;
                })
                .join('\n');
            errorMessage = '❌ Erros encontrados:\n' + fieldErrors;
        }
        
        alert(errorMessage);
    }

    getCSRFToken() {
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return csrfInput ? csrfInput.value : '';
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new TransactionForm();
});