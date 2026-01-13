// Configurações
const API_BASE = '/api';
let CSRF_TOKEN = '';

// Estado da aplicação
let state = {
    categories: [],
    tags: [],
    showHidden: false,
    activeTab: 'categories'
};

// Elementos do DOM
const elements = {
    tabs: document.querySelectorAll('.tab-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    categoryForm: document.getElementById('add-category-form'),
    tagForm: document.getElementById('add-tag-form'),
    categoriesList: document.getElementById('categories-list'),
    tagsList: document.getElementById('tags-list'),
    toggleHiddenBtn: document.getElementById('toggle-hidden-categories'),
    hiddenCountSpan: document.getElementById('hidden-count'),
    tagsCountSpan: document.getElementById('tags-count'),
    categoryParentSelect: document.getElementById('category-parent'),
    iconPreview: document.getElementById('icon-preview'),
    categoryIconInput: document.getElementById('category-icon')
};

// Gerenciamento do modal de ícones
let iconModal = null;
let selectedIcon = null;
let currentIconTarget = null;

// Funções utilitárias
function showMessage(message, type = 'success') {
    document.querySelectorAll('.message').forEach(msg => msg.remove());
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    
    const container = document.querySelector('.container-categories');
    container.insertBefore(messageDiv, container.firstChild);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    } catch (e) {
        return dateString;
    }
}

function lightenColor(color, percent) {
    if (!color) return '#3B82F6';
    
    try {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        
        return `#${(
            0x1000000 +
            (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
            (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
            (B < 255 ? (B < 1 ? 0 : B) : 255)
        )
            .toString(16)
            .slice(1)}`;
    } catch (e) {
        return color;
    }
}

