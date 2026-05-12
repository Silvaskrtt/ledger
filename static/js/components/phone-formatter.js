/**
 * Formatação automática de telefone brasileiro
 * Padrão: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
 */

function formatBrazilianPhone(input) {
    let value = input.value.replace(/\D/g, ''); // Remove tudo que não é dígito
    
    if (value.length === 0) return;
    
    if (value.length <= 2) {
        input.value = value;
    } else if (value.length <= 7) {
        input.value = `(${value.slice(0, 2)}) ${value.slice(2)}`;
    } else if (value.length <= 11) {
        if (value.length === 11) {
            // Celular: (XX) 9XXXX-XXXX
            input.value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7)}`;
        } else {
            // Fixo: (XX) XXXX-XXXX
            input.value = `(${value.slice(0, 2)}) ${value.slice(2, 6)}-${value.slice(6)}`;
        }
    } else {
        // Limita a 11 dígitos
        input.value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7, 11)}`;
    }
}

function validateBrazilianPhone(phone) {
    const digits = phone.replace(/\D/g, '');
    
    if (digits.length === 0) return true; // Campo vazio é válido
    
    if (digits.length !== 10 && digits.length !== 11) {
        return false;
    }
    
    const ddd = parseInt(digits.slice(0, 2));
    if (ddd < 11 || ddd > 99) {
        return false;
    }
    
    const firstDigit = parseInt(digits[2]);
    if (firstDigit < 2 || firstDigit > 9) {
        return false;
    }
    
    return true;
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phoneInput');
    
    if (phoneInput) {
        // Aplicar formatação ao digitar
        phoneInput.addEventListener('input', function() {
            formatBrazilianPhone(this);
        });
        
        // Validar ao perder o foco
        phoneInput.addEventListener('blur', function() {
            if (this.value && !validateBrazilianPhone(this.value)) {
                this.classList.add('input-error');
                console.warn('Telefone inválido');
            } else {
                this.classList.remove('input-error');
            }
        });
        
        // Remover classe de erro ao começar a digitar
        phoneInput.addEventListener('focus', function() {
            this.classList.remove('input-error');
        });
    }
});
