// frontend/static/js/transactions/form.js
class TransactionForm {
    constructor() {
        this.form = document.getElementById('transactionForm');
        this.typeButtons = document.querySelectorAll('.btn-type');
        this.directionInput = document.getElementById('id_direction');
        this.init();
    }

    init() {
        this.setDefaultDateTime();
        this.setupTypeButtons();
        this.setupFormSubmit();
    }

    setDefaultDateTime() {
        const input = document.getElementById('id_occurred_at');
        if (input && !input.value) {
            // Ajustar para fuso horário local
            const now = new Date();
            const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
                .toISOString()
                .slice(0, 16);
            input.value = localDateTime;
        }
        
        // Configurar moeda e origem padrão
        const currencySelect = document.getElementById('id_currency');
        if (currencySelect) currencySelect.value = 'BRL';
        
        const originSelect = document.getElementById('id_origin');
        if (originSelect) originSelect.value = 'MANUAL';
    }

    setupTypeButtons() {
        this.typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.typeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.directionInput.value = btn.dataset.direction;
            });
        });
    }

    setupFormSubmit() {
        this.form.addEventListener('submit', async e => {
            e.preventDefault();
            await this.submitForm();
        });
    }

    async submitForm() {
        try {
            const formData = new FormData(this.form);
            
            // Coletar tags como array
            const tagsSelect = document.getElementById('id_tags');
            const tags = Array.from(tagsSelect.selectedOptions).map(option => parseInt(option.value));

            // Montar payload completo
            const payload = {
                amount: parseFloat(formData.get('amount')),
                occurred_at: formData.get('occurred_at'),
                direction: formData.get('direction'),
                currency: formData.get('currency') || 'BRL',
                origin: formData.get('origin') || 'MANUAL',
                id_category: parseInt(formData.get('id_category')),
                id_payment_method: parseInt(formData.get('id_payment_method')),
                id_account: parseInt(formData.get('id_account')),
                tags: tags
            };

            console.log('Enviando payload:', payload); // Para debug

            const response = await fetch('/api/transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                },
                body: JSON.stringify(payload)
            });

            const responseData = await response.json();
            
            if (response.ok) {
                alert('✅ Transação criada com sucesso!');
                // Redirecionar para o histórico
                window.location.href = "{% url 'transaction-history' %}";
            } else {
                // Mostrar erros detalhados
                let errorMessage = '❌ Erro ao salvar transação';
                if (responseData.detail) {
                    errorMessage = '❌ ' + responseData.detail;
                } else if (responseData.non_field_errors) {
                    errorMessage = '❌ ' + responseData.non_field_errors.join(', ');
                } else if (typeof responseData === 'object') {
                    const fieldErrors = Object.entries(responseData)
                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
                        .join('; ');
                    errorMessage = '❌ ' + fieldErrors;
                }
                alert(errorMessage);
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('❌ Erro de conexão. Verifique sua internet e tente novamente.');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TransactionForm();
});