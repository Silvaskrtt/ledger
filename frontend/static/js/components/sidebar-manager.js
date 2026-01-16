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
        
        // Update visibility
        if (sidebarState.isOpen) {
            this.sidebar.classList.add('show-sidebar');
            this.sidebar.setAttribute('aria-hidden', 'false');
        } else {
            this.sidebar.classList.remove('show-sidebar');
            this.sidebar.setAttribute('aria-hidden', 'true');
        }
        
        // Update reduced state
        if (sidebarState.isReduced) {
            this.sidebar.classList.add('reduced');
        } else {
            this.sidebar.classList.remove('reduced');
        }
        
        // Update toggle button
        this.updateToggleButton(sidebarState);
        
        // Update mobile overlay
        this.updateMobileOverlay(sidebarState);
    }
    
    updateToggleButton(sidebarState) {
        if (!this.toggleBtn) return;
        
        const icon = this.toggleBtn.querySelector('i');
        if (icon) {
            if (sidebarState.isOpen) {
                icon.classList.replace('ri-menu-line', 'ri-close-line');
                this.toggleBtn.setAttribute('aria-label', 'Fechar menu de navegação');
            } else {
                icon.classList.replace('ri-close-line', 'ri-menu-line');
                this.toggleBtn.setAttribute('aria-label', 'Abrir menu de navegação');
            }
        }
        
        this.toggleBtn.setAttribute('aria-expanded', sidebarState.isOpen.toString());
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