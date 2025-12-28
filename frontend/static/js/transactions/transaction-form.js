// frontend/static/transactions/js/transaction-form.js

class TransactionForm {
    constructor() {
        this.form = document.getElementById('transactionForm');
        this.typeButtons = document.querySelectorAll('.type-btn');
        this.directionInput = document.getElementById('id_direction');
        this.init();
    }

    init() {
        this.setDefaultDateTime();
        this.setupTypeButtons();
        this.setupFormSubmit();
        this.setupBeforeUnload();
    }

    setDefaultDateTime() {
        const dateInput = document.getElementById('id_occurred_at');
        if (dateInput && !dateInput.value) {
            dateInput.value = new Date().toISOString().slice(0, 16);
        }
    }

    setupTypeButtons() {
        if (!this.typeButtons.length || !this.directionInput) return;
        
        this.typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.typeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.directionInput.value = btn.dataset.type;
            });
        });
    }

    setupFormSubmit() {
        if (!this.form) return;
        
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitForm();
        });
    }

    async submitForm() {
        try {
            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData.entries());
            
            const jsonData = this.prepareJsonData(data);
            
            const response = await fetch('/api/transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': data.csrfmiddlewaretoken
                },
                body: JSON.stringify(jsonData)
            });
            
            await this.handleResponse(response);
            
        } catch (error) {
            this.showError('Erro de conexão. Tente novamente.');
        }
    }

    prepareJsonData(data) {
        // Ajuste conforme seus modelos
        return {
            ...data,
            amount: parseFloat(data.amount),
            id_user: 1, // Ajuste: use usuário logado
            id_category: parseInt(data.id_category),
            id_payment_method: parseInt(data.id_payment_method),
            currency: data.currency || 'BRL',
            origin: data.origin || 'MANUAL' // Baseado no seu modelo
        };
    }

    async handleResponse(response) {
        if (response.ok) {
            const result = await response.json();
            this.showSuccess('✅ Transação criada com sucesso!');
            setTimeout(() => {
                window.location.href = '/api/transactions/';
            }, 1500);
        } else {
            const error = await response.json();
            this.showError('❌ Erro: ' + (error.detail || JSON.stringify(error)));
        }
    }

    showError(message) {
        alert(message);
        // Ou use um sistema de notificação mais sofisticado
    }

    showSuccess(message) {
        alert(message);
        // Ou use um sistema de notificação mais sofisticado
    }

    setupBeforeUnload() {
        window.addEventListener('beforeunload', (e) => {
            if (this.form && this.hasFormData()) {
                e.preventDefault();
                e.returnValue = 'Você tem dados não salvos. Tem certeza que deseja sair?';
            }
        });
    }

    hasFormData() {
        const formData = new FormData(this.form);
        for (let value of formData.values()) {
            if (value) return true;
        }
        return false;
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new TransactionForm();
});