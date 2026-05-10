// MyLedger - JavaScript de Login
// Funcionalidades da tela de login

(function () {
    'use strict';

    // ===== ALTERNAR VISIBILIDADE DA SENHA =====
    window.togglePassword = function () {
        const senhaInput = document.getElementById('id_password');
        const botaoAlternar = document.querySelector('.toggle-password i');

        if (!senhaInput || !botaoAlternar) return;

        if (senhaInput.type === 'password') {
            senhaInput.type = 'text';
            botaoAlternar.classList.remove('fa-eye');
            botaoAlternar.classList.add('fa-eye-slash');
        } else {
            senhaInput.type = 'password';
            botaoAlternar.classList.remove('fa-eye-slash');
            botaoAlternar.classList.add('fa-eye');
        }
    };

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const gruposFormulario = document.querySelectorAll('.form-group');
        gruposFormulario.forEach((grupo, indice) => {
            grupo.style.animation = `fadeUp 0.4s ease-out ${0.1 + indice * 0.05}s both`;
        });
    }

    // ===== EXIBIR ESTADO DE CARREGAMENTO =====
    function configurarEnvioFormulario() {
        const formulario = document.querySelector('.login-form');
        if (!formulario) return;

        formulario.addEventListener('submit', function (e) {
            const botao = this.querySelector('.btn-login');
            if (!botao) return;

            // Prevenir múltiplos envios
            if (botao.classList.contains('loading')) {
                e.preventDefault();
                return;
            }

            botao.classList.add('loading');
            const conteudoOriginal = botao.innerHTML;
            botao.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Entrando...';

            // Se houver erro, restaurar botão
            setTimeout(() => {
                if (botao.classList.contains('loading')) {
                    botao.classList.remove('loading');
                    botao.innerHTML = conteudoOriginal;
                }
            }, 10000);
        });
    }

    // ===== VALIDAÇÃO DE FORMULÁRIO EM TEMPO REAL =====
    function configurarValidacaoTempoReal() {
        const emailInput = document.getElementById('id_login');
        const senhaInput = document.getElementById('id_password');

        if (emailInput) {
            emailInput.addEventListener('input', function () {
                const pai = this.closest('.form-group');
                const spanErro = pai?.querySelector('.error-message');

                if (this.value && !this.value.includes('@')) {
                    if (!spanErro) {
                        const erro = document.createElement('span');
                        erro.className = 'error-message';
                        erro.textContent = 'Digite um e-mail válido';
                        pai?.appendChild(erro);
                        pai?.classList.add('error');
                    }
                } else {
                    if (spanErro) spanErro.remove();
                    pai?.classList.remove('error');
                }
            });
        }

        if (senhaInput) {
            senhaInput.addEventListener('input', function () {
                const pai = this.closest('.form-group');
                const spanErro = pai?.querySelector('.error-message');

                if (this.value && this.value.length < 6) {
                    if (!spanErro) {
                        const erro = document.createElement('span');
                        erro.className = 'error-message';
                        erro.textContent = 'A senha deve ter pelo menos 6 caracteres';
                        pai?.appendChild(erro);
                        pai?.classList.add('error');
                    }
                } else {
                    if (spanErro && spanErro.textContent.includes('6 caracteres')) {
                        spanErro.remove();
                        pai?.classList.remove('error');
                    }
                }
            });
        }
    }

    // ===== BOTÕES DE LOGIN SOCIAL (ESPAÇO RESERVADO) =====
    function configurarBotoesSociais() {
        const botaoGoogle = document.querySelector('.social-btn.google');
        const botaoGithub = document.querySelector('.social-btn.github');

        if (botaoGoogle) {
            botaoGoogle.addEventListener('click', function () {
                // Implementar OAuth do Google
                console.log('Login com Google clicado - Implementar OAuth aqui');
                // window.location.href = '/accounts/google/login/';
            });
        }

        if (botaoGithub) {
            botaoGithub.addEventListener('click', function () {
                // Implementar OAuth do GitHub
                console.log('Login com GitHub clicado - Implementar OAuth aqui');
                // window.location.href = '/accounts/github/login/';
            });
        }
    }

    // ===== GERENCIAMENTO DE FOCO =====
    function configurarGerenciamentoFoco() {
        const primeiroCampo = document.getElementById('id_login');
        if (primeiroCampo) {
            primeiroCampo.focus();
        }
    }

    // ===== ATALHOS DE TECLADO =====
    function configurarAtalhosTeclado() {
        document.addEventListener('keydown', function (e) {
            // Pressione 'Esc' para limpar o formulário
            if (e.key === 'Escape') {
                const emailInput = document.getElementById('id_login');
                const senhaInput = document.getElementById('id_password');
                if (emailInput) emailInput.value = '';
                if (senhaInput) senhaInput.value = '';
                if (emailInput) emailInput.focus();
            }
        });
    }

    // ===== PREVENIR ENVIO DUPLICADO =====
    function prevenirEnvioDuplicado() {
        const formulario = document.querySelector('.login-form');
        if (formulario) {
            formulario.addEventListener('submit', function () {
                const botaoEnviar = this.querySelector('.btn-login');
                if (botaoEnviar) {
                    botaoEnviar.disabled = true;
                    setTimeout(() => {
                        botaoEnviar.disabled = false;
                    }, 3000);
                }
            });
        }
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        configurarEnvioFormulario();
        configurarValidacaoTempoReal();
        configurarBotoesSociais();
        configurarGerenciamentoFoco();
        configurarAtalhosTeclado();
        prevenirEnvioDuplicado();

        // Registrar inicialização
        console.log('Página de login do MyLedger inicializada');
    });
})();