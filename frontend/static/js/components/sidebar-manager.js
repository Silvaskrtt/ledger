/**
 * Sidebar Manager para template Bedimcode
 * Responsabilidade única: gerenciar UI da sidebar
 */
class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.toggleBtn = document.getElementById('header-toggle');
        this.links = document.querySelectorAll('.sidebar__link');

        console.log('🔍 SidebarManager encontrou:', {
            sidebar: !!this.sidebar,
            toggleBtn: !!this.toggleBtn,
            AppState: !!window.AppState
        });
        
        this.init();
    }
    
    init() {
        console.log('🔄 SidebarManager.init() chamado');

        if (!window.AppState) {
            console.error('❌ AppState não disponível!');
            this.setupFallback();
            return;
        }

        // VERIFICAÇÃO: O subscribe está funcionando?
        console.log('📡 Inscrito no AppState...');

        // Estado inicial
        const initialState = window.AppState.getSidebarState();
        console.log('📂 Estado inicial:', initialState);

        this.setupEventListeners();
        this.setupAccessibility();
        
        // Subscribe to state changes
        window.AppState.subscribe('sidebar:*', (sidebarState) => {
            console.log('📨 Evento recebido do AppState:', sidebarState);
            this.updateUI(sidebarState);
        });
        
        // Set initial state
        this.updateUI(initialState);
    }
    
    updateUI(sidebarState) {
        if (!this.sidebar) return;
        
        console.log('🎨 Atualizando UI do sidebar:', sidebarState);
        
        // **LÓGICA CORRIGIDA:**
        
        // 1. Em MOBILE: show/hide normal
        if (sidebarState.isMobile) {
            if (sidebarState.isOpen) {
                this.sidebar.classList.add('show-sidebar');
                this.sidebar.classList.remove('reduced', 'hidden');
                console.log('📱 Mobile: sidebar aberta');
            } else {
                this.sidebar.classList.remove('show-sidebar', 'reduced');
                this.sidebar.classList.add('hidden');
                console.log('📱 Mobile: sidebar fechada');
            }
        }
        // 2. Em DESKTOP: sempre visível, alternar entre expandido/reduzido
        else {
            // SEMPRE visível em desktop
            this.sidebar.classList.add('show-sidebar');
            this.sidebar.classList.remove('hidden');
            
            if (sidebarState.isReduced) {
                this.sidebar.classList.add('reduced');
                console.log('💻 Desktop: sidebar REDUZIDA (somente ícones)');
            } else {
                this.sidebar.classList.remove('reduced');
                console.log('💻 Desktop: sidebar EXPANDIDA (textos + ícones)');
            }
        }
        
        // Update toggle button
        this.updateToggleButton(sidebarState);
        
        // Update mobile overlay
        if (sidebarState.isMobile) {
            this.updateMobileOverlay(sidebarState);
        }
    }
    
    updateToggleButton(sidebarState) {
        if (!this.toggleBtn) return;
        
        const icon = this.toggleBtn.querySelector('i');
        if (icon) {
            // Diferentes comportamentos para mobile vs desktop
            if (sidebarState.isMobile) {
                // Mobile: alternar entre menu e X
                if (sidebarState.isOpen) {
                    icon.className = 'ri-close-line';
                    this.toggleBtn.setAttribute('aria-label', 'Fechar menu');
                } else {
                    icon.className = 'ri-menu-line';
                    this.toggleBtn.setAttribute('aria-label', 'Abrir menu');
                }
            } else {
                // Desktop: alternar entre setas (expandir/reduzir)
                if (sidebarState.isReduced) {
                    icon.className = 'ri-arrow-right-line';
                    this.toggleBtn.setAttribute('aria-label', 'Expandir menu');
                } else {
                    icon.className = 'ri-arrow-left-line';
                    this.toggleBtn.setAttribute('aria-label', 'Reduzir menu');
                }
            }
        }
        
        // Acessibilidade: em desktop sempre "expanded" pois nunca fecha
        this.toggleBtn.setAttribute('aria-expanded', 
            sidebarState.isMobile ? sidebarState.isOpen.toString() : 'true');
    }
    
    updateMobileOverlay(sidebarState) {
        if (!sidebarState.isMobile) return;
        
        const existingOverlay = document.querySelector('.sidebar-overlay');
        
        if (sidebarState.isOpen && !existingOverlay) {
            const overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.setAttribute('role', 'presentation');
            overlay.setAttribute('aria-hidden', 'true');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                z-index: calc(var(--z-fixed) - 1);
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s ease, visibility 0.3s ease;
            `;
            
            overlay.addEventListener('click', () => {
                window.AppState.closeSidebar();
            });
            
            document.body.appendChild(overlay);
            
            // Animate in
            setTimeout(() => {
                overlay.style.opacity = '1';
                overlay.style.visibility = 'visible';
            }, 10);
            
        } else if (!sidebarState.isOpen && existingOverlay) {
            existingOverlay.style.opacity = '0';
            existingOverlay.style.visibility = 'hidden';
            
            setTimeout(() => {
                if (existingOverlay.parentNode) {
                    existingOverlay.parentNode.removeChild(existingOverlay);
                }
            }, 300);
        }
    }
    
    setupEventListeners() {
        // Toggle button
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.AppState.toggleSidebar();
            });
        }
        
        // Link clicks
        this.links.forEach(link => {
            link.addEventListener('click', () => {
                this.setActiveLink(link);
                window.AppState.setCurrentPage(link.getAttribute('href'));
            });
        });
        
        // Close on outside click (mobile)
        document.addEventListener('click', (e) => {
            const sidebarState = window.AppState.getSidebarState();
            if (sidebarState.isMobile && sidebarState.isOpen) {
                const isClickInsideSidebar = this.sidebar?.contains(e.target);
                const isClickOnToggle = this.toggleBtn?.contains(e.target);
                
                if (!isClickInsideSidebar && !isClickOnToggle) {
                    window.AppState.closeSidebar();
                }
            }
        });
    }
    
    setActiveLink(activeLink) {
        this.links.forEach(link => {
            link.classList.remove('active-link');
        });
        activeLink.classList.add('active-link');
    }
    
    setupAccessibility() {
        if (this.sidebar) {
            this.sidebar.setAttribute('role', 'navigation');
            this.sidebar.setAttribute('aria-label', 'Menu principal');
        }
        
        // Keyboard navigation
        this.sidebar?.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                window.AppState.closeSidebar();
                this.toggleBtn?.focus();
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('sidebar')) {
        new SidebarManager();
        console.log('✅ Sidebar Manager inicializado');
    }
});