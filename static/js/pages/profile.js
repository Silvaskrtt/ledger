// MyLedger - JavaScript de Perfil
// Funcionalidades da tela de perfil do usuário

(function () {
    'use strict';

    // ===== Elementos do DOM =====
    const toastSucesso = document.getElementById('successToast');
    const toastErro = document.getElementById('errorToast');
    const modalEditarNome = document.getElementById('editNameModal');
    const modalEditarTelefone = document.getElementById('editPhoneModal');
    const modalExcluirConta = document.getElementById('deleteAccountModal');

    let campoEditandoAtual = null;

    // ===== EXIBIR NOTIFICAÇÃO =====
    function exibirNotificacao(tipo, mensagem) {
        const notificacao = tipo === 'success' ? toastSucesso : toastErro;
        const spanMensagem = tipo === 'success'
            ? document.getElementById('toastMessage')
            : document.getElementById('errorToastMessage');

        if (spanMensagem) spanMensagem.textContent = mensagem;
        if (notificacao) {
            notificacao.style.display = 'flex';
            setTimeout(() => {
                notificacao.style.opacity = '0';
                notificacao.style.transition = 'opacity 0.3s';
                setTimeout(() => {
                    notificacao.style.display = 'none';
                    notificacao.style.opacity = '1';
                }, 300);
            }, 3000);
        }
    }

    // ===== FUNÇÃO GENÉRICA PARA ENVIAR AO BACKEND =====
    async function salvarNoBackend(campo, valor) {
        try {
            const response = await fetch('/accounts/profile/update-ajax/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ [campo]: valor })
            });

            const data = await response.json();

            if (data.success) {
                return { success: true };
            } else {
                return { success: false, error: data.error || 'Erro ao salvar' };
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            return { success: false, error: 'Erro de conexão com o servidor' };
        }
    }

    // ===== OBTER CSRF TOKEN =====
    function getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookieValue ? cookieValue.split('=')[1] : '';
    }

    // ===== OPÇÕES DE AVATAR =====
    window.mostrarOpcoesAvatar = function () {
        exibirNotificacao('info', 'Funcionalidade de avatar em breve!');
    };

    // ===== EDITAR CAMPO =====
    window.editarCampo = function (campo) {
        campoEditandoAtual = campo;

        if (campo === 'name') {
            const nomeAtual = document.getElementById('displayName').textContent;
            document.getElementById('editNameInput').value = nomeAtual;
            if (modalEditarNome) modalEditarNome.style.display = 'flex';
        } else if (campo === 'phone') {
            const telefoneAtual = document.getElementById('displayPhone').textContent;
            const telefoneSemMascara = telefoneAtual !== 'Não informado' ? telefoneAtual : '';
            document.getElementById('editPhoneInput').value = telefoneSemMascara;
            if (modalEditarTelefone) modalEditarTelefone.style.display = 'flex';
        }
    };

    // ===== SALVAR NOME =====
    window.salvarNome = async function () {
        const novoNome = document.getElementById('editNameInput').value.trim();

        if (!novoNome) {
            exibirNotificacao('error', 'Digite um nome válido');
            return;
        }

        if (novoNome.length < 3) {
            exibirNotificacao('error', 'O nome deve ter pelo menos 3 caracteres');
            return;
        }

        // Mostra loading no botão
        const botaoSalvar = document.querySelector('#editNameModal .btn-modal-confirm');
        const textoOriginal = botaoSalvar.textContent;
        botaoSalvar.textContent = 'Salvando...';
        botaoSalvar.disabled = true;

        // Envia para o backend
        const resultado = await salvarNoBackend('name', novoNome);

        if (resultado.success) {
            // Atualiza exibição na interface
            document.getElementById('displayName').textContent = novoNome;
            document.getElementById('profileName').textContent = novoNome;

            fecharModalEdicao();
            exibirNotificacao('success', 'Nome atualizado com sucesso!');
        } else {
            exibirNotificacao('error', resultado.error || 'Erro ao atualizar nome');
        }

        // Restaura botão
        botaoSalvar.textContent = textoOriginal;
        botaoSalvar.disabled = false;
    };

    // ===== SALVAR TELEFONE =====
    window.salvarTelefone = async function () {
        let novoTelefone = document.getElementById('editPhoneInput').value.trim();

        if (!novoTelefone) {
            exibirNotificacao('error', 'Digite um número de telefone válido');
            return;
        }

        // Remove caracteres não numéricos para validação
        const numerosApenas = novoTelefone.replace(/\D/g, '');

        if (numerosApenas.length < 10 || numerosApenas.length > 11) {
            exibirNotificacao('error', 'Telefone deve ter 10 ou 11 dígitos');
            return;
        }

        // Mostra loading no botão
        const botaoSalvar = document.querySelector('#editPhoneModal .btn-modal-confirm');
        const textoOriginal = botaoSalvar.textContent;
        botaoSalvar.textContent = 'Salvando...';
        botaoSalvar.disabled = true;

        // Envia para o backend
        const resultado = await salvarNoBackend('phone', novoTelefone);

        if (resultado.success) {
            // Atualiza exibição na interface
            document.getElementById('displayPhone').textContent = novoTelefone;

            fecharModalEdicao();
            exibirNotificacao('success', 'Telefone atualizado com sucesso!');
        } else {
            exibirNotificacao('error', resultado.error || 'Erro ao atualizar telefone');
        }

        // Restaura botão
        botaoSalvar.textContent = textoOriginal;
        botaoSalvar.disabled = false;
    };

    // ===== FECHAR MODAL DE EDIÇÃO =====
    window.fecharModalEdicao = function () {
        if (modalEditarNome) modalEditarNome.style.display = 'none';
        if (modalEditarTelefone) modalEditarTelefone.style.display = 'none';
        campoEditandoAtual = null;
    };

    // ===== CLICAR FORA DO MODAL =====
    document.addEventListener('click', function (e) {
        if (modalEditarNome && e.target === modalEditarNome) {
            fecharModalEdicao();
        }
        if (modalEditarTelefone && e.target === modalEditarTelefone) {
            fecharModalEdicao();
        }
        if (modalExcluirConta && e.target === modalExcluirConta) {
            fecharModalExclusao();
        }
    });

    // ===== ESC PARA FECHAR O MODAL =====
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            fecharModalEdicao();
            fecharModalExclusao();
        }
    });

    // ===== FUNÇÕES DE NAVEGAÇÃO =====
    window.irParaGerenciamentoEmail = function () {
        window.location.href = '/accounts/email/';
    };

    window.irParaAlterarSenha = function () {
        window.location.href = '/accounts/password/change/';
    };

    window.irParaDoisFatores = function () {
        exibirNotificacao('info', 'Funcionalidade de 2FA em breve!');
    };

    window.irParaSessoes = function () {
        exibirNotificacao('info', 'Gerenciamento de sessões em breve!');
    };

    window.alterarIdioma = function () {
        exibirNotificacao('info', 'Funcionalidade de idiomas em breve!');
    };

    window.alterarMoeda = function () {
        exibirNotificacao('info', 'Funcionalidade de moeda em breve!');
    };

    // ===== EXCLUIR CONTA =====
    window.confirmarExcluirConta = function () {
        if (modalExcluirConta) {
            modalExcluirConta.style.display = 'flex';
        }
    };

    window.fecharModalExclusao = function () {
        if (modalExcluirConta) {
            modalExcluirConta.style.display = 'none';
        }
    };

    window.excluirConta = function () {
        exibirNotificacao('error', 'Esta ação será implementada em breve');
        fecharModalExclusao();
    };

    // ===== EXPORTAR DADOS =====
    window.exportarDados = function () {
        exibirNotificacao('success', 'Preparando exportação de dados...');

        setTimeout(() => {
            const dados = {
                usuario: {
                    nome: document.getElementById('profileName').textContent,
                    email: document.getElementById('profileEmail').textContent,
                    telefone: document.getElementById('displayPhone').textContent,
                    membroDesde: document.querySelector('.info-row:last-child .info-value')?.textContent || 'Não informado'
                },
                dataExportacao: new Date().toISOString()
            };

            const dadosStr = JSON.stringify(dados, null, 2);
            const blob = new Blob([dadosStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `myledger_dados_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            exibirNotificacao('success', 'Dados exportados com sucesso!');
        }, 1000);
    };

    // ===== CONFIRMAR SAÍDA =====
    window.confirmarSair = function () {
        if (confirm('Tem certeza que deseja sair da sua conta?')) {
            window.location.href = '/accounts/logout/';
        }
    };

    // ===== ALTERNAR DOIS FATORES =====
    const alternarDoisFatores = document.getElementById('twoFactorToggle');
    if (alternarDoisFatores) {
        alternarDoisFatores.addEventListener('change', function () {
            if (this.checked) {
                exibirNotificacao('info', 'Configuração de 2FA em breve!');
                this.checked = false;
            }
        });
    }

    // ===== ALTERNAR NOTIFICAÇÕES POR E-MAIL =====
    const notificacoesEmail = document.getElementById('emailNotifications');
    if (notificacoesEmail) {
        notificacoesEmail.addEventListener('change', function () {
            const status = this.checked ? 'ativadas' : 'desativadas';
            exibirNotificacao('success', `Notificações por e-mail ${status} com sucesso!`);
        });
    }

    // ===== ADICIONAR ANIMAÇÃO DO GRADIENTE =====
    function adicionarAnimacaoGradiente() {
        const orbes = document.querySelectorAll('.gradient-orb');
        orbes.forEach((orbe, indice) => {
            orbe.style.animationDelay = `${indice * 3}s`;
        });
    }

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const secoes = document.querySelectorAll('.info-section, .security-section, .preferences-section, .danger-section, .logout-section');
        secoes.forEach((secao, indice) => {
            secao.style.animation = `fadeUp 0.4s ease-out ${0.1 + indice * 0.05}s both`;
        });
    }

    // ===== CARREGAR DADOS DO USUÁRIO DO BACKEND =====
    async function carregarDadosUsuario() {
        try {
            // Se precisar buscar dados atualizados do backend
            const response = await fetch('/accounts/profile/data/', {
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                }
            });

            if (response.ok) {
                const dados = await response.json();
                if (dados.name) {
                    document.getElementById('profileName').textContent = dados.name;
                    document.getElementById('displayName').textContent = dados.name;
                }
                if (dados.email) {
                    document.getElementById('profileEmail').textContent = dados.email;
                    document.getElementById('displayEmail').textContent = dados.email;
                }
                if (dados.phone) {
                    document.getElementById('displayPhone').textContent = dados.phone;
                }
            }
        } catch (error) {
            console.log('Usando dados do template inicial');
        }
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAnimacaoGradiente();
        adicionarAtrasosAnimacao();
        carregarDadosUsuario();

        console.log('MyLedger - Página de perfil inicializada');
    });
})();