// frontend/static/js/core/balance-validator.js

/**
 * Validador de consistência de saldos
 * Verifica se saldos das contas estão consistentes com transações
 */

class BalanceValidator {
    static async checkAccountConsistency(accountId) {
        try {
            const response = await fetch(`/api/accounts/check-consistency/`);
            if (response.ok) {
                const data = await response.json();
                const accountResult = data.results.find(r => r.id_account === accountId);
                
                if (accountResult && !accountResult.is_consistent) {
                    console.warn('INCONSISTÊNCIA DETECTADA:', accountResult);
                    
                    // Mostrar alerta para o usuário
                    if (window.showMessage) {
                        window.showMessage(
                            `Inconsistência detectada na conta ${accountResult.name}. ` +
                            `Diferença: R$${accountResult.difference.toFixed(2)}. ` +
                            `Sincronize os saldos.`,
                            'warning'
                        );
                    }
                    
                    return accountResult;
                }
            }
            return null;
        } catch (error) {
            console.error('Erro ao verificar consistência:', error);
            return null;
        }
    }
    
    static async syncAllBalances() {
        try {
            const response = await fetch(`/api/accounts/sync-balances/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Saldos sincronizados:', data);
                
                if (window.showMessage) {
                    window.showMessage('Saldos sincronizados com sucesso!', 'success');
                }
                
                // Recarregar dados se estiver em página de contas
                if (typeof fetchAccounts === 'function') {
                    fetchAccounts();
                }
                
                return data;
            }
        } catch (error) {
            console.error('Erro ao sincronizar saldos:', error);
            return null;
        }
    }
    
    static async validateTransaction(accountId, amount, direction) {
        // Buscar dados da conta
        const account = await this.getAccount(accountId);
        if (!account) return { valid: true }; // Falha silenciosa
        
        if (account.type === 'CREDIT_CARD') {
            const availableCredit = account.available_credit || 0;
            if (direction === 'OUT' && amount > availableCredit) {
                return {
                    valid: false,
                    message: `Limite insuficiente. Disponível: R$${availableCredit.toFixed(2)}`
                };
            }
        } else {
            const currentBalance = account.balance || 0;
            if (direction === 'OUT' && amount > currentBalance) {
                return {
                    valid: false,
                    message: `Saldo insuficiente. Disponível: R$${currentBalance.toFixed(2)}`
                };
            }
        }
        
        return { valid: true };
    }
    
    static async getAccount(accountId) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Erro ao buscar conta:', error);
        }
        return null;
    }
}

// Adicionar ao contexto global
window.BalanceValidator = BalanceValidator;

// Verificar consistência ao carregar páginas de finanças
document.addEventListener('DOMContentLoaded', function() {
    const financialPages = [
        '/',
        '/transactions/',
        '/accounts/',
        '/managementCategories/'
    ];
    
    const currentPath = window.location.pathname;
    
    if (financialPages.some(page => currentPath.includes(page))) {
        // Verificar consistência a cada 5 minutos
        setInterval(() => {
            BalanceValidator.checkAccountConsistency();
        }, 5 * 60 * 1000); // 5 minutos
        
        // Verificar na primeira carga (após 2 segundos)
        setTimeout(() => {
            BalanceValidator.checkAccountConsistency();
        }, 2000);
    }
});