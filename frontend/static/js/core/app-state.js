/**
 * Gerenciador Central de Estado da Aplicação
 * Fonte única da verdade para o estado global
 */
class AppState {
    constructor() {
        this.state = {
            sidebar: {
                isOpen: localStorage.getItem('sidebarOpen') === 'true' || false,
                isReduced: localStorage.getItem('sidebarReduced') === 'true' || false,
                isMobile: window.innerWidth <= 768
            },
            theme: localStorage.getItem('theme') || 'dark',
            currentPage: window.location.pathname,
            user: null
        };
        
        this.observers = [];
        this.init();
    }
    
    init() {
        this.setupResponsive();
        this.applyTheme();
        this.setupGlobalListeners();
    }
    
    /* ========= SIDEBAR METHODS ========= */
    toggleSidebar() {
        this.state.sidebar.isOpen = !this.state.sidebar.isOpen;
        this.persistState('sidebar');
        this.notify('sidebar:toggle', this.state.sidebar);
    }
    
    openSidebar() {
        if (!this.state.sidebar.isOpen) {
            this.state.sidebar.isOpen = true;
            this.persistState('sidebar');
            this.notify('sidebar:open', this.state.sidebar);
        }
    }
    
    closeSidebar() {
        if (this.state.sidebar.isOpen) {
            this.state.sidebar.isOpen = false;
            this.persistState('sidebar');
            this.notify('sidebar:close', this.state.sidebar);
        }
    }
    
    toggleSidebarReduced() {
        this.state.sidebar.isReduced = !this.state.sidebar.isReduced;
        localStorage.setItem('sidebarReduced', this.state.sidebar.isReduced);
        this.notify('sidebar:reduced', this.state.sidebar);
    }
    
    /* ========= THEME METHODS ========= */
    toggleTheme() {
        this.state.theme = this.state.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.state.theme);
        this.applyTheme();
        this.notify('theme:toggle', this.state.theme);
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.state.theme);
    }
    
    /* ========= PAGE NAVIGATION ========= */
    setCurrentPage(page) {
        this.state.currentPage = page;
        this.notify('page:change', page);
        
        // Auto-close sidebar on mobile
        if (this.state.sidebar.isMobile && this.state.sidebar.isOpen) {
            setTimeout(() => this.closeSidebar(), 300);
        }
    }
    
    /* ========= UTILITY METHODS ========= */
    setupResponsive() {
        const checkMobile = () => {
            const wasMobile = this.state.sidebar.isMobile;
            this.state.sidebar.isMobile = window.innerWidth <= 768;
            
            if (wasMobile !== this.state.sidebar.isMobile) {
                // Auto-adjust sidebar on device change
                if (this.state.sidebar.isMobile) {
                    this.closeSidebar();
                } else {
                    this.openSidebar();
                }
                this.notify('device:change', this.state.sidebar.isMobile);
            }
        };
        
        window.addEventListener('resize', checkMobile);
        checkMobile(); // Initial check
    }
    
    setupGlobalListeners() {
        // Close sidebar on ESC key (mobile only)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.state.sidebar.isMobile && this.state.sidebar.isOpen) {
                this.closeSidebar();
            }
        });
        
        // Track navigation
        this.trackNavigation();
    }
    
    trackNavigation() {
        // Observe URL changes
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
    
    /* ========= OBSERVER PATTERN ========= */
    subscribe(event, callback) {
        console.log(`📝 Novo subscription: ${event}`);
        
        this.observers.push({ event, callback });
        
        // Notificar imediatamente com estado atual se for um evento relacionado
        if (event === 'sidebar:*') {
            console.log(`   → Notificação inicial para sidebar:*`);
            setTimeout(() => {
                try {
                    callback(this.state.sidebar);
                } catch (error) {
                    console.error(`❌ Erro na notificação inicial:`, error);
                }
            }, 0);
        } else if (event === 'theme:*') {
            console.log(`   → Notificação inicial para theme:*`);
            setTimeout(() => {
                try {
                    callback(this.state.theme);
                } catch (error) {
                    console.error(`❌ Erro na notificação inicial:`, error);
                }
            }, 0);
        }
    }
    
    notify(event, data = null) {
        console.log(`🔔 Notificando evento: ${event}`, data || this.state);
        
        this.observers.forEach(observer => {
            if (observer.event === event || observer.event === '*') {
                try {
                    console.log(`   → Enviando para observer:`, observer.event);
                    observer.callback(data || this.state);
                } catch (error) {
                    console.error(`❌ Erro no observer:`, error);
                }
            } else if (observer.event.endsWith(':*')) {
                const baseEvent = observer.event.replace(':*', '');
                if (event.startsWith(baseEvent)) {
                    try {
                        console.log(`   → Enviando para observer pattern:`, observer.event);
                        observer.callback(data || this.state);
                    } catch (error) {
                        console.error(`❌ Erro no observer pattern:`, error);
                    }
                }
            }
        });
    }
    
    persistState(key) {
        if (key === 'sidebar') {
            localStorage.setItem('sidebarOpen', this.state.sidebar.isOpen);
        }
    }
    
    /* ========= PUBLIC API ========= */
    getSidebarState() {
        return { ...this.state.sidebar };
    }
    
    getTheme() {
        return this.state.theme;
    }
    
    getCurrentPage() {
        return this.state.currentPage;
    }
}

// Global instance
window.AppState = new AppState();