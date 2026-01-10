// Configurações
const API_BASE = '/api';
const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

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

// Templates
const categoryTemplate = document.getElementById('category-template');
const tagTemplate = document.getElementById('tag-template');

// Funções utilitárias
function showMessage(message, type = 'success') {
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
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function lightenColor(color, percent) {
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
}

// Funções de API
async function fetchCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories/`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar categorias');
        
        const categories = await response.json();
        state.categories = categories;
        renderCategories();
        populateParentCategorySelect();
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao carregar categorias', 'error');
    }
}

async function fetchTags() {
    try {
        const response = await fetch(`${API_BASE}/tags/`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar tags');
        
        const tags = await response.json();
        state.tags = tags;
        renderTags();
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao carregar tags', 'error');
    }
}

async function createCategory(categoryData) {
    try {
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
        state.categories.push(newCategory);
        renderCategories();
        populateParentCategorySelect();
        showMessage('Categoria criada com sucesso!');
        
        // Limpar formulário
        elements.categoryForm.reset();
        elements.iconPreview.className = 'fa-solid fa-shopping-cart';
        elements.categoryIconInput.value = 'shopping-cart';
        
        return newCategory;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao criar categoria', 'error');
        throw error;
    }
}

async function createTag(tagData) {
    try {
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
        state.tags.push(newTag);
        renderTags();
        showMessage('Tag criada com sucesso!');
        
        // Limpar formulário
        elements.tagForm.reset();
        document.getElementById('tag-color').value = '#6B7280';
        
        return newTag;
    } catch (error) {
        console.error('Erro:', error);
        showMessage(error.message || 'Erro ao criar tag', 'error');
        throw error;
    }
}

async function updateCategory(categoryId, categoryData) {
    try {
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
        const index = state.categories.findIndex(c => c.id_category === categoryId);
        if (index !== -1) {
            state.categories[index] = updatedCategory;
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

async function updateTag(tagId, tagData) {
    try {
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
        const index = state.tags.findIndex(t => t.id_tag === tagId);
        if (index !== -1) {
            state.tags[index] = updatedTag;
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

async function deleteCategory(categoryId) {
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
        
        state.categories = state.categories.filter(c => c.id_category !== categoryId);
        renderCategories();
        populateParentCategorySelect();
        showMessage('Categoria excluída com sucesso!');
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao excluir categoria', 'error');
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
        
        state.tags = state.tags.filter(t => t.id_tag !== tagId);
        renderTags();
        showMessage('Tag excluída com sucesso!');
    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro ao excluir tag', 'error');
    }
}

// Renderização
function populateParentCategorySelect() {
    if (!elements.categoryParentSelect) return;
    
    elements.categoryParentSelect.innerHTML = '<option value="">Sem categoria pai</option>';
    
    state.categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id_category;
        option.textContent = `${category.name} (${category.type_display})`;
        elements.categoryParentSelect.appendChild(option);
    });
}

function renderCategories() {
    if (!elements.categoriesList) return;
    
    // Agrupar categorias por tipo
    const expenseCategories = state.categories.filter(c => c.type === 'OUT');
    const incomeCategories = state.categories.filter(c => c.type === 'IN');
    
    let html = '';
    
    // Renderizar categorias de receita
    if (incomeCategories.length > 0) {
        html += `
            <div class="group-title receita-color">
                <i class="fas fa-chart-line-up"></i> Categorias de Receita 
                <span>(${incomeCategories.length})</span>
            </div>
        `;
        
        incomeCategories.forEach(category => {
            html += renderCategoryItem(category);
        });
    }
    
    // Renderizar categorias de despesa
    if (expenseCategories.length > 0) {
        html += `
            <div class="group-title despesa-color">
                <i class="fas fa-chart-line-down"></i> Categorias de Despesa 
                <span>(${expenseCategories.length})</span>
            </div>
        `;
        
        expenseCategories.forEach(category => {
            html += renderCategoryItem(category);
        });
    }
    
    if (state.categories.length === 0) {
        html = '<div class="message info">Nenhuma categoria encontrada. Adicione sua primeira categoria!</div>';
    }
    
    elements.categoriesList.innerHTML = html;
    attachCategoryEventListeners();
}

function renderCategoryItem(category) {
    const lightColor = lightenColor(category.color || '#3B82F6', 30);
    const subcategoriesCount = category.subcategories_count || 0;
    
    return `
        <div class="category-item" data-id="${category.id_category}">
            <div class="category-main">
                <div class="icon-box" style="background-color: ${lightColor}; color: ${category.color || '#3B82F6'}">
                    <i class="fa-solid fa-${category.icon || 'receipt'}"></i>
                </div>
                <div class="category-details">
                    <div class="name-row">
                        <strong class="category-name">${category.name}</strong>
                        <span class="badge ${category.type === 'IN' ? 'badge-success' : 'badge-danger'}">
                            ${category.type_display || (category.type === 'IN' ? 'Receita' : 'Despesa')}
                        </span>
                    </div>
                    <div class="category-info">
                        <span class="subtext">
                            <i class="fas fa-clock"></i> Criada em: ${formatDate(category.created_at)}
                        </span>
                        ${category.id_parent_category ? `
                            <span class="subtext">
                                <i class="fas fa-level-up-alt"></i> Subcategoria
                            </span>
                        ` : `
                            <span class="subtext subcategories-count">
                                <i class="fas fa-folder"></i> Subcategorias: <span>${subcategoriesCount}</span>
                            </span>
                        `}
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
            <div class="category-edit-form" style="display: none;">
                <!-- Formulário de edição será inserido dinamicamente -->
            </div>
        </div>
    `;
}

function renderTags() {
    if (!elements.tagsList) return;
    
    elements.tagsCountSpan.textContent = `${state.tags.length} tag${state.tags.length !== 1 ? 's' : ''}`;
    
    if (state.tags.length === 0) {
        elements.tagsList.innerHTML = '<div class="message info">Nenhuma tag encontrada. Adicione sua primeira tag!</div>';
        return;
    }
    
    let html = '';
    state.tags.forEach(tag => {
        const lightColor = lightenColor(tag.color || '#6B7280', 20);
        
        html += `
            <div class="tag-item" data-id="${tag.id_tag}" style="background-color: ${lightColor};">
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
}

