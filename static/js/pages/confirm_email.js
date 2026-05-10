// MyLedger - JavaScript de Confirmação de E-mail
// Funcionalidades da tela de confirmação de e-mail

(function () {
    'use strict';

    // ===== EXIBIR ESTADO DE CARREGAMENTO NO ENVIO DO FORMULÁRIO =====
    function configurarEnvioFormulario() {
        const formulario = document.querySelector('.confirm-form');
        if (!formulario) return;

        formulario.addEventListener('submit', function (e) {
            const botao = this.querySelector('.btn-confirm');
            if (!botao) return;

            // Prevenir múltiplos envios
            if (botao.classList.contains('loading')) {
                e.preventDefault();
                return;
            }

            botao.classList.add('loading');
            const conteudoOriginal = botao.innerHTML;
            botao.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Confirmando...';

            // Timeout de segurança (restaurar após 10s se algo der errado)
            setTimeout(() => {
                if (botao.classList.contains('loading')) {
                    botao.classList.remove('loading');
                    botao.innerHTML = conteudoOriginal;
                }
            }, 10000);
        });
    }

    // ===== ATRASOS DE ANIMAÇÃO =====
    function adicionarAtrasosAnimacao() {
        const elementos = document.querySelectorAll('.content-section, .footer-links');
        elementos.forEach((elemento, indice) => {
            elemento.style.animation = `fadeUp 0.5s ease-out ${0.2 + indice * 0.1}s both`;
        });
    }

    // ===== COPIAR E-MAIL PARA ÁREA DE TRANSFERÊNCIA (se houver e-mail exibido) =====
    function configurarCopiaEmail() {
        const elementoEmail = document.querySelector('.message strong');
        if (!elementoEmail) return;

        const email = elementoEmail.textContent;
        if (email && email.includes('@')) {
            // Adicionar tooltip ou funcionalidade de cópia
            elementoEmail.style.cursor = 'pointer';
            elementoEmail.title = 'Clique para copiar o e-mail';

            elementoEmail.addEventListener('click', function () {
                navigator.clipboard.writeText(email).then(() => {
                    exibirNotificacao('E-mail copiado para a área de transferência!', 'success');
                }).catch(() => {
                    exibirNotificacao('Falha ao copiar e-mail', 'error');
                });
            });
        }
    }

    // ===== NOTIFICAÇÃO TOAST =====
    function exibirNotificacao(mensagem, tipo = 'success') {
        // Remover toast existente
        const toastExistente = document.querySelector('.custom-toast');
        if (toastExistente) toastExistente.remove();

        const toast = document.createElement('div');
        toast.className = `custom-toast toast-${tipo}`;
        toast.innerHTML = `
            <i class="fas ${tipo === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${mensagem}</span>
        `;

        // Estilos do toast
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.zIndex = '10000';
        toast.style.padding = '12px 24px';
        toast.style.borderRadius = '12px';
        toast.style.fontSize = '14px';
        toast.style.fontWeight = '500';
        toast.style.display = 'flex';
        toast.style.alignItems = 'center';
        toast.style.gap = '10px';
        toast.style.animation = 'fadeUp 0.3s ease-out';

        if (tipo === 'success') {
            toast.style.background = 'rgba(16, 185, 129, 0.95)';
            toast.style.backdropFilter = 'blur(10px)';
            toast.style.border = '1px solid rgba(16, 185, 129, 0.3)';
            toast.style.color = '#fff';
        } else {
            toast.style.background = 'rgba(239, 68, 68, 0.95)';
            toast.style.backdropFilter = 'blur(10px)';
            toast.style.border = '1px solid rgba(239, 68, 68, 0.3)';
            toast.style.color = '#fff';
        }

        document.body.appendChild(toast);

        // Remover após 3 segundos
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ===== REDIRECIONAR COM CARREGAMENTO =====
    function configurarBotoesRedirecionamento() {
        const botoes = document.querySelectorAll('.btn-primary, .btn-secondary');

        botoes.forEach(botao => {
            botao.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href && href !== '#') {
                    e.preventDefault();

                    // Adicionar estado de carregamento
                    const conteudoOriginal = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Redirecionando...';
                    this.style.opacity = '0.7';
                    this.style.cursor = 'wait';

                    setTimeout(() => {
                        window.location.href = href;
                    }, 500);
                }
            });
        });
    }

    // ===== VERIFICAR EXPIRAÇÃO DO LINK =====
    function verificarExpiracaoLink() {
        const iconeErro = document.querySelector('.icon-circle.error');
        const iconeAviso = document.querySelector('.icon-circle.warning');

        if (iconeErro || iconeAviso) {
            // Se o link expirou, mostrar mensagem adicional após alguns segundos
            setTimeout(() => {
                const textoAjuda = document.createElement('p');
                textoAjuda.className = 'help-text';
                textoAjuda.style.fontSize = '11px';
                textoAjuda.style.color = 'rgba(255, 255, 255, 0.35)';
                textoAjuda.style.marginTop = '16px';
                textoAjuda.style.textAlign = 'center';
                textoAjuda.innerHTML = '<i class="fas fa-envelope"></i> Verifique sua pasta de spam se não recebeu o e-mail';

                const secaoConteudo = document.querySelector('.content-section');
                if (secaoConteudo && !secaoConteudo.querySelector('.help-text')) {
                    secaoConteudo.appendChild(textoAjuda);
                }
            }, 1000);
        }
    }

    // ===== EFEITO DE PARTÍCULAS PARA O GRADIENTE =====
    function criarParticulas() {
        const fundoGradiente = document.querySelector('.gradient-background');
        if (!fundoGradiente) return;

        // Criar partículas sutis
        for (let i = 0; i < 30; i++) {
            const particula = document.createElement('div');
            particula.className = 'gradient-particle';
            particula.style.position = 'absolute';
            particula.style.width = '2px';
            particula.style.height = '2px';
            particula.style.background = 'rgba(138, 79, 255, 0.3)';
            particula.style.borderRadius = '50%';
            particula.style.left = Math.random() * 100 + '%';
            particula.style.top = Math.random() * 100 + '%';
            particula.style.animation = `flutuarParticula ${5 + Math.random() * 10}s linear infinite`;
            particula.style.animationDelay = Math.random() * 5 + 's';

            fundoGradiente.appendChild(particula);
        }
    }

    // Animação de partículas
    const estilo = document.createElement('style');
    estilo.textContent = `
        @keyframes flutuarParticula {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 0.5;
            }
            90% {
                opacity: 0.5;
            }
            100% {
                transform: translateY(-100vh) rotate(360deg);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(estilo);

    // ===== GERENCIAMENTO DE FOCO =====
    function configurarGerenciamentoFoco() {
        const botaoConfirmar = document.querySelector('.btn-confirm, .btn-primary');
        if (botaoConfirmar) {
            // Dar foco ao botão principal para acessibilidade
            botaoConfirmar.focus();
        }
    }

    // ===== ATALHOS DE TECLADO =====
    function configurarAtalhosTeclado() {
        document.addEventListener('keydown', function (e) {
            // Pressione 'Enter' no formulário de confirmação
            if (e.key === 'Enter') {
                const formulario = document.querySelector('.confirm-form');
                const botaoEnviar = document.querySelector('.btn-confirm');
                if (formulario && botaoEnviar && document.activeElement !== botaoEnviar) {
                    e.preventDefault();
                    botaoEnviar.click();
                }
            }

            // Pressione 'Escape' para voltar ao login
            if (e.key === 'Escape') {
                const linkLogin = document.querySelector('a[href*="account_login"]');
                if (linkLogin) {
                    window.location.href = linkLogin.getAttribute('href');
                }
            }
        });
    }

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function () {
        adicionarAtrasosAnimacao();
        configurarEnvioFormulario();
        configurarCopiaEmail();
        configurarBotoesRedirecionamento();
        verificarExpiracaoLink();
        criarParticulas();
        configurarGerenciamentoFoco();
        configurarAtalhosTeclado();

        console.log('Página de confirmação de e-mail do MyLedger inicializada');
    });
})();