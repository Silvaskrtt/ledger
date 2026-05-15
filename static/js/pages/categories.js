// MyLedger - Categories JavaScript (CONECTADO AO BACKEND)
// Funcionalidades da tela de gerenciamento de categorias

(function () {
    'use strict';

    // ===== DOM Elements =====
    const categoriesGrid = document.getElementById('categoriesGrid');
    const totalCategoriesSpan = document.getElementById('totalCategories');
    const mostUsedCategorySpan = document.getElementById('mostUsedCategory');
    const totalSpentByCategorySpan = document.getElementById('totalSpentByCategory');
    const categoryModal = document.getElementById('categoryModal');
    const deleteModal = document.getElementById('deleteModal');
    const categoryForm = document.getElementById('categoryForm');
    const modalTitle = document.getElementById('modalTitle');
    const submitBtnText = document.getElementById('submitBtnText');
    const categoryIdInput = document.getElementById('categoryId');
    const catNameInput = document.getElementById('cat_name');
    const catIconInput = document.getElementById('cat_icon');
    const catColorInput = document.getElementById('cat_color');
    const catBudgetInput = document.getElementById('cat_budget');
    const colorPreview = document.getElementById('colorPreview');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // ===== State =====
    let categories = [];
    let categoryToDelete = null;
    let editingId = null;
    let isLoading = false;

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(message, type = 'success') {
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
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ===== Load Categories from Backend =====
    async function loadCategories() {
        if (isLoading) return;
        isLoading = true;

        try {
            if (categoriesGrid) {
                categoriesGrid.innerHTML = `
                    <div class="loading-skeleton">
                        <div class="skeleton-card"></div>
                        <div class="skeleton-card"></div>
                        <div class="skeleton-card"></div>
                    </div>
                `;
            }

            const response = await fetch('/categories/api/categories/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();

            if (data.success) {
                categories = data.categories || [];
                renderCategories();
                await loadSummary();
            } else {
                throw new Error(data.error || 'Erro ao carregar categorias');
            }

        } catch (error) {
            console.error('Error loading categories:', error);
            showToast('Erro ao carregar categorias', 'error');
            if (categoriesGrid) {
                categoriesGrid.innerHTML = `
                    <div class="empty-state fade-up">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Erro ao carregar categorias</p>
                        <button onclick="location.reload()">Tentar novamente</button>
                    </div>
                `;
            }
        } finally {
            isLoading = false;
        }
    }

    // ===== Load Summary Statistics =====
    async function loadSummary() {
        try {
            const response = await fetch('/categories/api/categories/summary/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();

            if (data.success) {
                if (totalCategoriesSpan) {
                    totalCategoriesSpan.textContent = data.total_categories || 0;
                }
                if (mostUsedCategorySpan) {
                    mostUsedCategorySpan.textContent = data.most_used_category || '-';
                }
                if (totalSpentByCategorySpan) {
                    totalSpentByCategorySpan.textContent = formatCurrency(data.total_spent || 0);
                }
            }

        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }

    // ===== Render Categories =====
    function renderCategories() {
        if (!categoriesGrid) return;

        if (categories.length === 0) {
            categoriesGrid.innerHTML = `
                <div class="empty-state fade-up">
                    <i class="fas fa-folder-open"></i>
                    <p>Nenhuma categoria cadastrada</p>
                    <small>Clique em "Nova Categoria" para começar</small>
                </div>
            `;
            return;
        }

        categoriesGrid.innerHTML = categories.map(category => `
            <div class="category-card fade-up" style="--category-color: ${category.color || '#8A4FFF'}">
                <div class="category-header">
                    <div class="category-icon" style="background: ${category.color || '#8A4FFF'}20">
                        ${category.icon || '📌'}
                    </div>
                    <div class="category-info">
                        <div class="category-name">${escapeHtml(category.name)}</div>
                        <div class="category-stats">
                            <span><i class="fas fa-chart-line"></i> ${formatCurrency(category.total_spent || 0)}</span>
                            ${category.budget > 0 ? `<span><i class="fas fa-chart-simple"></i> ${formatCurrency(category.budget)}</span>` : ''}
                        </div>
                    </div>
                    <div class="category-actions">
                        ${!category.is_default ? `
                            <button class="category-action edit" onclick="editCategory(${category.id})" title="Editar">
                                <i class="fas fa-pencil-alt"></i>
                            </button>
                            <button class="category-action delete" onclick="confirmDelete(${category.id})" title="Excluir">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        ` : `
                            <span class="default-badge" title="Categoria padrão do sistema">
                                <i class="fas fa-check-circle"></i>
                            </span>
                        `}
                    </div>
                </div>
                <div class="category-type">
                    <span class="type-badge ${category.type}">
                        ${category.type === 'income' ? 'Receita' : 'Despesa'}
                    </span>
                </div>
                ${category.budget > 0 ? `
                <div class="category-footer">
                    <div class="category-budget">
                        <span class="budget-label">Orçamento</span>
                        <span class="budget-value">${formatCurrency(category.total_spent || 0)} / ${formatCurrency(category.budget)}</span>
                    </div>
                    <div class="budget-progress">
                        <div class="budget-progress-bar" style="width: ${Math.min(((category.total_spent || 0) / category.budget) * 100, 100)}%; background: ${category.color || '#8A4FFF'}"></div>
                    </div>
                </div>
                ` : ''}
            </div>
        `).join('');
    }

    // ===== Open Modal =====
    window.openCategoryModal = function (id = null) {
        editingId = id;

        if (id) {
            // Edit mode
            const category = categories.find(c => c.id === id);
            if (category) {
                modalTitle.textContent = 'Editar Categoria';
                submitBtnText.textContent = 'Atualizar';
                categoryIdInput.value = category.id;
                catNameInput.value = category.name;
                catIconInput.value = category.icon || '📌';
                if (catColorInput) catColorInput.value = category.color || '#8A4FFF';
                if (catBudgetInput) catBudgetInput.value = category.budget > 0 ? formatCurrency(category.budget) : '';
                if (colorPreview) colorPreview.style.background = category.color || '#8A4FFF';
            }
        } else {
            // Create mode
            modalTitle.textContent = 'Nova Categoria';
            submitBtnText.textContent = 'Salvar';
            categoryIdInput.value = '';
            catNameInput.value = '';
            catIconInput.value = '📌';
            if (catColorInput) catColorInput.value = '#8A4FFF';
            if (catBudgetInput) catBudgetInput.value = '';
            if (colorPreview) colorPreview.style.background = '#8A4FFF';
        }

        if (categoryModal) {
            categoryModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            if (catNameInput) catNameInput.focus();
        }
    };

    window.closeCategoryModal = function () {
        if (categoryModal) {
            categoryModal.style.display = 'none';
            document.body.style.overflow = '';
            editingId = null;
        }
    };

    // ===== Save Category (Backend) =====
    async function saveCategory(event) {
        event.preventDefault();

        const name = catNameInput?.value.trim();
        const icon = catIconInput?.value.trim() || '📌';
        const color = catColorInput?.value || '#8A4FFF';
        let budget = 0;

        if (catBudgetInput && catBudgetInput.value) {
            const budgetValue = catBudgetInput.value.replace(/[^0-9,]/g, '').replace(',', '.');
            budget = parseFloat(budgetValue) || 0;
        }

        if (!name) {
            showToast('Por favor, insira um nome para a categoria', 'error');
            return;
        }

        const submitBtn = categoryForm?.querySelector('button[type="submit"]');
        const originalText = submitBtn?.textContent || 'Salvar';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        }

        try {
            let url, method, response;

            if (editingId) {
                // Update existing category
                url = `/categories/api/categories/${editingId}/update/`;
                method = 'PUT';
                response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        name: name,
                        icon: icon,
                        color: color,
                        budget: budget
                    })
                });
            } else {
                // Create new category
                url = '/categories/api/categories/create/';
                method = 'POST';
                response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        name: name,
                        icon: icon,
                        color: color,
                        budget: budget,
                        type: 'expense'
                    })
                });
            }

            const data = await response.json();

            if (data.success) {
                showToast(data.message || (editingId ? 'Categoria atualizada com sucesso!' : 'Categoria criada com sucesso!'), 'success');
                closeCategoryModal();
                await loadCategories(); // Recarregar lista
            } else {
                showToast(data.error || 'Erro ao salvar categoria', 'error');
            }

        } catch (error) {
            console.error('Error saving category:', error);
            showToast('Erro ao conectar com o servidor', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    }

    // ===== Edit Category =====
    window.editCategory = function (id) {
        openCategoryModal(id);
    };

    // ===== Delete Category =====
    window.confirmDelete = function (id) {
        const category = categories.find(c => c.id === id);
        if (category && category.is_default) {
            showToast('Não é possível excluir categorias padrão do sistema', 'error');
            return;
        }
        categoryToDelete = id;
        if (deleteModal) {
            deleteModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    };

    function closeDeleteModal() {
        if (deleteModal) {
            deleteModal.style.display = 'none';
            document.body.style.overflow = '';
            categoryToDelete = null;
        }
    }

    async function deleteCategory() {
        if (categoryToDelete === null) return;

        const submitBtn = confirmDeleteBtn;
        const originalText = submitBtn?.textContent || 'Excluir';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Excluindo...';
        }

        try {
            const response = await fetch(`/categories/api/categories/${categoryToDelete}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                showToast(data.message || 'Categoria excluída com sucesso!', 'success');
                closeDeleteModal();
                await loadCategories(); // Recarregar lista
            } else {
                showToast(data.error || 'Erro ao excluir categoria', 'error');
            }

        } catch (error) {
            console.error('Error deleting category:', error);
            showToast('Erro ao conectar com o servidor', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    }

    // ===== Color Preview =====
    if (catColorInput && colorPreview) {
        catColorInput.addEventListener('input', function () {
            colorPreview.style.background = this.value;
        });
    }

    // ===== Budget Input Formatting =====
    if (catBudgetInput) {
        catBudgetInput.addEventListener('input', function (e) {
            let value = this.value.replace(/\D/g, '');
            if (value === '') {
                this.value = '';
                return;
            }
            value = (parseInt(value) / 100).toFixed(2);
            value = value.replace('.', ',');
            this.value = `R$ ${value}`;
        });
    }

    // ===== Event Listeners =====
    if (categoryForm) {
        categoryForm.addEventListener('submit', saveCategory);
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', deleteCategory);
    }

    // Close modals on escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeCategoryModal();
            closeDeleteModal();
        }
    });

    // Close modal on click outside
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function (e) {
            if (e.target === this) {
                closeCategoryModal();
                closeDeleteModal();
            }
        });
    });

    // ===== Initialize =====
    function init() {
        loadCategories();
    }

    // Export to global scope
    window.closeDeleteModal = closeDeleteModal;
    window.deleteCategory = deleteCategory;
    window.editCategory = editCategory;
    window.confirmDelete = confirmDelete;
    window.openCategoryModal = openCategoryModal;
    window.closeCategoryModal = closeCategoryModal;

    init();
})();