/**
 * Theme Manager para template Bedimcode
 */
class ThemeManager {
    constructor() {
        this.themeButton = document.getElementById('theme-button');
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupAccessibility();
        
        // Subscribe to theme changes
        window.AppState.subscribe('theme:toggle', (theme) => {
            this.updateThemeButton(theme);
        });
        
        // Set initial state
        this.updateThemeButton(window.AppState.getTheme());
    }
    
    updateThemeButton(theme) {
        if (!this.themeButton) return;
        
        const icon = this.themeButton.querySelector('i');
        if (icon) {
            if (theme === 'dark') {
                icon.classList.remove('ri-sun-fill');
                icon.classList.add('ri-moon-clear-fill');
                this.themeButton.setAttribute('aria-label', 'Alternar para tema claro');
            } else {
                icon.classList.remove('ri-moon-clear-fill');
                icon.classList.add('ri-sun-fill');
                this.themeButton.setAttribute('aria-label', 'Alternar para tema escuro');
            }
        }
    }
    
    setupEventListeners() {
        if (this.themeButton) {
            this.themeButton.addEventListener('click', (e) => {
                e.preventDefault();
                window.AppState.toggleTheme();
            });
        }
    }
    
    setupAccessibility() {
        if (this.themeButton) {
            this.themeButton.setAttribute('role', 'button');
            this.themeButton.setAttribute('tabindex', '0');
            
            this.themeButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    window.AppState.toggleTheme();
                }
            });
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('theme-button')) {
        new ThemeManager();
        console.log('✅ Theme Manager inicializado');
    }
});