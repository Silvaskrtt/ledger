// MyLedger - Categories JavaScript
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

    // ===== Sample Data =====
    const sampleCategories = [
        { id: 1, name: 'Alimentação', icon: '🍔', color: '#8A4FFF', budget: 800, spent: 342.50 },
        { id: 2, name: 'Transporte', icon: '🚗', color: '#5E2C9A', budget: 300, spent: 28.90 },
        { id: 3, name: 'Lazer', icon: '🎮', color: '#c084fc', budget: 400, spent: 39.90 },
        { id: 4, name: 'Moradia', icon: '🏠', color: '#6366f1', budget: 1500, spent: 1500 },
        { id: 5, name: 'Trabalho', icon: '💼', color: '#10b981', budget: 0, spent: 6200 },
        { id: 6, name: 'Educação', icon: '📚', color: '#ec4899', budget: 200, spent: 199 }
    ];

    // ===== Helper Functions =====
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function formatBudgetInput(value) {
        let number = value.replace(/\D/g, '');
        number = (parseInt(number) / 100).toFixed(2);
        return number !== 'NaN' ? number : '0';
    }

    // ===== Load Categories =====
    function loadCategories() {
        try {
            const savedCategories = localStorage.getItem('myledger_categories');
            if (savedCategories) {
                categories = JSON.parse(savedCategories);
            } else {
                categories = [...sampleCategories];
                saveCategories();
            }
            renderCategories();
            updateSummary();
        } catch (error) {
            console.error('Error loading categories:', error);
            showToast('Erro ao carregar categorias', 'error');
        }
    }

    function saveCategories() {
        localStorage.setItem('myledger_categories', JSON.stringify(categories));
    }

    // ===== Render Categories =====
    function renderCategories() {
        if (!categoriesGrid) return;

        if (categories.length === 0) {
            categoriesGrid.innerHTML = `
                <div class="empty-state fade-up">
                    <i class="fas fa-folder-open"></i>
                    <p>${window.translations?.noCategories || 'Nenhuma categoria cadastrada'}</p>
                    <small>${window.translations?.addCategoryHint || 'Clique em "Nova Categoria" para começar'}</small>
                </div>
            `;
            return;
        }

        categoriesGrid.innerHTML = categories.map(category => `
            <div class="category-card fade-up" style="--category-color: ${category.color}">
                <div class="category-header">
                    <div class="category-icon">${category.icon || '📌'}</div>
                    <div class="category-info">
                        <div class="category-name">${escapeHtml(category.name)}</div>
                        <div class="category-stats">
                            <span><i class="fas fa-chart-line"></i> ${formatCurrency(category.spent || 0)}</span>
                            ${category.budget > 0 ? `<span><i class="fas fa-chart-simple"></i> ${formatCurrency(category.budget)}</span>` : ''}
                        </div>
                    </div>
                    <div class="category-actions">
                        <button class="category-action edit" onclick="editCategory(${category.id})" title="Editar">
                            <i class="fas fa-pencil-alt"></i>
                        </button>
                        <button class="category-action delete" onclick="confirmDelete(${category.id})" title="Excluir">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                ${category.budget > 0 ? `
                <div class="category-footer">
                    <div class="category-budget">
                        <span class="budget-label">Orçamento</span>
                        <span class="budget-value">${formatCurrency(category.spent || 0)} / ${formatCurrency(category.budget)}</span>
                    </div>
                    <div class="budget-progress">
                        <div class="budget-progress-bar" style="width: ${Math.min(((category.spent || 0) / category.budget) * 100, 100)}%; background: ${category.color}"></div>
                    </div>
                </div>
                ` : ''}
            </div>
        `).join('');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== Update Summary =====
    function updateSummary() {
        if (totalCategoriesSpan) {
            totalCategoriesSpan.textContent = categories.length;
        }

        if (mostUsedCategorySpan) {
            // Find category with highest spent
            const mostUsed = [...categories].sort((a, b) => (b.spent || 0) - (a.spent || 0))[0];
            mostUsedCategorySpan.textContent = mostUsed ? mostUsed.name : '-';
        }

        if (totalSpentByCategorySpan) {
            const totalSpent = categories.reduce((sum, cat) => sum + (cat.spent || 0), 0);
            totalSpentByCategorySpan.textContent = formatCurrency(totalSpent);
        }
    }

    // ===== Open Modal =====
    window.openCategoryModal = function (id = null) {
        editingId = id;

        if (id) {
            // Edit mode
            const category = categories.find(c => c.id === id);
            if (category) {
                modalTitle.textContent = window.translations?.editCategory || 'Editar Categoria';
                submitBtnText.textContent = window.translations?.update || 'Atualizar';
                categoryIdInput.value = category.id;
                catNameInput.value = category.name;
                catIconInput.value = category.icon || '';
                catColorInput.value = category.color;
                if (catBudgetInput) catBudgetInput.value = formatCurrency(category.budget || 0);
                if (colorPreview) colorPreview.style.background = category.color;
            }
        } else {
            // Create mode
            modalTitle.textContent = window.translations?.newCategory || 'Nova Categoria';
            submitBtnText.textContent = window.translations?.save || 'Salvar';
            categoryIdInput.value = '';
            catNameInput.value = '';
            catIconInput.value = '';
            catColorInput.value = '#8A4FFF';
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

    // ===== Save Category =====
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

        if (editingId) {
            // Update existing category
            const index = categories.findIndex(c => c.id === editingId);
            if (index !== -1) {
                categories[index] = {
                    ...categories[index],
                    name: name,
                    icon: icon,
                    color: color,
                    budget: budget
                };
                showToast('Categoria atualizada com sucesso!', 'success');
            }
        } else {
            // Create new category
            const newCategory = {
                id: Date.now(),
                name: name,
                icon: icon,
                color: color,
                budget: budget,
                spent: 0
            };
            categories.push(newCategory);
            showToast('Categoria criada com sucesso!', 'success');
        }

        saveCategories();
        renderCategories();
        updateSummary();
        closeCategoryModal();
    }

    // ===== Edit Category =====
    window.editCategory = function (id) {
        openCategoryModal(id);
    };

    // ===== Delete Category =====
    window.confirmDelete = function (id) {
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

    function deleteCategory() {
        if (categoryToDelete !== null) {
            const index = categories.findIndex(c => c.id === categoryToDelete);
            if (index !== -1) {
                categories.splice(index, 1);
                saveCategories();
                renderCategories();
                updateSummary();
                showToast('Categoria excluída com sucesso!', 'success');
            }
            closeDeleteModal();
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
            value = (parseInt(value) / 100).toFixed(2);
            this.value = formatCurrency(value);
        });
    }

    // ===== Show Toast =====
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

    window.translations = {
        noCategories: 'Nenhuma categoria cadastrada',
        addCategoryHint: 'Clique em "Nova Categoria" para começar',
        newCategory: 'Nova Categoria',
        editCategory: 'Editar Categoria',
        save: 'Salvar',
        update: 'Atualizar'
    };

    init();
})();