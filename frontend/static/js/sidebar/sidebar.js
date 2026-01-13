// frontend/static/js/sidebar.js

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const btn = document.getElementById('btn');
    const mainContent = document.querySelector('.main-content');
    
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
    
    // Função para atualizar ícone do menu (mantida por compatibilidade)
    // O ideal seria remover essa função e fazer apenas com CSS
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
            
            searchInput.addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const navItems = document.querySelectorAll('.nav-list li:not(.search-container)');
                
                navItems.forEach(item => {
                    const linkName = item.querySelector('.links_name');
                    if (linkName) {
                        const text = linkName.textContent.toLowerCase();
                        // Usa classe CSS em vez de manipular style.display diretamente
                        item.classList.toggle('hidden', !text.includes(searchTerm));
                    }
                });
            });
            
            // Limpar filtro quando campo for limpo com botão de limpar
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    const navItems = document.querySelectorAll('.nav-list li:not(.search-container)');
                    navItems.forEach(item => {
                        item.classList.remove('hidden');
                    });
                }
            });
        }
    }
    
    // Melhorar acessibilidade do sidebar
    function setupAccessibility() {
        // Fechar sidebar com tecla ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && window.innerWidth <= 768 && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                updateMenuIcon();
                saveSidebarState();
                btn.focus(); // Mantém foco no botão para acessibilidade
            }
        });
        
        // Focar no primeiro item da navegação quando sidebar abrir
        btn.addEventListener('click', function() {
            if (sidebar.classList.contains('open')) {
                const firstNavItem = document.querySelector('.nav-list li:first-child a');
                if (firstNavItem) {
                    setTimeout(() => firstNavItem.focus(), 300);
                }
            }
        });
    }
    
    // Configurar tooltips dinâmicos
    function setupTooltips() {
        const tooltips = document.querySelectorAll('.sidebar li .tooltip');
        
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
    
    // Inicializar sidebar
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
        
        // Configurar acessibilidade
        setupAccessibility();
        
        // Configurar tooltips
        setupTooltips();
        
        // Redimensionamento - apenas lógica, sem manipular estilos
        window.addEventListener('resize', function() {
            // Se estiver em mobile e sidebar aberta, salvar estado
            if (window.innerWidth > 768 && sidebar.classList.contains('open')) {
                // Manter sidebar aberta ao voltar para desktop
                saveSidebarState();
            }
        });
    }
    
    // Inicializar sidebar
    initSidebar();
    
    console.log('Sidebar initialized successfully');
});

// Função auxiliar para verificar se é dispositivo móvel
function isMobileDevice() {
    return window.innerWidth <= 768;
}

// Função para abrir sidebar programaticamente (para uso externo)
export function openSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const btn = document.getElementById('btn');
    
    if (sidebar && btn) {
        sidebar.classList.add('open');
        
        // Atualizar ícone (remover quando CSS assumir essa responsabilidade)
        btn.classList.replace('bx-menu', 'bx-menu-alt-right');
        
        // Salvar estado
        localStorage.setItem('sidebarOpen', 'true');
        
        return true;
    }
    return false;
}

// Função para fechar sidebar programaticamente (para uso externo)
export function closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const btn = document.getElementById('btn');
    
    if (sidebar && btn) {
        sidebar.classList.remove('open');
        
        // Atualizar ícone (remover quando CSS assumir essa responsabilidade)
        btn.classList.replace('bx-menu-alt-right', 'bx-menu');
        
        // Salvar estado
        localStorage.setItem('sidebarOpen', 'false');
        
        return true;
    }
    return false;
}

// Função para alternar sidebar programaticamente (para uso externo)
export function toggleSidebarState() {
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebar) {
        if (sidebar.classList.contains('open')) {
            return closeSidebar();
        } else {
            return openSidebar();
        }
    }
    return false;
}

// Função para atualizar informações do usuário dinamicamente
export function updateUserProfile(userData) {
    const userNameElement = document.querySelector('.user-name');
    const userEmailElement = document.querySelector('.user-email');
    const userAvatar = document.querySelector('.user-avatar');
    const avatarDefault = document.querySelector('.avatar-default');
    
    if (userData.name && userNameElement) {
        userNameElement.textContent = userData.name;
    }
    
    if (userData.email && userEmailElement) {
        userEmailElement.textContent = userData.email;
    }
    
    if (userData.avatarUrl && userAvatar) {
        userAvatar.src = userData.avatarUrl;
        userAvatar.style.display = 'block';
        if (avatarDefault) avatarDefault.style.display = 'none';
    } else if (userData.name && avatarDefault) {
        const initial = userData.name.charAt(0).toUpperCase();
        avatarDefault.textContent = initial;
        avatarDefault.setAttribute('data-initial', initial);
        
        // Atualizar cor do avatar
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ];
        let hash = 0;
        for (let i = 0; i < initial.length; i++) {
            hash = initial.charCodeAt(i) + ((hash << 5) - hash);
        }
        const color = colors[Math.abs(hash) % colors.length];
        avatarDefault.style.background = `linear-gradient(135deg, ${color} 0%, ${color}80 100%)`;
    }
    
    return true;
}

// Verificar e aplicar estado inicial baseado no dispositivo
document.addEventListener('DOMContentLoaded', function() {
    // Se for dispositivo móvel, fechar sidebar por padrão
    if (isMobileDevice()) {
        const savedState = localStorage.getItem('sidebarOpen');
        if (savedState === null) {
            localStorage.setItem('sidebarOpen', 'false');
        }
    }
});