// Event Listeners
function attachCategoryEventListeners() {
    // Botões de edição
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const categoryItem = this.closest('.category-item');
            const categoryId = categoryItem.dataset.id;
            const category = state.categories.find(c => c.id_category === categoryId);
            
            if (category) {
                showEditCategoryForm(categoryItem, category);
            }
        });
    });
    
    // Botões de exclusão
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const categoryId = this.closest('.category-item').dataset.id;
            deleteCategory(categoryId);
        });
    });
}

function attachTagEventListeners() {
    // Botões de edição de tag
    document.querySelectorAll('.btn-tag-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const tagItem = this.closest('.tag-item');
            const tagId = tagItem.dataset.id;
            const tag = state.tags.find(t => t.id_tag === tagId);
            
            if (tag) {
                showEditTagForm(tagItem, tag);
            }
        });
    });
    
    // Botões de exclusão de tag
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
    
    editForm.innerHTML = `
        <form class="edit-category-form" data-id="${category.id_category}">
            <div class="inline-form" style="margin-top: 15px; padding: 15px; background: #f8fafc; border-radius: 8px;">
                <div class="input-group">
                    <input type="text" name="name" value="${category.name}" placeholder="Nome" required>
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
                    <i class="fa-solid fa-${category.icon || 'receipt'}" id="edit-icon-preview-${category.id_category}"></i>
                    <input type="text" name="icon" value="${category.icon || 'receipt'}" 
                           placeholder="Ícone" list="icon-list">
                </div>
                <div class="input-group">
                    <select name="id_parent_category">
                        <option value="">Sem categoria pai</option>
                        ${state.categories
                            .filter(c => c.id_category !== category.id_category)
                            .map(c => `
                                <option value="${c.id_category}" ${c.id_category === category.id_parent_category ? 'selected' : ''}>
                                    ${c.name} (${c.type_display})
                                </option>
                            `).join('')}
                    </select>
                </div>
                <div class="input-group">
                    <button type="submit" class="btn-add-dark">
                        <i class="fas fa-save"></i> Salvar
                    </button>
                    <button type="button" class="btn-cancel" style="background: #ef4444; color: white; border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                </div>
            </div>
        </form>
    `;
    
    editForm.style.display = 'block';
    
    // Atualizar preview do ícone ao digitar
    const iconInput = editForm.querySelector('input[name="icon"]');
    const iconPreview = editForm.querySelector(`#edit-icon-preview-${category.id_category}`);
    
    iconInput.addEventListener('input', function() {
        iconPreview.className = `fa-solid fa-${this.value || 'receipt'}`;
    });
    
    // Submeter formulário de edição
    editForm.querySelector('.edit-category-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const categoryData = {
            name: formData.get('name'),
            type: formData.get('type'),
            color: formData.get('color'),
            icon: formData.get('icon'),
            id_parent_category: formData.get('id_parent_category') || null
        };
        
        await updateCategory(category.id_category, categoryData);
        editForm.style.display = 'none';
    });
    
    // Botão cancelar
    editForm.querySelector('.btn-cancel').addEventListener('click', function() {
        editForm.style.display = 'none';
    });
}