// ============================
// FUNÇÕES DE API - CATEGORIAS
// ============================
async function fetchCategories() {
    try {
        console.log('Buscando categorias da API...');
        
        const response = await fetch(`${API_BASE}/categories/`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) {
            console.error('Erro na resposta:', response.status, response.statusText);
            throw new Error(`Erro ao carregar categorias: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Dados de categorias recebidos:', data);
        
        let categories = [];
        
        if (data && data.results && Array.isArray(data.results)) {
            categories = data.results;
            console.log('Extraído array de categorias do campo results:', categories.length);
        } else if (Array.isArray(data)) {
            categories = data;
            console.log('Dados são um array direto:', categories.length);
        } else {
            console.error('Formato de dados inesperado:', data);
            categories = [];
        }
        
        state.categories = categories;
        console.log('Categorias no estado:', state.categories.length);
        
        renderCategories();
        populateParentCategorySelect();
        
    } catch (error) {
        console.error('Erro ao buscar categorias:', error);
        showMessage('Erro ao carregar categorias: ' + error.message, 'error');
        state.categories = [];
        renderCategories();
    }
}

async function createCategory(categoryData) {
    try {
        console.log('Enviando categoria:', categoryData);
        
        const response = await fetch(`${API_BASE}/categories/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(categoryData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao criar categoria');
        }
        
        const newCategory = await response.json();
        console.log('Categoria criada:', newCategory);
        
        state.categories.push(newCategory);
        renderCategories();
        populateParentCategorySelect();
        showMessage('Categoria criada com sucesso!');
        
        elements.categoryForm.reset();
        elements.iconPreview.className = 'fa-solid fa-shopping-cart';
        elements.categoryIconInput.value = 'shopping-cart';
        document.getElementById('category-color').value = '#3B82F6';
        document.getElementById('category-parent').value = '';
        
        return newCategory;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao criar categoria', 'error');
        throw error;
    }
}

async function updateCategory(categoryId, categoryData) {
    try {
        console.log('Atualizando categoria:', categoryId, categoryData);
        
        const response = await fetch(`${API_BASE}/categories/${categoryId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(categoryData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao atualizar categoria');
        }
        
        const updatedCategory = await response.json();
        console.log('Categoria atualizada:', updatedCategory);
        
        const index = state.categories.findIndex(c => c.category === categoryId);
        if (index !== -1) {
            state.categories[index] = updatedCategory;
        } else {
            state.categories.push(updatedCategory);
        }
        
        renderCategories();
        populateParentCategorySelect();
        showMessage('Categoria atualizada com sucesso!');
        
        return updatedCategory;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao atualizar categoria', 'error');
        throw error;
    }
}

async function deleteCategory(categoryId) {
    const category = state.categories.find(c => c.category === categoryId);
    
    if (category && category.subcategories_count > 0) {
        showMessage('Não é possível excluir uma categoria que possui subcategorias.', 'error');
        return;
    }
    
    if (!confirm('Tem certeza que deseja excluir esta categoria?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/categories/${categoryId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao excluir categoria');
        }
        
        state.categories = state.categories.filter(c => c.category !== categoryId);
        renderCategories();
        populateParentCategorySelect();
        showMessage('Categoria excluída com sucesso!');
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao excluir categoria', 'error');
    }
}

// ============================
// FUNÇÕES DE API - TAGS
// ============================
async function fetchTags() {
    try {
        console.log('Buscando tags da API...');
        
        const response = await fetch(`${API_BASE}/tags/`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) {
            console.error('Erro na resposta:', response.status, response.statusText);
            throw new Error(`Erro ao carregar tags: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Dados de tags recebidos:', data);
        
        let tags = [];
        
        if (data && data.results && Array.isArray(data.results)) {
            tags = data.results;
            console.log('Extraído array de tags do campo results:', tags.length);
        } else if (Array.isArray(data)) {
            tags = data;
            console.log('Dados são um array direto:', tags.length);
        } else {
            console.error('Formato de dados inesperado:', data);
            tags = [];
        }
        
        state.tags = tags;
        console.log('Tags no estado:', state.tags.length);
        
        renderTags();
        
    } catch (error) {
        console.error('Erro ao buscar tags:', error);
        showMessage('Erro ao carregar tags: ' + error.message, 'error');
        state.tags = [];
        renderTags();
    }
}

async function createTag(tagData) {
    try {
        console.log('Enviando tag:', tagData);
        
        const response = await fetch(`${API_BASE}/tags/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(tagData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao criar tag');
        }
        
        const newTag = await response.json();
        console.log('Tag criada:', newTag);
        
        state.tags.push(newTag);
        renderTags();
        showMessage('Tag criada com sucesso!');
        
        elements.tagForm.reset();
        document.getElementById('tag-color').value = '#6B7280';
        
        return newTag;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao criar tag', 'error');
        throw error;
    }
}

async function updateTag(tagId, tagData) {
    try {
        console.log('Atualizando tag:', tagId, tagData);
        
        const response = await fetch(`${API_BASE}/tags/${tagId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(tagData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao atualizar tag');
        }
        
        const updatedTag = await response.json();
        console.log('Tag atualizada:', updatedTag);
        
        const index = state.tags.findIndex(t => t.tag === tagId);
        if (index !== -1) {
            state.tags[index] = updatedTag;
        } else {
            state.tags.push(updatedTag);
        }
        
        renderTags();
        showMessage('Tag atualizada com sucesso!');
        
        return updatedTag;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao atualizar tag', 'error');
        throw error;
    }
}

async function deleteTag(tagId) {
    if (!confirm('Tem certeza que deseja excluir esta tag?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/tags/${tagId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao excluir tag');
        }
        
        state.tags = state.tags.filter(t => t.tag !== tagId);
        renderTags();
        showMessage('Tag excluída com sucesso!');
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao excluir tag', 'error');
    }
}

// ============================
// RENDERIZAÇÃO
// ============================
function populateParentCategorySelect() {
    if (!elements.categoryParentSelect) {
        console.error('Elemento categoryParentSelect não encontrado!');
        return;
    }
    
    console.log('Populando dropdown de categorias pai...');
    
    elements.categoryParentSelect.innerHTML = '';
    
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Sem categoria pai';
    elements.categoryParentSelect.appendChild(defaultOption);
    
    if (!Array.isArray(state.categories)) {
        console.error('state.categories não é um array:', state.categories);
        state.categories = [];
    }
    
    const rootCategories = state.categories.filter(cat => {
        return !cat.parent_category || cat.parent_category === null;
    });
    
    console.log('Categorias raiz encontradas:', rootCategories.length);
    
    rootCategories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.category;
        option.textContent = `${category.name} (${category.type_display || category.type})`;
        elements.categoryParentSelect.appendChild(option);
    });
    
    console.log(`Dropdown populado com ${elements.categoryParentSelect.options.length} opções`);
}

function renderCategories() {
    if (!elements.categoriesList) {
        console.error('Elemento categoriesList não encontrado!');
        return;
    }
    
    console.log('Renderizando categorias...');
    console.log('Total de categorias no estado:', state.categories.length);
    
    if (!Array.isArray(state.categories)) {
        console.error('state.categories não é um array durante renderização:', state.categories);
        state.categories = [];
    }
    
    const incomeCategories = state.categories.filter(c => c.type === 'IN');
    const expenseCategories = state.categories.filter(c => c.type === 'OUT');
    
    console.log('Categorias de receita:', incomeCategories.length);
    console.log('Categorias de despesa:', expenseCategories.length);
    
    let html = '';
    
    function renderCategoryTree(categories, parentId = null, level = 0) {
        let treeHtml = '';
        
        const filteredCategories = categories.filter(cat => {
            if (parentId === null) {
                return !cat.parent_category || cat.parent_category === null;
            } else {
                return cat.parent_category && cat.parent_category.category === parentId;
            }
        });
        
        console.log(`Nível ${level}: ${filteredCategories.length} categorias`);
        
        filteredCategories.forEach(category => {
            const isSubcategory = level > 0;
            const paddingLeft = level * 30;
            
            const lightColor = lightenColor(category.color || '#3B82F6', 30);
            const subcategoriesCount = category.subcategories_count || 0;
            
            treeHtml += `
                <div class="category-item ${isSubcategory ? 'subcategory' : ''}" 
                     data-id="${category.category}"
                     style="${isSubcategory ? `margin-left: ${paddingLeft}px;` : ''}">
                    <div class="category-main">
                        <div class="icon-box" style="background-color: ${lightColor};">
                            <i class="fa-solid fa-${category.icon || 'receipt'}" 
                               style="color: ${category.color || '#3B82F6'}"></i>
                        </div>
                        <div class="category-details">
                            <div class="name-row">
                                <strong class="category-name">${category.name}</strong>
                                <span class="badge ${category.type === 'IN' ? 'badge-success' : 'badge-danger'}">
                                    ${category.type_display || (category.type === 'IN' ? 'Receita' : 'Despesa')}
                                </span>
                                ${isSubcategory ? `
                                    <span class="badge badge-subcategory">
                                        <i class="fas fa-level-up-alt"></i> Subcategoria
                                    </span>
                                ` : ''}
                            </div>
                            <div class="category-info">
                                <span class="subtext">
                                    <i class="fas fa-clock"></i> Criada em: ${formatDate(category.created_at)}
                                </span>
                                <span class="subtext subcategories-count">
                                    <i class="fas fa-folder"></i> Subcategorias: <span>${subcategoriesCount}</span>
                                </span>
                            </div>
                        </div>
                        <div class="category-actions">
                            <button class="btn-edit" title="Editar">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-delete" title="Excluir">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="category-edit-form" style="display: none;"></div>
                </div>
            `;
            
            if (subcategoriesCount > 0) {
                treeHtml += renderCategoryTree(categories, category.category, level + 1);
            }
        });
        
        return treeHtml;
    }
    
    if (incomeCategories.length > 0) {
        html += `
            <div class="group-title receita-color">
                <i class="fas fa-chart-line-up"></i> Categorias de Receita 
                <span>(${incomeCategories.length})</span>
            </div>
        `;
        html += renderCategoryTree(incomeCategories);
    } else {
        html += `
            <div class="group-title receita-color">
                <i class="fas fa-chart-line-up"></i> Categorias de Receita 
                <span>(0)</span>
            </div>
            <div class="message info" style="margin: 10px 20px;">
                Nenhuma categoria de receita encontrada
            </div>
        `;
    }
    
    if (expenseCategories.length > 0) {
        html += `
            <div class="group-title despesa-color">
                <i class="fas fa-chart-line-down"></i> Categorias de Despesa 
                <span>(${expenseCategories.length})</span>
            </div>
        `;
        html += renderCategoryTree(expenseCategories);
    } else {
        html += `
            <div class="group-title despesa-color">
                <i class="fas fa-chart-line-down"></i> Categorias de Despesa 
                <span>(0)</span>
            </div>
            <div class="message info" style="margin: 10px 20px;">
                Nenhuma categoria de despesa encontrada
            </div>
        `;
    }
    
    if (state.categories.length === 0) {
        html = '<div class="message info">Nenhuma categoria encontrada. Adicione sua primeira categoria!</div>';
    }
    
    elements.categoriesList.innerHTML = html;
    attachCategoryEventListeners();
    
    console.log('Categorias renderizadas com sucesso');
}

function renderTags() {
    if (!elements.tagsList) {
        console.error('Elemento tagsList não encontrado!');
        return;
    }
    
    console.log('Renderizando tags...');
    console.log('Total de tags no estado:', state.tags.length);
    
    if (!Array.isArray(state.tags)) {
        console.error('state.tags não é um array:', state.tags);
        state.tags = [];
    }
    
    elements.tagsCountSpan.textContent = `${state.tags.length} tag${state.tags.length !== 1 ? 's' : ''}`;
    
    if (state.tags.length === 0) {
        elements.tagsList.innerHTML = '<div class="message info">Nenhuma tag encontrada. Adicione sua primeira tag!</div>';
        return;
    }
    
    let html = '';
    state.tags.forEach(tag => {
        const lightColor = lightenColor(tag.color || '#6B7280', 20);
        
        html += `
            <div class="tag-item" data-id="${tag.tag}" style="background-color: ${lightColor};">
                <div class="tag-content">
                    <span class="tag-name">${tag.name}</span>
                    <span class="tag-color-badge" style="background-color: ${tag.color || '#6B7280'}"></span>
                </div>
                <div class="tag-actions">
                    <button class="btn-tag-edit" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-tag-delete" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    elements.tagsList.innerHTML = html;
    attachTagEventListeners();
    
    console.log('Tags renderizadas com sucesso');
}

// ============================
// EVENT LISTENERS
// ============================
function attachCategoryEventListeners() {
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const categoryItem = this.closest('.category-item');
            const categoryId = categoryItem.dataset.id;
            const category = state.categories.find(c => c.category === categoryId);
            
            if (category) {
                showEditCategoryForm(categoryItem, category);
            }
        });
    });
    
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const categoryId = this.closest('.category-item').dataset.id;
            deleteCategory(categoryId);
        });
    });
}

function attachTagEventListeners() {
    document.querySelectorAll('.btn-tag-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const tagItem = this.closest('.tag-item');
            const tagId = tagItem.dataset.id;
            const tag = state.tags.find(t => t.tag === tagId);
            
            if (tag) {
                showEditTagForm(tagItem, tag);
            }
        });
    });
    
    document.querySelectorAll('.btn-tag-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const tagId = this.closest('.tag-item').dataset.id;
            deleteTag(tagId);
        });
    });
}

function showEditCategoryForm(categoryItem, category) {
    const editForm = categoryItem.querySelector('.category-edit-form');
    
    if (editForm.style.display === 'block') {
        editForm.style.display = 'none';
        return;
    }
    
    document.querySelectorAll('.category-edit-form').forEach(form => {
        if (form !== editForm) {
            form.style.display = 'none';
        }
    });
    
    if (!Array.isArray(state.categories)) {
        console.error('state.categories não é um array durante edição:', state.categories);
        state.categories = [];
    }
    
    const availableParents = state.categories.filter(cat => {
        if (cat.category === category.category) return false;
        
        function isAncestor(currentCat, potentialParentId) {
            if (!currentCat.parent_category) return false;
            if (currentCat.parent_category.category === potentialParentId) return true;
            return isAncestor(currentCat.parent_category, potentialParentId);
        }
        
        if (isAncestor(cat, category.category)) return false;
        return cat.type === category.type;
    });
    
    const parentCategoryId = category.parent_category ? 
        (typeof category.parent_category === 'object' ? category.parent_category.category : category.parent_category) : 
        '';
    
    editForm.innerHTML = `
        <form class="edit-category-form" data-id="${category.category}">
            <div class="inline-form" style="margin-top: 15px; padding: 15px; background: #f8fafc; border-radius: 8px;">
                <div class="input-group">
                    <input type="text" name="name" value="${category.name || ''}" placeholder="Nome" required>
                </div>
                <div class="input-group">
                    <select name="type" required>
                        <option value="OUT" ${category.type === 'OUT' ? 'selected' : ''}>Despesa</option>
                        <option value="IN" ${category.type === 'IN' ? 'selected' : ''}>Receita</option>
                    </select>
                </div>
                <div class="input-group">
                    <input type="color" name="color" value="${category.color || '#3B82F6'}" title="Escolha uma cor">
                </div>
                <div class="input-group icon-picker">
                    <div class="icon-picker-wrapper">
                        <div class="icon-preview">
                            <i class="fa-solid fa-${category.icon || 'receipt'}" id="edit-icon-preview-${category.category}"></i>
                        </div>
                        <input type="text" 
                               name="icon" 
                               value="${category.icon || 'receipt'}" 
                               placeholder="Ícone"
                               class="edit-category-icon">
                        <button type="button" class="btn-icon-picker open-edit-icon-modal" data-id="${category.category}">
                            <i class="fa-solid fa-list"></i>
                        </button>
                    </div>
                </div>
                <div class="input-group">
                    <select name="parent_category">
                        <option value="">Sem categoria pai</option>
                        ${availableParents.map(parent => `
                            <option value="${parent.category}" 
                                    ${(parentCategoryId === parent.category) ? 'selected' : ''}>
                                ${parent.name} (${parent.type_display || parent.type})
                            </option>
                        `).join('')}
                    </select>
                </div>
                <div class="input-group" style="display: flex; gap: 10px;">
                    <button type="submit" class="btn-add-dark">
                        <i class="fas fa-save"></i> Salvar
                    </button>
                    <button type="button" class="btn-cancel" style="background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                </div>
            </div>
        </form>
    `;
    
    editForm.style.display = 'block';
    
    const iconInput = editForm.querySelector('input[name="icon"]');
    const iconPreview = editForm.querySelector(`#edit-icon-preview-${category.category}`);
    
    if (iconInput && iconPreview) {
        iconInput.addEventListener('input', function() {
            iconPreview.className = `fa-solid fa-${this.value || 'receipt'}`;
        });
    }
    
    const editIconBtn = editForm.querySelector('.open-edit-icon-modal');
    if (editIconBtn) {
        editIconBtn.addEventListener('click', function() {
            const iconValue = editForm.querySelector('.edit-category-icon').value;
            openIconModal(
                { 
                    type: 'category-edit',
                    input: editForm.querySelector('.edit-category-icon'),
                    preview: editForm.querySelector(`#edit-icon-preview-${category.category}`)
                },
                iconValue
            );
        });
    }
    
    editForm.querySelector('.edit-category-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const categoryData = {
            name: formData.get('name'),
            type: formData.get('type'),
            color: formData.get('color'),
            icon: formData.get('icon'),
            parent_category: formData.get('parent_category') || null
        };
        
        await updateCategory(category.category, categoryData);
        editForm.style.display = 'none';
    });
    
    editForm.querySelector('.btn-cancel').addEventListener('click', function() {
        editForm.style.display = 'none';
    });
}

function showEditTagForm(tagItem, tag) {
    const tagContainer = tagItem.parentNode;
    
    // Remover formulários de edição existentes
    const existingForm = tagContainer.querySelector('.tag-edit-form');
    if (existingForm) {
        existingForm.remove();
        return;
    }
    
    const editForm = document.createElement('div');
    editForm.className = 'tag-edit-form';
    editForm.style.cssText = `
        margin-top: 10px;
        padding: 15px;
        background: #f8fafc;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    `;
    
    editForm.innerHTML = `
        <form class="edit-tag-form" data-id="${tag.tag}">
            <div class="inline-form">
                <div class="input-group">
                    <input type="text" name="name" value="${tag.name || ''}" placeholder="Nome da tag" required>
                </div>
                <div class="input-group">
                    <input type="color" name="color" value="${tag.color || '#6B7280'}" title="Escolha uma cor">
                </div>
                <div class="input-group">
                    <button type="submit" class="btn-add-dark">
                        <i class="fas fa-save"></i> Salvar
                    </button>
                    <button type="button" class="btn-cancel" style="background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                </div>
            </div>
        </form>
    `;
    
    tagContainer.insertBefore(editForm, tagItem.nextSibling);
    
    editForm.querySelector('.edit-tag-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const tagData = {
            name: formData.get('name'),
            color: formData.get('color')
        };
        
        await updateTag(tag.tag, tagData);
        editForm.remove();
    });
    
    editForm.querySelector('.btn-cancel').addEventListener('click', function() {
        editForm.remove();
    });
}

