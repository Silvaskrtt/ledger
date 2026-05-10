// MyLedger - JavaScript de Verificação de E-mail
// Funcionalidades da tela de verificação de e-mail

(function () {
    'use strict';

    // ===== Elementos do DOM =====
    const btnReenviar = document.getElementById('resendEmailBtn');
    const modalReenviar = document.getElementById('resendModal');
    const btnContatarSuporte = document.getElementById('contactSupportBtn');
    const inputEmailReenvio = document.getElementById('resendEmailInput');
    const erroModal = document.getElementById('modalError');
    const toastSucesso = document.getElementById('successToast');
    const toastErro = document.getElementById('errorToast');

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const elementos = document.querySelectorAll('.tips-section, .action-buttons, .help-text');
        elementos.forEach((elemento, indice) => {
            elemento.style.animation = `fadeUp 0.5s ease-out ${0.2 + indice * 0.1}s both`;
        });
    }

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

    // ===== MODAL DE REENVIO DE E-MAIL =====
    window.abrirModalReenvio = function () {
        if (modalReenviar) {
            modalReenviar.style.display = 'flex';
            if (inputEmailReenvio) {
                inputEmailReenvio.value = '';
                inputEmailReenvio.focus();
            }
            if (erroModal) erroModal.style.display = 'none';
        }
    };

    window.fecharModalReenvio = function () {
        if (modalReenviar) {
            modalReenviar.style.display = 'none';
        }
    };

    // ===== ENVIAR SOLICITAÇÃO DE REENVIO =====
    window.enviarReenvioEmail = async function () {
        const email = inputEmailReenvio?.value.trim();

        if (!email) {
            if (erroModal) {
                erroModal.textContent = 'Digite seu endereço de e-mail';
                erroModal.style.display = 'block';
            }
            return;
        }

        if (!isEmailValido(email)) {
            if (erroModal) {
                erroModal.textContent = 'Digite um endereço de e-mail válido';
                erroModal.style.display = 'block';
            }
            return;
        }

        // Desabilitar botão e mostrar carregamento
        const btnConfirmar = document.querySelector('.btn-modal-confirm');
        const conteudoOriginal = btnConfirmar?.innerHTML;
        if (btnConfirmar) {
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        }

        try {
            // Simular chamada de API - Substitua pelo endpoint real
            await simularChamadaApi('/api/resend-verification/', { email: email });

            fecharModalReenvio();
            exibirNotificacao('success', 'E-mail de verificação enviado com sucesso! Verifique sua caixa de entrada.');

            // Resetar estado do botão
            if (btnConfirmar) {
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = conteudoOriginal;
            }
        } catch (erro) {
            if (erroModal) {
                erroModal.textContent = erro.message || 'Falha ao enviar e-mail. Tente novamente.';
                erroModal.style.display = 'block';
            }

            if (btnConfirmar) {
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = conteudoOriginal;
            }
        }
    };

    // ===== VALIDAR E-MAIL =====
    function isEmailValido(email) {
        const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regexEmail.test(email);
    }

    // ===== SIMULAR CHAMADA DE API =====
    function simularChamadaApi(url, dados) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                // Simular resposta bem-sucedida
                if (dados.email && dados.email.length > 0) {
                    resolve({ success: true });
                } else {
                    reject(new Error('Endereço de e-mail inválido'));
                }
            }, 1500);
        });
    }

    // ===== CHAMADA REAL DE API (para implementação real) =====
    async function enviarEmailVerificacao(email) {
        const tokenCsrf = obterTokenCsrf();

        const resposta = await fetch('/api/auth/resend-verification/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': tokenCsrf
            },
            body: JSON.stringify({ email: email })
        });

        if (!resposta.ok) {
            const erro = await resposta.json();
            throw new Error(erro.message || 'Falha ao enviar e-mail');
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

    // ===== CLIQUE NO BOTÃO REENVIAR =====
    if (btnReenviar) {
        btnReenviar.addEventListener('click', abrirModalReenvio);
    }

    // ===== CONTATAR SUPORTE =====
    if (btnContatarSuporte) {
        btnContatarSuporte.addEventListener('click', function (e) {
            e.preventDefault();
            // Implementar contato com suporte - pode abrir cliente de e-mail ou formulário
            window.location.href = 'mailto:suporte@myledger.com?subject=Ajuda%20na%20Verifica%C3%A7%C3%A3o%20de%20E-mail';
            exibirNotificacao('success', 'Abrindo cliente de e-mail...');
        });
    }

    // ===== CLICAR FORA DO MODAL PARA FECHAR =====
    if (modalReenviar) {
        modalReenviar.addEventListener('click', function (e) {
            if (e.target === modalReenviar) {
                fecharModalReenvio();
            }
        });
    }

    // ===== PRESSIONAR ESC PARA FECHAR O MODAL =====
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modalReenviar && modalReenviar.style.display === 'flex') {
            fecharModalReenvio();
        }
    });

    // ===== TEMPORIZADOR PARA BOTÃO REENVIAR =====
    let contagemRegressiva = 0;
    let intervalo = null;

    function iniciarEsperaReenvio(segundos = 30) {
        if (!btnReenviar) return;

        contagemRegressiva = segundos;
        btnReenviar.disabled = true;
        const textoOriginal = btnReenviar.innerHTML;

        intervalo = setInterval(() => {
            if (contagemRegressiva <= 0) {
                clearInterval(intervalo);
                btnReenviar.disabled = false;
                btnReenviar.innerHTML = textoOriginal;
            } else {
                btnReenviar.innerHTML = `<i class="fas fa-clock"></i> Aguarde ${contagemRegressiva}s`;
                contagemRegressiva--;
            }
        }, 1000);
    }

    // Iniciar espera automaticamente ao carregar a página (opcional)
    // iniciarEsperaReenvio(30);

    // ===== VERIFICAR PARÂMETROS DA URL =====
    function verificarParametrosUrl() {
        const parametrosUrl = new URLSearchParams(window.location.search);
        const email = parametrosUrl.get('email');

        if (email && inputEmailReenvio) {
            inputEmailReenvio.value = email;
        }

        const reenviado = parametrosUrl.get('resent');
        if (reenviado === 'true') {
            exibirNotificacao('success', 'E-mail de verificação foi reenviado!');
        }
    }

    // ===== REENVIO AUTOMÁTICO AO CARREGAR PÁGINA (se houver parâmetro) =====
    function reenviarAutomaticamenteSeNecessario() {
        const parametrosUrl = new URLSearchParams(window.location.search);
        if (parametrosUrl.get('auto_resend') === 'true') {
            setTimeout(() => {
                abrirModalReenvio();
            }, 1000);
        }
    }

    // ===== COPIAR E-MAIL PARA ÁREA DE TRANSFERÊNCIA =====
    function configurarCopiaEmail() {
        // Se houver elemento mostrando o e-mail, permitir cópia
        const elementoEmail = document.querySelector('.message strong');
        if (elementoEmail && elementoEmail.textContent.includes('@')) {
            elementoEmail.style.cursor = 'pointer';
            elementoEmail.title = 'Clique para copiar o e-mail';
            elementoEmail.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(elementoEmail.textContent);
                    exibirNotificacao('success', 'E-mail copiado para a área de transferência!');
                } catch (err) {
                    exibirNotificacao('error', 'Falha ao copiar e-mail');
                }
            });
        }
    }

    // ===== GERENCIAMENTO DE FOCO =====
    function configurarGerenciamentoFoco() {
        // Dar foco ao botão principal após carregar
        if (btnReenviar) {
            setTimeout(() => {
                btnReenviar.focus();
            }, 100);
        }
    }

    // ===== MONITORAR STATUS DE VERIFICAÇÃO =====
    function verificarStatusVerificacao() {
        // Opcional: Polling para verificar se o e-mail já foi verificado
        let tentativas = 0;
        const maxTentativas = 30; // 30 segundos

        const intervalo = setInterval(() => {
            tentativas++;
            if (tentativas >= maxTentativas) {
                clearInterval(intervalo);
            }

            // Aqui você poderia fazer uma chamada API para verificar o status
            // Se verificado, redirecionar para o login
        }, 1000);
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        verificarParametrosUrl();
        reenviarAutomaticamenteSeNecessario();
        configurarCopiaEmail();
        configurarGerenciamentoFoco();
        // verificarStatusVerificacao(); // Descomente se quiser polling

        // Registrar inicialização
        console.log('Página de verificação de e-mail do MyLedger inicializada');
    });
})();