// frontend/static/js/state-manager.js

/**
 * Gerenciador de Estado Global
 * Controla o estado do sidebar e outros estados compartilhados
 */
class StateManager {
    constructor() {
        this.state = {
            sidebarOpen: false,
            isMobile: false,
            darkMode: localStorage.getItem('darkMode') === 'true',
            searchQuery: '',
            currentPage: window.location.pathname
        };
        
        this.subscribers = [];
        this.init();
    }
    
    init() {
        console.log('🔄 StateManager iniciando...');

        // Verificar se é dispositivo móvel
        this.checkDevice();
        
        // Carregar estado do sidebar do localStorage
        const savedSidebarState = localStorage.getItem('sidebarOpen');
        if (savedSidebarState !== null) {
            this.state.sidebarOpen = savedSidebarState === 'true';
            console.log('📂 Estado carregado do localStorage:', this.state.sidebarOpen);
        } else {
            // Estado padrão: fechado em mobile, aberto em desktop
            this.state.sidebarOpen = !this.state.isMobile;
            this.saveSidebarState();
            console.log('⚙️  Estado padrão:', this.state.sidebarOpen, '(mobile:', this.state.isMobile, ')');
        }

        // Configurar botão toggle
        this.setupToggleButton();
        
        // Ouvir redimensionamento da janela
        window.addEventListener('resize', () => {
            const wasMobile = this.state.isMobile;
            this.checkDevice();
            
            // Se mudou de mobile para desktop e sidebar estava fechada, abrir
            if (wasMobile && !this.state.isMobile && !this.state.sidebarOpen) {
                console.log('📱→💻 Mudou para desktop, abrindo sidebar');
                this.openSidebar();
            }
            // Se mudou de desktop para mobile, fechar sidebar
            else if (!wasMobile && this.state.isMobile && this.state.sidebarOpen) {
                console.log('💻→📱 Mudou para mobile, fechando sidebar');
                this.closeSidebar();
            }
        });
        
        // Fechar sidebar ao clicar fora (mobile)
        document.addEventListener('click', (event) => {
            if (this.state.isMobile && this.state.sidebarOpen) {
                const sidebar = document.querySelector('.sidebar');
                const toggleBtn = document.getElementById('sidebar-toggle-btn');
                
                if (sidebar && toggleBtn) {
                    const isClickInsideSidebar = sidebar.contains(event.target);
                    const isClickOnToggleBtn = toggleBtn.contains(event.target);
                    
                    if (!isClickInsideSidebar && !isClickOnToggleBtn) {
                        console.log('👆 Clicou fora, fechando sidebar');
                        this.closeSidebar();
                    }
                }
            }
        });
        
        // Fechar com tecla ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.state.isMobile && this.state.sidebarOpen) {
                console.log('ESC pressionado, fechando sidebar');
                this.closeSidebar();
            }
        });
        
        // Atualizar estado inicial da UI
        this.updateUI();
        
        console.log('✅ StateManager inicializado. Sidebar aberta:', this.state.sidebarOpen);
    }
    
    setupToggleButton() {
        const toggleBtn = document.getElementById('sidebar-toggle-btn');
        if (toggleBtn) {
            // Remover event listeners anteriores
            const newToggleBtn = toggleBtn.cloneNode(true);
            toggleBtn.parentNode.replaceChild(newToggleBtn, toggleBtn);
            
            // Adicionar novo event listener
            newToggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSidebar();
            });
            
            console.log('✅ Botão toggle configurado');
        }
    }
    
    checkDevice() {
        const wasMobile = this.state.isMobile;
        this.state.isMobile = window.innerWidth <= 768;
        
        if (wasMobile !== this.state.isMobile) {
            console.log('📱 Dispositivo:', this.state.isMobile ? 'Mobile' : 'Desktop');
            this.notifySubscribers('deviceChange');
        }
    }
    
    toggleSidebar() {
        console.log('🔄 Alternando sidebar. Estado atual:', this.state.sidebarOpen);
        this.state.sidebarOpen = !this.state.sidebarOpen;
        this.saveSidebarState();
        this.notifySubscribers('sidebarToggle');
        this.updateUI();
        
        // Acessibilidade: foco no primeiro link quando abre
        if (this.state.sidebarOpen) {
            setTimeout(() => {
                const firstLink = document.querySelector('.sidebar .nav-list a');
                if (firstLink) firstLink.focus();
            }, 100);
        }
    }
    
    openSidebar() {
        if (!this.state.sidebarOpen) {
            console.log('👉 Abrindo sidebar');
            this.state.sidebarOpen = true;
            this.saveSidebarState();
            this.notifySubscribers('sidebarOpen');
            this.updateUI();
        }
    }
    
    closeSidebar() {
        if (this.state.sidebarOpen) {
            console.log('👈 Fechando sidebar');
            this.state.sidebarOpen = false;
            this.saveSidebarState();
            this.notifySubscribers('sidebarClose');
            this.updateUI();
            
            // Acessibilidade: retornar foco ao botão toggle
            const toggleBtn = document.getElementById('sidebar-toggle-btn');
            if (toggleBtn) toggleBtn.focus();
        }
    }
    
    saveSidebarState() {
        localStorage.setItem('sidebarOpen', this.state.sidebarOpen.toString());
        console.log('💾 Estado salvo:', this.state.sidebarOpen);
    }
    
    updateUI() {
        const sidebar = document.querySelector('.sidebar');
        const toggleBtn = document.getElementById('sidebar-toggle-btn');
        
        if (sidebar) {
            if (this.state.sidebarOpen) {
                sidebar.classList.add('open');
                sidebar.setAttribute('aria-expanded', 'true');
                console.log('✅ Sidebar: classe "open" adicionada');
            } else {
                sidebar.classList.remove('open');
                sidebar.setAttribute('aria-expanded', 'false');
                console.log('✅ Sidebar: classe "open" removida');
            }
        } else {
            console.error('❌ Elemento .sidebar não encontrado!');
        }
        
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            if (icon) {
                if (this.state.sidebarOpen) {
                    icon.classList.replace('bx-menu', 'bx-menu-alt-right');
                    toggleBtn.setAttribute('aria-label', 'Fechar menu de navegação');
                    console.log('✅ Ícone alterado para: bx-menu-alt-right');
                } else {
                    icon.classList.replace('bx-menu-alt-right', 'bx-menu');
                    toggleBtn.setAttribute('aria-label', 'Abrir menu de navegação');
                    console.log('✅ Ícone alterado para: bx-menu');
                }
            } else {
                console.error('❌ Ícone não encontrado no botão toggle!');
            }
            
            // Acessibilidade
            toggleBtn.setAttribute('aria-expanded', this.state.sidebarOpen.toString());
        }
        
        // Em mobile, criar/remover overlay
        if (this.state.isMobile) {
            const existingOverlay = document.querySelector('.sidebar-overlay');
            
            if (this.state.sidebarOpen && !existingOverlay) {
                console.log('📱 Criando overlay para mobile');
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                overlay.setAttribute('aria-hidden', 'true');
                overlay.setAttribute('role', 'presentation');
                overlay.style.cssText = `
                    position: fixed;
                    top: var(--header-height, 60px);
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 998;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s ease, visibility 0.3s ease;
                `;
                
                overlay.addEventListener('click', () => {
                    console.log('👆 Overlay clicado, fechando sidebar');
                    this.closeSidebar();
                });
                
                const mainLayout = document.querySelector('.main-layout');
                if (mainLayout) {
                    mainLayout.appendChild(overlay);
                    
                    // Animar overlay
                    setTimeout(() => {
                        overlay.style.opacity = '1';
                        overlay.style.visibility = 'visible';
                    }, 10);
                }
            } else if (!this.state.sidebarOpen && existingOverlay) {
                console.log('📱 Removendo overlay');
                existingOverlay.style.opacity = '0';
                existingOverlay.style.visibility = 'hidden';
                
                setTimeout(() => {
                    if (existingOverlay.parentNode) {
                        existingOverlay.parentNode.removeChild(existingOverlay);
                    }
                }, 300);
            }
        }
    }
    
    subscribe(callback) {
        this.subscribers.push(callback);
        // Notificar imediatamente com estado atual
        callback('init', this.state);
    }
    
    notifySubscribers(event) {
        this.subscribers.forEach(callback => {
            try {
                callback(event, this.state);
            } catch (error) {
                console.error('Erro no subscriber:', error);
            }
        });
    }
    
    // Métodos para outros estados globais
    toggleDarkMode() {
        this.state.darkMode = !this.state.darkMode;
        localStorage.setItem('darkMode', this.state.darkMode.toString());
        this.notifySubscribers('darkModeToggle');
        
        // Aplicar classe dark-mode ao body
        if (this.state.darkMode) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }
    
    setSearchQuery(query) {
        this.state.searchQuery = query;
        this.notifySubscribers('searchChange');
    }
    
    setCurrentPage(page) {
        this.state.currentPage = page;
        this.notifySubscribers('pageChange');
        
        // Em mobile, fechar sidebar ao mudar de página
        if (this.state.isMobile && this.state.sidebarOpen) {
            setTimeout(() => this.closeSidebar(), 300);
        }
    }
    
    trackNavigation() {
        // Observar mudanças de URL via History API
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;
        
        history.pushState = function(...args) {
            originalPushState.apply(this, args);
            window.dispatchEvent(new Event('locationchange'));
        };
        
        history.replaceState = function(...args) {
            originalReplaceState.apply(this, args);
            window.dispatchEvent(new Event('locationchange'));
        };
        
        window.addEventListener('popstate', () => {
            window.dispatchEvent(new Event('locationchange'));
        });
        
        window.addEventListener('locationchange', () => {
            this.setCurrentPage(window.location.pathname);
        });
    }
    
    // Verificar estado persistente
    isSidebarOpen() {
        return this.state.sidebarOpen;
    }
    
    isMobile() {
        return this.state.isMobile;
    }
    
    getCurrentPage() {
        return this.state.currentPage;
    }
    
    getSearchQuery() {
        return this.state.searchQuery;
    }
    
    // Utilitário para resetar estado
    reset() {
        this.state.sidebarOpen = !this.state.isMobile;
        this.saveSidebarState();
        this.updateUI();
        this.notifySubscribers('reset');
    }
}

// Verificar se já existe uma instância
if (!window.AppState) {
    window.AppState = new StateManager();
    
    // API pública para compatibilidade
    window.SidebarManager = {
        toggle: () => window.AppState.toggleSidebar(),
        open: () => window.AppState.openSidebar(),
        close: () => window.AppState.closeSidebar(),
        isOpen: () => window.AppState.isSidebarOpen(),
        isMobile: () => window.AppState.isMobile()
    };
    
    console.log('✅ StateManager pronto para uso');
} else {
    console.log('✅ StateManager já foi inicializado');
}