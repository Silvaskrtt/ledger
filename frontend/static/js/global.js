// frontend/static/js/global.js
let sidebar = document.querySelector(".sidebar");
let closeBtn = document.querySelector("#btn");
let searchBtn = document.querySelector(".bx-search");

closeBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    menuBtnChange();
})

searchBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    menuBtnChange();
})

function menuBtnChange() {
    if (sidebar.classList.contains("open")) {
        closeBtn.classList.replace("bx-menu", "bx-menu-alt-right");
    } else {
        closeBtn.classList.replace("bx-menu-alt-right", "bx-menu");
    }
}

window.BalanceValidator = {
    showSyncAlert: function(message) {
        const alertDiv = document.getElementById('balance-sync-alert');
        if (alertDiv) {
            const span = alertDiv.querySelector('span');
            if (span) span.textContent = message;
            alertDiv.style.display = 'block';
            
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 30000);
        }
    },
    
    syncAllBalances: function() {
        // Implementar sincronização
        console.log('Sincronizando saldos...');
    }
};

// Garantir que BalanceValidator existe
if (typeof window.BalanceValidator === 'undefined') {
    window.BalanceValidator = {
        showSyncAlert: function(message) {
            const alertDiv = document.getElementById('balance-sync-alert');
            if (alertDiv) {
                const span = alertDiv.querySelector('span');
                if (span) span.textContent = message;
                alertDiv.style.display = 'block';
                
                setTimeout(() => {
                    alertDiv.style.display = 'none';
                }, 30000);
            }
        },
        
        syncAllBalances: function() {
            // Implementar sincronização
            console.log('Sincronizando saldos...');
            fetch('/api/accounts/sync-balances/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                alert('✅ ' + data.message);
                location.reload();
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('❌ Erro ao sincronizar saldos');
            });
        }
    };
}

menuBtnChange();