function showEditTagForm(tagItem, tag) {
    const editForm = document.createElement('div');
    editForm.className = 'tag-edit-form';
    editForm.innerHTML = `
        <form class="edit-tag-form" data-id="${tag.id_tag}" style="margin-top: 10px; padding: 15px; background: #f8fafc; border-radius: 8px;">
            <div class="inline-form">
                <div class="input-group">
                    <input type="text" name="name" value="${tag.name}" placeholder="Nome da tag" required>
                </div>
                <div class="input-group">
                    <input type="color" name="color" value="${tag.color || '#6B7280'}" title="Escolha uma cor">
                </div>
                <div class="input-group">
                    <button type="submit" class="btn-add-dark">
                        <i class="fas fa-save"></i> Salvar
                    </button>
                    <button type="button" class="btn-cancel" style="background: #ef4444; color: white; border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                </div>
            </div>
        </form>
    `;
    
    tagItem.parentNode.insertBefore(editForm, tagItem.nextSibling);
    
    // Submeter formulário de edição
    editForm.querySelector('.edit-tag-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const tagData = {
            name: formData.get('name'),
            color: formData.get('color')
        };
        
        await updateTag(tag.id_tag, tagData);
        editForm.remove();
    });
    
    // Botão cancelar
    editForm.querySelector('.btn-cancel').addEventListener('click', function() {
        editForm.remove();
    });
}

// Inicialização
function init() {
    // Configurar abas
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // Atualizar abas ativas
            elements.tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            elements.tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tabId}-tab`).classList.add('active');
            
            state.activeTab = tabId;
            
            // Carregar dados da aba se necessário
            if (tabId === 'categories' && state.categories.length === 0) {
                fetchCategories();
            } else if (tabId === 'tags' && state.tags.length === 0) {
                fetchTags();
            }
        });
    });
    
    // Formulário de categoria
    if (elements.categoryForm) {
        elements.categoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const categoryData = {
                name: formData.get('category-name'),
                type: formData.get('category-type'),
                color: formData.get('category-color'),
                icon: formData.get('category-icon'),
                id_parent_category: formData.get('category-parent') || null
            };
            
            await createCategory(categoryData);
        });
    }
    
    // Formulário de tag
    if (elements.tagForm) {
        elements.tagForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const tagData = {
                name: formData.get('tag-name'),
                color: formData.get('tag-color')
            };
            
            await createTag(tagData);
        });
    }
    
    // Atualizar preview do ícone
    if (elements.categoryIconInput && elements.iconPreview) {
        elements.categoryIconInput.addEventListener('input', function() {
            elements.iconPreview.className = `fa-solid fa-${this.value || 'shopping-cart'}`;
        });
    }
    
    // Botão para mostrar/ocultar categorias
    if (elements.toggleHiddenBtn) {
        elements.toggleHiddenBtn.addEventListener('click', function() {
            state.showHidden = !state.showHidden;
            this.innerHTML = `
                <i class="fa-solid fa-eye${state.showHidden ? '-slash' : ''}"></i>
                ${state.showHidden ? 'Ocultar' : 'Mostrar'} Ocultas
                (<span id="hidden-count">${elements.hiddenCountSpan.textContent}</span>)
            `;
            renderCategories();
        });
    }
    
    // Carregar dados iniciais
    fetchCategories();
}

// Iniciar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', init);