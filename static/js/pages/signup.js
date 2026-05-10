// MyLedger - JavaScript de Cadastro
// Funcionalidades da tela de registro

(function () {
    'use strict';

    // ===== ALTERNAR VISIBILIDADE DA SENHA =====
    function iniciarAlternadoresSenha() {
        const botoesAlternar = document.querySelectorAll('.toggle-password');

        botoesAlternar.forEach(botao => {
            botao.addEventListener('click', function () {
                const idAlvo = this.getAttribute('data-target');
                const inputSenha = document.getElementById(idAlvo);
                const icone = this.querySelector('i');

                if (!inputSenha) return;

                if (inputSenha.type === 'password') {
                    inputSenha.type = 'text';
                    icone.classList.remove('fa-eye');
                    icone.classList.add('fa-eye-slash');
                } else {
                    inputSenha.type = 'password';
                    icone.classList.remove('fa-eye-slash');
                    icone.classList.add('fa-eye');
                }
            });
        });
    }

    // ===== VALIDAÇÃO DE SENHA EM TEMPO REAL =====
    function configurarValidacaoSenha() {
        const senha1 = document.getElementById('id_password1');
        const senha2 = document.getElementById('id_password2');

        if (senha1) {
            senha1.addEventListener('input', function () {
                validarForcaSenha(this.value);
                verificarSenhasIguais();
            });
        }

        if (senha2) {
            senha2.addEventListener('input', verificarSenhasIguais);
        }
    }

    function validarForcaSenha(senha) {
        const grupo = document.getElementById('id_password1')?.closest('.form-group');
        if (!grupo) return;

        let forca = 0;
        let mensagem = '';

        // Remover mensagem de força existente
        const forcaExistente = grupo.querySelector('.password-strength');
        if (forcaExistente) forcaExistente.remove();

        if (senha.length === 0) return;

        // Critérios de força
        if (senha.length >= 8) forca++;
        if (senha.match(/[a-z]/) && senha.match(/[A-Z]/)) forca++;
        if (senha.match(/[0-9]/)) forca++;
        if (senha.match(/[^a-zA-Z0-9]/)) forca++;

        // Determinar força
        if (forca <= 1) {
            mensagem = '🔴 Senha fraca';
        } else if (forca === 2) {
            mensagem = '🟡 Senha razoável';
        } else if (forca === 3) {
            mensagem = '🟢 Senha boa';
        } else {
            mensagem = '✅ Senha forte';
        }

        const elementoForca = document.createElement('small');
        elementoForca.className = 'help-text password-strength';
        elementoForca.textContent = mensagem;
        grupo.appendChild(elementoForca);
    }

    function verificarSenhasIguais() {
        const senha1 = document.getElementById('id_password1');
        const senha2 = document.getElementById('id_password2');
        const grupo = document.getElementById('id_password2')?.closest('.form-group');

        if (!senha1 || !senha2 || !grupo) return;

        const erroExistente = grupo.querySelector('.error-message');

        if (senha2.value && senha1.value !== senha2.value) {
            if (!erroExistente || !erroExistente.textContent.includes('iguais')) {
                if (erroExistente) erroExistente.remove();
                const erro = document.createElement('span');
                erro.className = 'error-message';
                erro.textContent = 'As senhas não coincidem';
                grupo.appendChild(erro);
            }
            grupo.classList.add('error');
            grupo.classList.remove('success');
        } else {
            if (erroExistente && erroExistente.textContent.includes('coincidem')) {
                erroExistente.remove();
            }
            if (senha2.value && senha1.value === senha2.value) {
                grupo.classList.add('success');
                grupo.classList.remove('error');
            } else {
                grupo.classList.remove('success', 'error');
            }
        }
    }

    // ===== VALIDAÇÃO DE E-MAIL =====
    function configurarValidacaoEmail() {
        const inputEmail = document.getElementById('id_email');

        if (inputEmail) {
            inputEmail.addEventListener('input', function () {
                const grupo = this.closest('.form-group');
                const valor = this.value;
                const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

                const erroExistente = grupo?.querySelector('.error-message');

                if (valor && !regexEmail.test(valor)) {
                    if (!erroExistente) {
                        const erro = document.createElement('span');
                        erro.className = 'error-message';
                        erro.textContent = 'Digite um e-mail válido';
                        grupo?.appendChild(erro);
                    }
                    grupo?.classList.add('error');
                    grupo?.classList.remove('success');
                } else {
                    if (erroExistente && erroExistente.textContent.includes('e-mail válido')) {
                        erroExistente.remove();
                    }
                    if (valor && regexEmail.test(valor)) {
                        grupo?.classList.add('success');
                        grupo?.classList.remove('error');
                    } else {
                        grupo?.classList.remove('success', 'error');
                    }
                }
            });
        }
    }

    // ===== EXIBIR ESTADO DE CARREGAMENTO =====
    function configurarEnvioFormulario() {
        const formulario = document.querySelector('.signup-form');
        if (!formulario) return;

        formulario.addEventListener('submit', function (e) {
            const botao = this.querySelector('.btn-signup');
            if (!botao) return;

            // Validar senhas antes de enviar
            const senha1 = document.getElementById('id_password1');
            const senha2 = document.getElementById('id_password2');

            if (senha1 && senha2 && senha1.value !== senha2.value) {
                e.preventDefault();
                exibirErroCampo(senha2, 'As senhas não coincidem');
                return;
            }

            // Prevenir múltiplos envios
            if (botao.classList.contains('loading')) {
                e.preventDefault();
                return;
            }

            botao.classList.add('loading');
            const conteudoOriginal = botao.innerHTML;
            botao.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Criando conta...';

            // Timeout de segurança
            setTimeout(() => {
                if (botao.classList.contains('loading')) {
                    botao.classList.remove('loading');
                    botao.innerHTML = conteudoOriginal;
                }
            }, 10000);
        });
    }

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

        // Remover erro após 3 segundos
        setTimeout(() => {
            if (erro.parentNode) {
                erro.remove();
                grupo.classList.remove('error');
            }
        }, 3000);
    }

    // ===== MANIPULADOR DE LOGIN SOCIAL =====
    window.manipularLoginSocial = function (provedor) {
        console.log(`Login com ${provedor} clicado - Implementar OAuth aqui`);

        // Exemplo de implementação:
        // window.location.href = `/accounts/${provedor}/login/`;

        // Feedback visual
        const botao = document.querySelector(`.social-btn.${provedor}`);
        if (botao) {
            const conteudoOriginal = botao.innerHTML;
            botao.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            botao.disabled = true;

            setTimeout(() => {
                botao.innerHTML = conteudoOriginal;
                botao.disabled = false;
            }, 2000);
        }
    };

    // ===== VALIDAÇÃO DE NOME DE USUÁRIO =====
    function configurarValidacaoUsername() {
        const inputUsername = document.getElementById('id_username');

        if (inputUsername) {
            inputUsername.addEventListener('input', function () {
                const grupo = this.closest('.form-group');
                const valor = this.value;

                const erroExistente = grupo?.querySelector('.error-message');

                if (valor && valor.length < 3) {
                    if (!erroExistente || !erroExistente.textContent.includes('Usuário')) {
                        if (erroExistente) erroExistente.remove();
                        const erro = document.createElement('span');
                        erro.className = 'error-message';
                        erro.textContent = 'O nome de usuário deve ter pelo menos 3 caracteres';
                        grupo?.appendChild(erro);
                    }
                    grupo?.classList.add('error');
                    grupo?.classList.remove('success');
                } else if (valor && valor.length > 30) {
                    if (!erroExistente || !erroExistente.textContent.includes('30')) {
                        if (erroExistente) erroExistente.remove();
                        const erro = document.createElement('span');
                        erro.className = 'error-message';
                        erro.textContent = 'O nome de usuário deve ter menos de 30 caracteres';
                        grupo?.appendChild(erro);
                    }
                    grupo?.classList.add('error');
                    grupo?.classList.remove('success');
                } else {
                    if (erroExistente && (erroExistente.textContent.includes('Usuário') || erroExistente.textContent.includes('caracteres'))) {
                        erroExistente.remove();
                    }
                    if (valor && valor.length >= 3) {
                        grupo?.classList.add('success');
                        grupo?.classList.remove('error');
                    } else {
                        grupo?.classList.remove('success', 'error');
                    }
                }
            });
        }
    }

    // ===== GERENCIAMENTO DE FOCO =====
    function configurarGerenciamentoFoco() {
        const primeiroCampo = document.getElementById('id_username') ||
            document.getElementById('id_email');
        if (primeiroCampo) {
            primeiroCampo.focus();
        }
    }

    // ===== ATALHOS DE TECLADO =====
    function configurarAtalhosTeclado() {
        document.addEventListener('keydown', function (e) {
            // Pressione 'Esc' para limpar o formulário
            if (e.key === 'Escape') {
                const inputs = document.querySelectorAll('.signup-form input');
                inputs.forEach(input => {
                    if (input.type !== 'submit' && input.type !== 'button') {
                        input.value = '';
                    }
                });
                const primeiroCampo = document.getElementById('id_username') ||
                    document.getElementById('id_email');
                if (primeiroCampo) primeiroCampo.focus();
            }
        });
    }

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const gruposFormulario = document.querySelectorAll('.form-group');
        gruposFormulario.forEach((grupo, indice) => {
            grupo.style.animation = `fadeUp 0.4s ease-out ${0.1 + indice * 0.05}s both`;
        });
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        iniciarAlternadoresSenha();
        configurarValidacaoSenha();
        configurarValidacaoEmail();
        configurarValidacaoUsername();
        configurarEnvioFormulario();
        configurarGerenciamentoFoco();
        configurarAtalhosTeclado();

        console.log('Página de cadastro do MyLedger inicializada');
    });
})();