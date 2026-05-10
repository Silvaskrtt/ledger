// MyLedger - JavaScript de Gerenciamento de E-mails
// Funcionalidades da tela de gerenciamento de e-mails

(function () {
    'use strict';

    // ===== Elementos do DOM =====
    const formularioAdicionarEmail = document.querySelector('.add-email-form');
    const formularioListaEmails = document.getElementById('email-list-form');
    const modalExclusao = document.getElementById('deleteModal');
    const btnConfirmarExclusao = document.getElementById('confirmDeleteBtn');
    const toastSucesso = document.getElementById('successToast');
    const toastErro = document.getElementById('errorToast');
    let emailSelecionadoParaExcluir = null;

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

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const itensEmail = document.querySelectorAll('.email-item');
        itensEmail.forEach((item, indice) => {
            item.style.animation = `fadeUp 0.4s ease-out ${0.1 + indice * 0.05}s both`;
        });
    }

    // ===== VALIDAÇÃO DE E-MAIL =====
    function isEmailValido(email) {
        const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regexEmail.test(email);
    }

    // ===== VALIDAÇÃO DE E-MAIL EM TEMPO REAL =====
    function configurarValidacaoEmail() {
        const inputEmail = document.getElementById('id_email');

        if (inputEmail) {
            inputEmail.addEventListener('input', function () {
                const grupo = this.closest('.form-group');
                const valor = this.value;

                const erroExistente = grupo?.querySelector('.error-message');

                if (valor && !isEmailValido(valor)) {
                    if (!erroExistente) {
                        const erro = document.createElement('span');
                        erro.className = 'error-message';
                        erro.textContent = 'Digite um e-mail válido';
                        grupo?.appendChild(erro);
                    }
                    grupo?.classList.add('error');
                    grupo?.classList.remove('success');
                } else {
                    if (erroExistente && erroExistente.textContent.includes('e-mail')) {
                        erroExistente.remove();
                    }
                    if (valor && isEmailValido(valor)) {
                        grupo?.classList.add('success');
                        grupo?.classList.remove('error');
                    } else {
                        grupo?.classList.remove('success', 'error');
                    }
                }
            });
        }
    }

    // ===== EXIBIR ERRO NO CAMPO =====
    function exibirErroCampo(campo, mensagem) {
        const grupo = campo.closest('.form-group');
        if (!grupo) return;

        const erroExistente = grupo.querySelector('.error-message');
        if (erroExistente) erroExistente.remove();

        const erro = document.createElement('span');
        erro.className = 'error-message';
        erro.textContent = mensagem;
        grupo.appendChild(erro);
        grupo.classList.add('error');

        campo.focus();

        setTimeout(() => {
            if (erro.parentNode) {
                erro.remove();
                grupo.classList.remove('error');
            }
        }, 5000);
    }

    // ===== CONFIRMAR EXCLUSÃO =====
    window.confirmarExclusao = function () {
        const radioSelecionado = document.querySelector('input[name="email"]:checked');

        if (!radioSelecionado) {
            exibirNotificacao('error', 'Selecione um e-mail para remover');
            return false;
        }

        emailSelecionadoParaExcluir = radioSelecionado.value;

        if (modalExclusao) {
            modalExclusao.style.display = 'flex';
        }

        return false;
    };

    window.fecharModalExclusao = function () {
        if (modalExclusao) {
            modalExclusao.style.display = 'none';
        }
        emailSelecionadoParaExcluir = null;
    };

    // ===== PROCESSAR CONFIRMAÇÃO DE EXCLUSÃO =====
    if (btnConfirmarExclusao) {
        btnConfirmarExclusao.addEventListener('click', function () {
            if (emailSelecionadoParaExcluir && formularioListaEmails) {
                // Enviar o formulário com ação de remover
                const formulario = formularioListaEmails;
                const inputOculto = document.createElement('input');
                inputOculto.type = 'hidden';
                inputOculto.name = 'action_remove';
                inputOculto.value = 'remove';
                formulario.appendChild(inputOculto);
                formulario.submit();
            }
            fecharModalExclusao();
        });
    }

    // ===== CLICAR FORA DO MODAL =====
    if (modalExclusao) {
        modalExclusao.addEventListener('click', function (e) {
            if (e.target === modalExclusao) {
                fecharModalExclusao();
            }
        });
    }

    // ===== ESC PARA FECHAR O MODAL =====
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modalExclusao && modalExclusao.style.display === 'flex') {
            fecharModalExclusao();
        }
    });

    // ===== PROCESSAR ENVIO DE ADIÇÃO DE E-MAIL =====
    async function processarEnvioAdicionarEmail(e) {
        e.preventDefault();

        const inputEmail = document.getElementById('id_email');
        const botaoAdicionar = document.querySelector('.btn-add');

        if (!inputEmail) return;

        const email = inputEmail.value.trim();

        if (!email) {
            exibirErroCampo(inputEmail, 'Digite um endereço de e-mail');
            return;
        }

        if (!isEmailValido(email)) {
            exibirErroCampo(inputEmail, 'Digite um e-mail válido');
            return;
        }

        // Exibir estado de carregamento
        if (botaoAdicionar) {
            botaoAdicionar.classList.add('loading');
            const conteudoOriginal = botaoAdicionar.innerHTML;
            botaoAdicionar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adicionando...';
            botaoAdicionar.disabled = true;
            botaoAdicionar.setAttribute('data-original', conteudoOriginal);
        }

        try {
            // Enviar o formulário
            e.target.submit();
        } catch (erro) {
            exibirNotificacao('error', 'Erro ao adicionar e-mail. Tente novamente.');

            if (botaoAdicionar) {
                botaoAdicionar.classList.remove('loading');
                const conteudoOriginal = botaoAdicionar.getAttribute('data-original');
                if (conteudoOriginal) {
                    botaoAdicionar.innerHTML = conteudoOriginal;
                }
                botaoAdicionar.disabled = false;
            }
        }
    }

    // ===== CONFIGURAR AÇÕES DE E-MAIL =====
    function configurarAcoesEmail() {
        const botoesAcao = document.querySelectorAll('.btn-action');

        botoesAcao.forEach(botao => {
            botao.addEventListener('click', function (e) {
                const radioSelecionado = document.querySelector('input[name="email"]:checked');

                if (!radioSelecionado && this.name !== 'action_remove') {
                    e.preventDefault();
                    exibirNotificacao('error', 'Selecione um e-mail');
                    return false;
                }

                // Exibir estado de carregamento no botão clicado
                if (!this.classList.contains('btn-danger-action')) {
                    const conteudoOriginal = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
                    this.disabled = true;

                    setTimeout(() => {
                        this.innerHTML = conteudoOriginal;
                        this.disabled = false;
                    }, 3000);
                }
            });
        });
    }

    // ===== VERIFICAR PARÂMETROS DA URL =====
    function verificarParametrosUrl() {
        const parametrosUrl = new URLSearchParams(window.location.search);
        const sucesso = parametrosUrl.get('success');
        const erro = parametrosUrl.get('error');

        if (sucesso === 'email_added') {
            exibirNotificacao('success', 'E-mail adicionado com sucesso!');
        } else if (sucesso === 'email_verified') {
            exibirNotificacao('success', 'E-mail verificado com sucesso!');
        } else if (sucesso === 'email_primary') {
            exibirNotificacao('success', 'E-mail principal atualizado!');
        } else if (sucesso === 'email_removed') {
            exibirNotificacao('success', 'E-mail removido com sucesso!');
        } else if (sucesso === 'verification_sent') {
            exibirNotificacao('success', 'E-mail de verificação reenviado!');
        } else if (erro) {
            exibirNotificacao('error', decodeURIComponent(erro));
        }
    }

    // ===== ADICIONAR ANIMAÇÃO DO GRADIENTE =====
    function adicionarAnimacaoGradiente() {
        const orbes = document.querySelectorAll('.gradient-orb');
        orbes.forEach((orbe, indice) => {
            orbe.style.animationDelay = `${indice * 3}s`;
        });
    }

    // ===== GERENCIAMENTO DE FOCO =====
    function configurarGerenciamentoFoco() {
        const inputEmail = document.getElementById('id_email');
        if (inputEmail) {
            setTimeout(() => {
                inputEmail.focus();
            }, 100);
        }
    }

    // ===== PREVENIR ENVIO DUPLICADO =====
    let estaEnviando = false;

    function prevenirEnvioDuplicado() {
        if (formularioAdicionarEmail) {
            formularioAdicionarEmail.addEventListener('submit', function (e) {
                if (estaEnviando) {
                    e.preventDefault();
                    return;
                }
                estaEnviando = true;
                setTimeout(() => {
                    estaEnviando = false;
                }, 5000);
            });
        }
    }

    // ===== DESTACAR E-MAIL SELECIONADO =====
    function configurarDestaqueEmail() {
        const radios = document.querySelectorAll('input[name="email"]');

        radios.forEach(radio => {
            radio.addEventListener('change', function () {
                // Remover destaque de todos os itens
                document.querySelectorAll('.email-item').forEach(item => {
                    item.style.background = 'rgba(255, 255, 255, 0.04)';
                });

                // Destacar item selecionado
                const itemSelecionado = this.closest('.email-item');
                if (itemSelecionado) {
                    itemSelecionado.style.background = 'rgba(138, 79, 255, 0.1)';
                    itemSelecionado.style.borderColor = 'rgba(138, 79, 255, 0.3)';
                }
            });
        });
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        configurarValidacaoEmail();
        configurarAcoesEmail();
        verificarParametrosUrl();
        adicionarAnimacaoGradiente();
        configurarGerenciamentoFoco();
        prevenirEnvioDuplicado();
        configurarDestaqueEmail();

        if (formularioAdicionarEmail) {
            formularioAdicionarEmail.addEventListener('submit', processarEnvioAdicionarEmail);
        }

        console.log('MyLedger - Página de gerenciamento de e-mails inicializada');
    });
})();