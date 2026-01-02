// frontend/static/js/transactions/transaction-form.js
class TransactionForm {
    constructor() {
        this.form = document.getElementById('transactionForm');
        if (!this.form) {
            console.error('Formulário não encontrado');
            return;
        }

        this.tomSelectInstances = {};
        this.init();
    }

    init() {
        this.initTomSelects();
        this.setDefaults();
        this.bindEvents();
        this.setupFormSubmit();
    }

    initTomSelects() {
        const selectConfigs = [
            {
                id: 'id_account',
                config: {
                    create: false,
                    sortField: { field: 'text', direction: 'asc' },
                    placeholder: 'Selecione uma conta',
                    allowEmptyOption: false
                }
            },
            {
                id: 'id_category',
                config: {
                    create: false,
                    placeholder: 'Selecione uma categoria',
                    allowEmptyOption: false
                }
            },
            {
                id: 'id_payment_method',
                config: {
                    create: false,
                    placeholder: 'Selecione um método de pagamento',
                    allowEmptyOption: false
                }
            },
            {
                id: 'id_tags',
                config: {
                    plugins: ['remove_button'],
                    placeholder: 'Selecione tags (opcional)',
                    create: false,
                    maxItems: 10
                }
            }
        ];

        selectConfigs.forEach(({ id, config }) => {
            const element = document.getElementById(id);
            if (element) {
                try {
                    this.tomSelectInstances[id] = new TomSelect(element, config);
                } catch (error) {
                    console.error(`Erro ao inicializar TomSelect para ${id}:`, error);
                }
            }
        });
    }

    setDefaults() {
        const dateTimeInput = document.getElementById('id_occurred_at');
        if (dateTimeInput && !dateTimeInput.value) {
            const now = new Date();
            const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
                .toISOString().slice(0, 16);
            dateTimeInput.value = localDateTime;
        }

        const currencySelect = document.getElementById('id_currency');
        if (currencySelect) currencySelect.value = 'BRL';

        const originSelect = document.getElementById('id_origin');
        if (originSelect) originSelect.value = 'MANUAL';
    }

    bindEvents() {
        const cancelBtn = this.form.querySelector('button[type="reset"]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/transactions/list/';
            });
        }
    }

    setupFormSubmit() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitForm();
        });
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

    validateForm() {
        const errors = [];

        const amount = parseFloat(document.getElementById('id_amount').value);
        if (isNaN(amount) || amount <= 0) {
            errors.push('O valor deve ser maior que zero');
        }

        const requiredFields = ['id_category', 'id_payment_method', 'id_account'];
        requiredFields.forEach(fieldId => {
            const value = this.getTomSelectValue(fieldId);
            if (!value) {
                const fieldName = this.getFieldLabel(fieldId);
                errors.push(`${fieldName} é obrigatório`);
            }
        });

        return { isValid: errors.length === 0, errors };
    }

    getFieldLabel(fieldId) {
        const labels = {
            'id_category': 'Categoria',
            'id_payment_method': 'Método de Pagamento',
            'id_account': 'Conta'
        };
        return labels[fieldId] || fieldId;
    }

    async submitForm() {
        const validation = this.validateForm();
        if (!validation.isValid) {
            alert('❌ ' + validation.errors.join('\n'));
            return;
        }

        try {
            const amount = parseFloat(document.getElementById('id_amount').value);
            const occurred_at = document.getElementById('id_occurred_at').value;
            const direction = document.querySelector('input[name="direction"]:checked').value;
            const currency = document.getElementById('id_currency').value;
            const origin = document.getElementById('id_origin').value;

            const id_category = this.getTomSelectValue('id_category');
            const id_payment_method = this.getTomSelectValue('id_payment_method');
            const id_account = this.getTomSelectValue('id_account');
            
            const tagsSelect = document.getElementById('id_tags');
            const tags = tagsSelect ? 
                Array.from(tagsSelect.selectedOptions)
                    .map(option => option.value)
                    .filter(value => value && value !== '') : [];

            // Validação de UUIDs
            const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
            
            if (!uuidRegex.test(id_category)) {
                alert('❌ Selecione uma categoria válida.');
                return;
            }
            
            if (!uuidRegex.test(id_payment_method)) {
                alert('❌ Selecione um método de pagamento válido.');
                return;
            }

            const id_account_num = parseInt(id_account);
            if (isNaN(id_account_num)) {
                alert('❌ Selecione uma conta válida.');
                return;
            }

            const payload = {
                amount: amount,
                occurred_at: occurred_at,
                direction: direction,
                currency: currency,
                origin: origin,
                id_category: id_category,
                id_payment_method: id_payment_method,
                id_account: id_account_num,
                tags: tags
            };

            const response = await fetch('/api/transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(payload)
            });

            const responseData = await response.json();
            
            if (response.ok) {
                alert('✅ Transação criada com sucesso!');
                window.location.href = '/transactions/list/';
            } else {
                this.handleApiError(responseData);
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('❌ Erro de conexão. Verifique sua internet e tente novamente.');
        }
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

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    new TransactionForm();
});