// ============================
// MODAL DE ÍCONES
// ============================
function initIconModal() {
    iconModal = document.getElementById('icon-modal');
    if (!iconModal) return;
    
    const modalContent = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Selecionar Ícone</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="icon-search">
                    <input type="text" id="icon-search" placeholder="Buscar ícone...">
                </div>
                <div class="icons-grid" id="icons-grid"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn-cancel">Cancelar</button>
                <button type="button" class="btn-confirm" disabled>Selecionar</button>
            </div>
        </div>
    `;
    
    iconModal.innerHTML = modalContent;
    
    const availableIcons = [
        'shopping-cart', 'home', 'car', 'utensils', 'heart', 'graduation-cap',
        'plane', 'gift', 'coffee', 'film', 'music', 'book', 'dumbbell',
        'briefcase', 'receipt', 'credit-card', 'wallet', 'money-bill-wave',
        'pizza-slice', 'wine-bottle', 'shirt', 'gamepad', 'mobile-alt',
        'wifi', 'lightbulb', 'water', 'gas-pump', 'stethoscope', 'pills',
        'dog', 'cat', 'baby', 'book-open', 'tools', 'palette', 'running',
        'cocktail', 'umbrella-beach', 'plane-departure', 'hotel', 'heartbeat',
        'hand-holding-usd', 'piggy-bank', 'chart-line', 'university',
        'handshake', 'question-circle', 'tag', 'tags', 'folder', 'folder-open',
        'layer-group', 'sitemap', 'project-diagram', 'stream'
    ];
    
    renderIcons(availableIcons);
    
    iconModal.querySelector('.modal-close').addEventListener('click', closeIconModal);
    iconModal.querySelector('.btn-cancel').addEventListener('click', closeIconModal);
    iconModal.querySelector('.btn-confirm').addEventListener('click', confirmIconSelection);
    
    const iconSearch = iconModal.querySelector('#icon-search');
    iconSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const filteredIcons = availableIcons.filter(icon => 
            icon.toLowerCase().includes(searchTerm)
        );
        renderIcons(filteredIcons);
    });
    
    iconModal.addEventListener('click', function(e) {
        if (e.target === iconModal) {
            closeIconModal();
        }
    });
}

function renderIcons(icons) {
    const iconsGrid = iconModal.querySelector('#icons-grid');
    if (!iconsGrid) return;
    
    iconsGrid.innerHTML = '';
    
    icons.forEach(iconName => {
        const iconItem = document.createElement('div');
        iconItem.className = 'icon-item';
        iconItem.dataset.icon = iconName;
        
        iconItem.innerHTML = `
            <i class="fa-solid fa-${iconName}"></i>
            <span>${iconName.replace(/-/g, ' ')}</span>
        `;
        
        iconItem.addEventListener('click', function() {
            iconsGrid.querySelectorAll('.icon-item').forEach(item => {
                item.classList.remove('selected');
            });
            
            this.classList.add('selected');
            selectedIcon = iconName;
            
            iconModal.querySelector('.btn-confirm').disabled = false;
        });
        
        iconsGrid.appendChild(iconItem);
    });
}

function openIconModal(targetInput, currentIcon) {
    currentIconTarget = targetInput;
    selectedIcon = currentIcon;
    
    if (iconModal) {
        iconModal.classList.add('active');
        
        const searchInput = iconModal.querySelector('#icon-search');
        if (searchInput) {
            searchInput.value = '';
            searchInput.focus();
        }
        
        if (currentIcon) {
            const iconItem = iconModal.querySelector(`[data-icon="${currentIcon}"]`);
            if (iconItem) {
                iconItem.classList.add('selected');
                const confirmBtn = iconModal.querySelector('.btn-confirm');
                if (confirmBtn) {
                    confirmBtn.disabled = false;
                }
            }
        } else {
            const confirmBtn = iconModal.querySelector('.btn-confirm');
            if (confirmBtn) {
                confirmBtn.disabled = true;
            }
        }
    }
}

function closeIconModal() {
    if (iconModal) {
        iconModal.classList.remove('active');
    }
    selectedIcon = null;
    currentIconTarget = null;
}

function confirmIconSelection() {
    if (selectedIcon && currentIconTarget) {
        if (currentIconTarget.type === 'category-add') {
            if (elements.categoryIconInput) {
                elements.categoryIconInput.value = selectedIcon;
            }
            if (elements.iconPreview) {
                elements.iconPreview.className = `fa-solid fa-${selectedIcon}`;
            }
        } else if (currentIconTarget.type === 'category-edit') {
            if (currentIconTarget.input) {
                currentIconTarget.input.value = selectedIcon;
            }
            if (currentIconTarget.preview) {
                currentIconTarget.preview.className = `fa-solid fa-${selectedIcon}`;
            }
        }
    }
    closeIconModal();
}

// ============================
// INICIALIZAÇÃO
// ============================
function init() {
    console.log('Inicializando gerenciamento de categorias e tags...');
    
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfTokenElement) {
        CSRF_TOKEN = csrfTokenElement.value;
        console.log('CSRF Token encontrado');
    } else {
        console.warn('CSRF Token não encontrado!');
    }
    
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            elements.tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            elements.tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tabId}-tab`).classList.add('active');
            
            state.activeTab = tabId;
            
            if (tabId === 'categories') {
                fetchCategories();
            } else if (tabId === 'tags') {
                fetchTags();
            }
        });
    });
    
    if (elements.categoryForm) {
        elements.categoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const nameInput = document.getElementById('category-name');
            const typeInput = document.getElementById('category-type');
            const colorInput = document.getElementById('category-color');
            const iconInput = document.getElementById('category-icon');
            const parentInput = document.getElementById('category-parent');
            
            if (!nameInput || !typeInput) {
                showMessage('Preencha todos os campos obrigatórios', 'error');
                return;
            }
            
            const categoryData = {
                name: nameInput.value,
                type: typeInput.value,
                color: colorInput ? colorInput.value : '#3B82F6',
                icon: iconInput ? iconInput.value : 'shopping-cart',
                parent_category: parentInput && parentInput.value ? parentInput.value : null
            };
            
            console.log('Criando categoria com dados:', categoryData);
            
            await createCategory(categoryData);
        });
    }
    
    if (elements.tagForm) {
        elements.tagForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const nameInput = document.getElementById('tag-name');
            const colorInput = document.getElementById('tag-color');
            
            if (!nameInput) {
                showMessage('Preencha o nome da tag', 'error');
                return;
            }
            
            const tagData = {
                name: nameInput.value,
                color: colorInput ? colorInput.value : '#6B7280'
            };
            
            console.log('Criando tag com dados:', tagData);
            
            await createTag(tagData);
        });
    }
    
    if (elements.categoryIconInput && elements.iconPreview) {
        elements.categoryIconInput.addEventListener('input', function() {
            elements.iconPreview.className = `fa-solid fa-${this.value || 'shopping-cart'}`;
        });
    }
    
    const openIconModalBtn = document.getElementById('open-icon-modal');
    if (openIconModalBtn) {
        openIconModalBtn.addEventListener('click', function() {
            const currentIcon = elements.categoryIconInput ? elements.categoryIconInput.value : 'shopping-cart';
            openIconModal(
                { type: 'category-add' },
                currentIcon
            );
        });
    }
    
    initIconModal();
    
    console.log('Carregando dados iniciais...');
    fetchCategories();
    
    // Se a aba de tags estiver ativa inicialmente, carregar tags também
    if (state.activeTab === 'tags') {
        fetchTags();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}