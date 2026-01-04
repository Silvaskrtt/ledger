// frontend/static/js/sidebar.js
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const btn = document.getElementById('btn');
    const mainContent = document.querySelector('.main-content');
    const appContainer = document.querySelector('.app-container');
    
    if (!sidebar || !btn) {
        console.warn('Sidebar elements not found');
        return;
    }
    
    // Função para alternar sidebar
    function toggleSidebar() {
        sidebar.classList.toggle('open');
        updateMenuIcon();
        saveSidebarState();
    }
    
    // Função para atualizar ícone do menu
    function updateMenuIcon() {
        if (sidebar.classList.contains('open')) {
            btn.classList.replace('bx-menu', 'bx-menu-alt-right');
        } else {
            btn.classList.replace('bx-menu-alt-right', 'bx-menu');
        }
    }
    
    // Salvar estado do sidebar no localStorage
    function saveSidebarState() {
        const isOpen = sidebar.classList.contains('open');
        localStorage.setItem('sidebarOpen', isOpen);
    }
    
    // Carregar estado do sidebar do localStorage
    function loadSidebarState() {
        const savedState = localStorage.getItem('sidebarOpen');
        if (savedState !== null) {
            if (savedState === 'true') {
                sidebar.classList.add('open');
            } else {
                sidebar.classList.remove('open');
            }
            updateMenuIcon();
        }
    }
    
    // Gerar cor do avatar baseado no nome
    function generateAvatarColor(username) {
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ];
        
        if (!username) return colors[0];
        
        let hash = 0;
        for (let i = 0; i < username.length; i++) {
            hash = username.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        return colors[Math.abs(hash) % colors.length];
    }
    
    // Aplicar cor do avatar
    function setupAvatarColors() {
        const avatarDefaults = document.querySelectorAll('.avatar-default');
        avatarDefaults.forEach(avatar => {
            const initial = avatar.getAttribute('data-initial') || '?';
            const color = generateAvatarColor(initial);
            avatar.style.background = `linear-gradient(135deg, ${color} 0%, ${color}80 100%)`;
            avatar.textContent = initial;
        });
    }
    
    // Fechar sidebar ao clicar fora (mobile)
    function setupClickOutside() {
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
                const isClickInsideSidebar = sidebar.contains(event.target);
                const isClickOnMenuBtn = btn.contains(event.target);
                
                if (!isClickInsideSidebar && !isClickOnMenuBtn) {
                    sidebar.classList.remove('open');
                    updateMenuIcon();
                    saveSidebarState();
                }
            }
        });
    }
    
    // Configurar busca
    function setupSearch() {
        const searchInput = document.querySelector('.sidebar input');
        const searchIcon = document.querySelector('.sidebar .bx-search');
        
        if (searchInput && searchIcon) {
            searchIcon.addEventListener('click', function() {
                searchInput.focus();
            });
            
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    alert('Funcionalidade de busca em desenvolvimento');
                    this.value = '';
                }
            });
        }
    }
    
    // Inicializar
    function initSidebar() {
        // Evento do botão menu
        btn.addEventListener('click', toggleSidebar);
        
        // Carregar estado salvo
        loadSidebarState();
        
        // Configurar cores do avatar
        setupAvatarColors();
        
        // Configurar clique fora (mobile)
        setupClickOutside();
        
        // Configurar busca
        setupSearch();
        
        // Atualizar ao redimensionar
        window.addEventListener('resize', function() {
            
            if (window.innerWidth > 768) {
                sidebar.style.transform = 'translateX(0)';
            } else {
                if (!sidebar.classList.contains('open')) {
                    sidebar.style.transform = 'translateX(-100%)';
                }
            }
        });
        
        // Inicializar transform para mobile
        if (window.innerWidth <= 768 && !sidebar.classList.contains('open')) {
            sidebar.style.transform = 'translateX(-100%)';
        }
    }
    
    // Inicializar sidebar
    initSidebar();
    
    console.log('Sidebar initialized successfully');
});

// Função para melhorar os tooltips
function setupTooltips() {
    const sidebar = document.querySelector('.sidebar');
    const tooltips = document.querySelectorAll('.sidebar li .tooltip');
    
    // Garantir que tooltips tenham o texto correto
    tooltips.forEach(tooltip => {
        const link = tooltip.parentElement.querySelector('a');
        if (link) {
            const linkName = link.querySelector('.links_name');
            if (linkName && linkName.textContent) {
                tooltip.textContent = linkName.textContent.trim();
            }
        }
    });
}

// Chame esta função após carregar a sidebar
setupTooltips();