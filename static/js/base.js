// MyLedger - Base JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
        });
    }

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function () {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // User Dropdown
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });

        document.addEventListener('click', function () {
            userDropdown.classList.remove('show');
        });
    }

    // Notifications Panel
    const notificationsBtn = document.getElementById('notificationsBtn');
    const closeNotificationsBtn = document.getElementById('closeNotificationsBtn');
    const notificationsPanel = document.getElementById('notificationsPanel');

    if (notificationsBtn && notificationsPanel) {
        notificationsBtn.addEventListener('click', function () {
            notificationsPanel.classList.toggle('show');
        });

        if (closeNotificationsBtn) {
            closeNotificationsBtn.addEventListener('click', function () {
                notificationsPanel.classList.remove('show');
            });
        }
    }

    // Close notifications when clicking outside
    document.addEventListener('click', function (e) {
        if (notificationsPanel && notificationsPanel.classList.contains('show')) {
            if (!notificationsPanel.contains(e.target) && !notificationsBtn?.contains(e.target)) {
                notificationsPanel.classList.remove('show');
            }
        }
    });
});

// Funções globais
window.showToast = function (message, type = 'success') {
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
};