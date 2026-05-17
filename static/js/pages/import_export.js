// MyLedger - Import/Export JavaScript (CONECTADO AO BACKEND)
// Funcionalidades da tela de importação e exportação de dados

(function () {
    'use strict';

    // ===== DOM Elements =====
    const importZone = document.getElementById('importZone');
    const fileInput = document.getElementById('fileInput');
    const importPreview = document.getElementById('importPreview');
    const previewStats = document.getElementById('previewStats');
    const confirmModal = document.getElementById('confirmModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const confirmActionBtn = document.getElementById('confirmActionBtn');

    // ===== State =====
    let pendingAction = null;
    let pendingFile = null;

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(message, type = 'success') {
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function showConfirmModal(title, message, action, isDanger = false) {
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        pendingAction = action;

        if (isDanger) {
            confirmActionBtn.classList.add('btn-modal-danger');
            confirmActionBtn.classList.remove('btn-modal-confirm');
        } else {
            confirmActionBtn.classList.remove('btn-modal-danger');
            confirmActionBtn.classList.add('btn-modal-confirm');
        }

        confirmModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    window.closeConfirmModal = function () {
        confirmModal.style.display = 'none';
        document.body.style.overflow = '';
        pendingAction = null;
    };

    // ===== Export Functions (Backend) - ALTERADO =====
    window.exportData = function (format) {
        showToast(`Preparando exportação em ${format.toUpperCase()}...`, 'success');
        
        // Criar link de download usando fetch para melhor controle
        const url = `${window.exportUrl}?format=${format}&type=all`;
        
        // Usar fetch para baixar o arquivo
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na exportação');
            }
            
            // Obter o nome do arquivo do header Content-Disposition
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `myledger_export_${new Date().toISOString().split('T')[0]}.${format}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?(.+)"?/);
                if (match) filename = match[1];
            }
            
            // Converter resposta para blob
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            // Criar link de download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast(`Exportação em ${format.toUpperCase()} concluída!`, 'success');
        })
        .catch(error => {
            console.error('Erro na exportação:', error);
            showToast(`Erro ao exportar em ${format.toUpperCase()}`, 'error');
        });
    };

    window.exportAllData = function () {
        showConfirmModal(
            'Exportar Todos os Dados',
            'Tem certeza que deseja exportar todos os seus dados?',
            () => {
                window.exportData('json');
                closeConfirmModal();
            }
        );
    };

    // ===== Import Functions (Backend) =====
    function setupDragAndDrop() {
        if (!importZone) return;

        importZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            importZone.classList.add('drag-over');
        });

        importZone.addEventListener('dragleave', () => {
            importZone.classList.remove('drag-over');
        });

        importZone.addEventListener('drop', (e) => {
            e.preventDefault();
            importZone.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file) processFile(file);
        });

        importZone.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) processFile(file);
        });
    }

    async function processFile(file) {
        const extension = file.name.split('.').pop().toLowerCase();

        if (extension !== 'json' && extension !== 'csv') {
            showToast('Formato não suportado. Use JSON ou CSV.', 'error');
            return;
        }

        pendingFile = file;

        // Mostrar preview
        const formData = new FormData();
        formData.append('file', file);

        previewStats.innerHTML = `
            <div class="loading-preview">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Analisando arquivo...</p>
            </div>
        `;
        importZone.style.display = 'none';
        importPreview.style.display = 'block';

        // Simular preview (opcional)
        setTimeout(() => {
            previewStats.innerHTML = `
                <div class="preview-success">
                    <i class="fas fa-check-circle"></i>
                    <p><strong>${file.name}</strong></p>
                    <p>Tamanho: ${(file.size / 1024).toFixed(2)} KB</p>
                    <p>Formato: ${extension.toUpperCase()}</p>
                </div>
            `;
        }, 500);
    }

    window.cancelImport = function () {
        pendingFile = null;
        importZone.style.display = 'flex';
        importPreview.style.display = 'none';
        fileInput.value = '';
    };

    window.confirmImport = async function () {
        if (!pendingFile) return;

        // PEGAR OS VALORES DOS SELECTS
        const bankSelect = document.getElementById('import-bank');
        const formatSelect = document.getElementById('import-format');
        const fileInput = document.getElementById('fileInput');

        const bank = bankSelect ? bankSelect.value : '';
        const file_format = formatSelect ? formatSelect.value : '';

        // Validar
        if (!bank) {
            showToast('Por favor, selecione o banco', 'error');
            return;
        }

        if (!file_format) {
            showToast('Por favor, selecione o formato do arquivo', 'error');
            return;
        }

        if (!pendingFile) {
            showToast('Por favor, selecione um arquivo', 'error');
            return;
        }

        console.log('Importando:', { bank, file_format, file: pendingFile.name });

        const formData = new FormData();
        formData.append('file', pendingFile);
        formData.append('bank', bank);
        formData.append('file_format', file_format);

        showToast('Enviando arquivo para importação...', 'info');

        try {
            const response = await fetch(window.importUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: formData
            });

            const data = await response.json();
            console.log('Resposta:', data);

            if (response.ok && data.success) {
                let message = data.message || 'Importação concluída!';
                if (data.summary && data.summary.records_imported > 0) {
                    message = `✅ ${data.summary.records_imported} transações importadas com sucesso!`;
                }
                showToast(message, 'success');
                cancelImport();
                setTimeout(() => location.reload(), 2000);
            } else {
                const errorMsg = data.error || data.message || 'Erro na importação';
                showToast(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro de conexão com o servidor', 'error');
        }
    };

    window.downloadExample = function () {
        const exampleData = {
            export_date: new Date().toISOString(),
            version: '1.0',
            data: {
                transactions: [
                    {
                        description: "Supermercado",
                        amount: 342.50,
                        date: new Date().toISOString().split('T')[0],
                        type: "expense",
                        category: "Alimentação",
                        notes: "Compras do mês"
                    },
                    {
                        description: "Salário",
                        amount: 5000.00,
                        date: new Date().toISOString().split('T')[0],
                        type: "income",
                        category: "Trabalho",
                        notes: ""
                    }
                ]
            }
        };

        const dataStr = JSON.stringify(exampleData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `myledger_example_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast('Arquivo exemplo baixado!', 'success');
    };

    // ===== Data Management =====
    window.backupData = function () {
        window.exportData('json');
        showToast('Backup criado com sucesso!', 'success');
    };

    window.restoreBackup = function () {
        showConfirmModal(
            'Restaurar Backup',
            'Tem certeza que deseja restaurar um backup? Os dados atuais serão substituídos.',
            () => {
                fileInput.click();
                const originalOnChange = fileInput.onchange;
                fileInput.onchange = (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        pendingFile = file;
                        window.confirmImport();
                    }
                    fileInput.onchange = originalOnChange;
                };
                closeConfirmModal();
            }
        );
    };

    window.clearAllData = async function () {
        showConfirmModal(
            'Limpar Todos os Dados',
            'ATENÇÃO: Esta ação irá remover permanentemente TODOS os seus dados. Esta operação não pode ser desfeita.',
            async () => {
                try {
                    const response = await fetch(window.clearDataUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });

                    const data = await response.json();

                    if (data.success) {
                        showToast(data.message, 'success');
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        showToast(data.error || 'Erro ao limpar dados', 'error');
                    }
                } catch (error) {
                    console.error('Error clearing data:', error);
                    showToast('Erro ao conectar com o servidor', 'error');
                }
                closeConfirmModal();
            },
            true
        );
    };

    // ===== Event Listeners =====
    if (confirmActionBtn) {
        confirmActionBtn.addEventListener('click', () => {
            if (pendingAction) {
                pendingAction();
                closeConfirmModal();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && confirmModal && confirmModal.style.display === 'flex') {
            closeConfirmModal();
        }
    });

    if (confirmModal) {
        confirmModal.addEventListener('click', (e) => {
            if (e.target === confirmModal) {
                closeConfirmModal();
            }
        });
    }

    // ===== Initialize =====
    function init() {
        setupDragAndDrop();
    }

    init();
})();