// MyLedger - JavaScript de Recuperação de Senha
// Funcionalidades da tela de recuperação de senha

(function () {
    'use strict';

    // ===== Elementos do DOM =====
    const formularioReset = document.querySelector('.reset-form');
    const inputEmail = document.getElementById('id_email');
    const botaoEnviar = document.querySelector('.btn-reset');
    const modalSucesso = document.getElementById('successModal');
    const toastCarregando = document.getElementById('loadingToast');
    const toastSucesso = document.getElementById('successToast');
    const toastErro = document.getElementById('errorToast');

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const elementos = document.querySelectorAll('.message-box, .reset-form, .help-text');
        elementos.forEach((elemento, indice) => {
            elemento.style.animation = `fadeUp 0.5s ease-out ${0.2 + indice * 0.1}s both`;
        });
    }

    // ===== EXIBIR NOTIFICAÇÃO =====
    function exibirNotificacao(tipo, mensagem) {
        let notificacao = null;

        if (tipo === 'loading') {
            notificacao = toastCarregando;
            const spanMensagem = notificacao?.querySelector('span');
            if (spanMensagem) spanMensagem.textContent = mensagem || 'Enviando link de redefinição...';
        } else if (tipo === 'success') {
            notificacao = toastSucesso;
            const spanMensagem = document.getElementById('toastMessage');
            if (spanMensagem) spanMensagem.textContent = mensagem || 'Link de redefinição enviado com sucesso!';
        } else {
            notificacao = toastErro;
            const spanMensagem = document.getElementById('errorToastMessage');
            if (spanMensagem) spanMensagem.textContent = mensagem || 'Algo deu errado. Tente novamente.';
        }

        if (notificacao) {
            notificacao.style.display = 'flex';
            setTimeout(() => {
                notificacao.style.opacity = '0';
                notificacao.style.transition = 'opacity 0.3s';
                setTimeout(() => {
                    notificacao.style.display = 'none';
                    notificacao.style.opacity = '1';
                }, 300);
            }, tipo === 'loading' ? 1000 : 3000);
        }
    }

    function esconderToastCarregando() {
        if (toastCarregando) {
            toastCarregando.style.display = 'none';
        }
    }

    // ===== EXIBIR MODAL DE SUCESSO =====
    window.fecharModalSucesso = function () {
        if (modalSucesso) {
            modalSucesso.style.display = 'none';
            // Redirecionar para o login após fechar o modal
            setTimeout(() => {
                window.location.href = '/accounts/login/';
            }, 300);
        }
    };

    function exibirModalSucesso() {
        if (modalSucesso) {
            modalSucesso.style.display = 'flex';
        }
    }

    // ===== VALIDAR E-MAIL =====
    function isEmailValido(email) {
        const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regexEmail.test(email);
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

    function limparErroCampo(campo) {
        const grupo = campo.closest('.form-group');
        if (grupo) {
            const erro = grupo.querySelector('.error-message');
            if (erro) erro.remove();
            grupo.classList.remove('error');
            grupo.classList.add('success');
        }
    }

    // ===== VALIDAÇÃO DE E-MAIL AO DIGITAR =====
    function configurarValidacaoEmail() {
        if (!inputEmail) return;

        inputEmail.addEventListener('input', function () {
            const valor = this.value.trim();

            if (valor && isEmailValido(valor)) {
                limparErroCampo(this);
            } else if (valor && !isEmailValido(valor)) {
                exibirErroCampo(this, 'Digite um endereço de e-mail válido');
            } else {
                const grupo = this.closest('.form-group');
                if (grupo) {
                    const erro = grupo.querySelector('.error-message');
                    if (erro && erro.textContent.includes('e-mail válido')) {
                        erro.remove();
                    }
                    grupo.classList.remove('error', 'success');
                }
            }
        });
    }

    // ===== SIMULAR CHAMADA DE API =====
    function simularChamadaApi(url, dados) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                // Simular resposta bem-sucedida
                if (dados.email && isEmailValido(dados.email)) {
                    resolve({ success: true, message: 'Link de redefinição enviado' });
                } else {
                    reject(new Error('Endereço de e-mail inválido'));
                }
            }, 2000);
        });
    }

    // ===== CHAMADA REAL DE API (para implementação real) =====
    async function enviarEmailRedefinicaoSenha(email) {
        const tokenCsrf = obterTokenCsrf();

        const resposta = await fetch('/api/auth/password/reset/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': tokenCsrf
            },
            body: JSON.stringify({ email: email })
        });

        if (!resposta.ok) {
            const erro = await resposta.json();
            throw new Error(erro.message || 'Falha ao enviar e-mail de redefinição');
        }

        return await resposta.json();
    }

    // ===== OBTER TOKEN CSRF =====
    function obterTokenCsrf() {
        const valorCookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return valorCookie || '';
    }

    // ===== PROCESSAR ENVIO DO FORMULÁRIO =====
    async function processarEnvio(e) {
        e.preventDefault();

        if (!inputEmail) return;

        const email = inputEmail.value.trim();

        // Validar e-mail
        if (!email) {
            exibirErroCampo(inputEmail, 'Digite seu endereço de e-mail');
            return;
        }

        if (!isEmailValido(email)) {
            exibirErroCampo(inputEmail, 'Digite um endereço de e-mail válido');
            return;
        }

        // Exibir estado de carregamento
        if (botaoEnviar) {
            botaoEnviar.classList.add('loading');
            const conteudoOriginal = botaoEnviar.innerHTML;
            botaoEnviar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
            botaoEnviar.disabled = true;

            // Armazenar conteúdo original para depois
            botaoEnviar.setAttribute('data-original', conteudoOriginal);
        }

        exibirNotificacao('loading', 'Enviando link de redefinição...');

        try {
            // Usar API real ou simulação
            const resultado = await simularChamadaApi('/api/auth/password/reset/', { email: email });
            // const resultado = await enviarEmailRedefinicaoSenha(email);

            esconderToastCarregando();

            // Exibir modal de sucesso para melhor UX
            exibirModalSucesso();

            // Limpar formulário
            inputEmail.value = '';

        } catch (erro) {
            esconderToastCarregando();
            exibirNotificacao('error', erro.message || 'Falha ao enviar e-mail de redefinição. Tente novamente.');
        } finally {
            // Resetar estado do botão
            if (botaoEnviar) {
                botaoEnviar.classList.remove('loading');
                const conteudoOriginal = botaoEnviar.getAttribute('data-original');
                if (conteudoOriginal) {
                    botaoEnviar.innerHTML = conteudoOriginal;
                }
                botaoEnviar.disabled = false;
            }
        }
    }

    // ===== LISTENER DO FORMULÁRIO =====
    if (formularioReset) {
        formularioReset.addEventListener('submit', processarEnvio);
    }

    // ===== CLICAR FORA DO MODAL =====
    if (modalSucesso) {
        modalSucesso.addEventListener('click', function (e) {
            if (e.target === modalSucesso) {
                fecharModalSucesso();
            }
        });
    }

    // ===== PRESSIONAR ESC PARA FECHAR O MODAL =====
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modalSucesso && modalSucesso.style.display === 'flex') {
            fecharModalSucesso();
        }
    });

    // ===== GERENCIAMENTO DE FOCO =====
    function configurarGerenciamentoFoco() {
        if (inputEmail) {
            setTimeout(() => {
                inputEmail.focus();
            }, 100);
        }
    }

    // ===== LEMBRAR ÚLTIMO E-MAIL (opcional) =====
    function carregarUltimoEmail() {
        const emailSalvo = localStorage.getItem('reset_email');
        if (emailSalvo && inputEmail && !inputEmail.value) {
            inputEmail.value = emailSalvo;
            // Opcional: auto-validar
            if (isEmailValido(emailSalvo)) {
                limparErroCampo(inputEmail);
            }
        }
    }

    function salvarEmail(email) {
        if (email && isEmailValido(email)) {
            localStorage.setItem('reset_email', email);
        }
    }

    // Salvar e-mail ao enviar com sucesso
    if (formularioReset) {
        formularioReset.addEventListener('submit', function () {
            if (inputEmail && isEmailValido(inputEmail.value.trim())) {
                salvarEmail(inputEmail.value.trim());
            }
        });
    }

    // ===== TEMPORIZADOR DE REENVIO (opcional) =====
    let temporizadorAtivo = false;

    function iniciarTemporizador(segundos = 60) {
        if (!botaoEnviar) return;

        temporizadorAtivo = true;
        let tempoRestante = segundos;
        const textoOriginal = botaoEnviar.innerHTML;

        const intervalo = setInterval(() => {
            if (tempoRestante <= 0) {
                clearInterval(intervalo);
                botaoEnviar.disabled = false;
                botaoEnviar.innerHTML = textoOriginal;
                temporizadorAtivo = false;
            } else {
                botaoEnviar.disabled = true;
                botaoEnviar.innerHTML = `<i class="fas fa-clock"></i> Tente novamente em ${tempoRestante}s`;
                tempoRestante--;
            }
        }, 1000);
    }

    // ===== VERIFICAR PARÂMETROS DA URL =====
    function verificarParametrosUrl() {
        const parametrosUrl = new URLSearchParams(window.location.search);
        const email = parametrosUrl.get('email');
        const erro = parametrosUrl.get('error');

        if (email && inputEmail) {
            inputEmail.value = email;
            // Auto-validar
            if (isEmailValido(email)) {
                limparErroCampo(inputEmail);
            }
        }

        if (erro) {
            exibirNotificacao('error', decodeURIComponent(erro));
        }
    }

    // ===== AUTO-FOCO E LIMPEZA =====
    function configurarAutoLimpeza() {
        if (inputEmail) {
            inputEmail.addEventListener('focus', function () {
                if (this.value && !isEmailValido(this.value)) {
                    this.select();
                }
            });
        }
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        configurarValidacaoEmail();
        configurarGerenciamentoFoco();
        carregarUltimoEmail();
        verificarParametrosUrl();
        configurarAutoLimpeza();

        console.log('Página de recuperação de senha do MyLedger inicializada');
    });
})();