// MyLedger - JavaScript de Alteração de Senha
// Funcionalidades da tela de alteração de senha

(function () {
    'use strict';

    // ===== Elementos do DOM =====
    const formularioSenha = document.querySelector('.password-form');
    const inputSenhaAtual = document.getElementById('id_oldpassword');
    const inputNovaSenha = document.getElementById('id_password1');
    const inputConfirmarSenha = document.getElementById('id_password2');
    const botaoEnviar = document.querySelector('.btn-change-password');
    const containerForca = document.getElementById('passwordStrengthContainer');
    const barraForca = document.getElementById('strengthFill');
    const textoForca = document.getElementById('strengthText');
    const toastSucesso = document.getElementById('successToast');
    const toastErro = document.getElementById('errorToast');

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

    // ===== VALIDAR FORÇA DA SENHA =====
    function validarForcaSenha(senha) {
        if (!senha || senha.length === 0) {
            if (containerForca) containerForca.style.display = 'none';
            return 0;
        }

        if (containerForca) containerForca.style.display = 'block';

        let forca = 0;
        let mensagem = '';

        // Verificar comprimento
        if (senha.length >= 8) forca++;

        // Letras maiúsculas e minúsculas
        if (senha.match(/[a-z]/) && senha.match(/[A-Z]/)) forca++;

        // Números
        if (senha.match(/[0-9]/)) forca++;

        // Caracteres especiais
        if (senha.match(/[^a-zA-Z0-9]/)) forca++;

        // Definir mensagem com base na força
        switch (forca) {
            case 1:
                mensagem = 'Senha fraca';
                break;
            case 2:
                mensagem = 'Senha razoável';
                break;
            case 3:
                mensagem = 'Senha boa';
                break;
            case 4:
                mensagem = 'Senha forte';
                break;
            default:
                mensagem = 'Senha muito fraca';
        }

        // Atualizar interface
        if (barraForca && textoForca) {
            // Remover classes existentes
            containerForca.classList.remove('strength-0', 'strength-1', 'strength-2', 'strength-3', 'strength-4');
            containerForca.classList.add(`strength-${forca}`);
            barraForca.style.width = `${forca * 25}%`;
            textoForca.textContent = mensagem;
        }

        return forca;
    }

    // ===== VERIFICAR SE AS SENHAS COINCIDEM =====
    function verificarSenhasIguais() {
        if (!inputNovaSenha || !inputConfirmarSenha) return;

        const grupo = inputConfirmarSenha.closest('.form-group');
        if (!grupo) return;

        const erroExistente = grupo.querySelector('.error-message');

        if (inputConfirmarSenha.value && inputNovaSenha.value !== inputConfirmarSenha.value) {
            if (!erroExistente || !erroExistente.textContent.includes('coincidem')) {
                if (erroExistente) erroExistente.remove();
                const erro = document.createElement('span');
                erro.className = 'error-message';
                erro.textContent = 'As senhas não coincidem';
                grupo.appendChild(erro);
            }
            grupo.classList.add('error');
            grupo.classList.remove('success');
            return false;
        } else {
            if (erroExistente && erroExistente.textContent.includes('coincidem')) {
                erroExistente.remove();
            }
            if (inputConfirmarSenha.value && inputNovaSenha.value === inputConfirmarSenha.value) {
                grupo.classList.add('success');
                grupo.classList.remove('error');
            } else {
                grupo.classList.remove('success', 'error');
            }
            return true;
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

    function limparErroCampo(campo) {
        const grupo = campo.closest('.form-group');
        if (grupo) {
            const erro = grupo.querySelector('.error-message');
            if (erro) erro.remove();
            grupo.classList.remove('error');
        }
    }

    // ===== CONFIGURAR VALIDAÇÃO EM TEMPO REAL =====
    function configurarValidacaoTempoReal() {
        if (inputNovaSenha) {
            inputNovaSenha.addEventListener('input', function () {
                validarForcaSenha(this.value);
                verificarSenhasIguais();

                if (this.value.length >= 8) {
                    const grupo = this.closest('.form-group');
                    grupo?.classList.add('success');
                } else {
                    const grupo = this.closest('.form-group');
                    grupo?.classList.remove('success');
                }
            });
        }

        if (inputConfirmarSenha) {
            inputConfirmarSenha.addEventListener('input', verificarSenhasIguais);
        }
    }

    // ===== PROCESSAR ENVIO DO FORMULÁRIO =====
    async function processarEnvio(e) {
        e.preventDefault();

        let temErro = false;

        // Validar senha atual
        if (inputSenhaAtual && !inputSenhaAtual.value) {
            exibirErroCampo(inputSenhaAtual, 'Digite sua senha atual');
            temErro = true;
        }

        // Validar nova senha
        if (inputNovaSenha) {
            if (!inputNovaSenha.value) {
                exibirErroCampo(inputNovaSenha, 'Digite uma nova senha');
                temErro = true;
            } else if (inputNovaSenha.value.length < 6) {
                exibirErroCampo(inputNovaSenha, 'A nova senha deve ter pelo menos 6 caracteres');
                temErro = true;
            }
        }

        // Validar confirmação de senha
        if (inputConfirmarSenha) {
            if (!inputConfirmarSenha.value) {
                exibirErroCampo(inputConfirmarSenha, 'Confirme sua nova senha');
                temErro = true;
            } else if (inputNovaSenha && inputNovaSenha.value !== inputConfirmarSenha.value) {
                exibirErroCampo(inputConfirmarSenha, 'As senhas não coincidem');
                temErro = true;
            }
        }

        if (temErro) return;

        // Exibir estado de carregamento
        if (botaoEnviar) {
            botaoEnviar.classList.add('loading');
            const conteudoOriginal = botaoEnviar.innerHTML;
            botaoEnviar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Alterando senha...';
            botaoEnviar.disabled = true;
            botaoEnviar.setAttribute('data-original', conteudoOriginal);
        }

        try {
            // Simular chamada de API (remover ao integrar com o backend real)
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Enviar o formulário
            e.target.submit();

        } catch (erro) {
            exibirNotificacao('error', erro.message || 'Erro ao alterar senha. Tente novamente.');

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

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const gruposFormulario = document.querySelectorAll('.form-group');
        gruposFormulario.forEach((grupo, indice) => {
            grupo.style.animation = `fadeUp 0.4s ease-out ${0.1 + indice * 0.05}s both`;
        });

        const secaoDicas = document.querySelector('.password-tips');
        if (secaoDicas) {
            secaoDicas.style.animation = `fadeUp 0.4s ease-out 0.35s both`;
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
        if (inputSenhaAtual) {
            setTimeout(() => {
                inputSenhaAtual.focus();
            }, 100);
        }
    }

    // ===== ATALHOS DE TECLADO =====
    function configurarAtalhosTeclado() {
        document.addEventListener('keydown', function (e) {
            // Pressione 'Esc' para limpar o formulário
            if (e.key === 'Escape') {
                if (inputSenhaAtual) inputSenhaAtual.value = '';
                if (inputNovaSenha) inputNovaSenha.value = '';
                if (inputConfirmarSenha) inputConfirmarSenha.value = '';
                if (inputSenhaAtual) inputSenhaAtual.focus();

                if (containerForca) containerForca.style.display = 'none';

                // Feedback visual
                if (botaoEnviar) {
                    botaoEnviar.style.transform = 'scale(0.98)';
                    setTimeout(() => {
                        botaoEnviar.style.transform = '';
                    }, 200);
                }
            }
        });
    }

    // ===== VERIFICAR PARÂMETROS DA URL =====
    function verificarParametrosUrl() {
        const parametrosUrl = new URLSearchParams(window.location.search);
        const sucesso = parametrosUrl.get('success');
        const erro = parametrosUrl.get('error');

        if (sucesso === 'password_changed') {
            exibirNotificacao('success', 'Senha alterada com sucesso!');
        } else if (erro) {
            exibirNotificacao('error', decodeURIComponent(erro));
        }
    }

    // ===== PREVENIR ENVIO DUPLICADO =====
    let estaEnviando = false;

    function prevenirEnvioDuplicado() {
        if (formularioSenha) {
            formularioSenha.addEventListener('submit', function (e) {
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

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        iniciarAlternadoresSenha();
        configurarValidacaoTempoReal();
        adicionarAnimacaoGradiente();
        configurarGerenciamentoFoco();
        configurarAtalhosTeclado();
        verificarParametrosUrl();
        prevenirEnvioDuplicado();

        if (formularioSenha) {
            formularioSenha.addEventListener('submit', processarEnvio);
        }

        console.log('MyLedger - Página de alteração de senha inicializada');
    });
})();