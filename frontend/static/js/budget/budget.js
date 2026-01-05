// frontend/static/js/budget/budget.js

const modal = document.getElementById('goalModal');
const openBtn = document.getElementById('openGoalModal');
const closeBtn = document.getElementById('closeGoalModal');
const form = document.getElementById('goalForm');

if (openBtn && modal) {
    openBtn.onclick = () => modal.style.display = 'flex';
}

if (closeBtn && modal) {
    closeBtn.onclick = () => modal.style.display = 'none';
}

document.getElementById('openGoalModal').onclick = () => {
    modal.style.display = 'flex';
};

document.getElementById('closeGoalModal').onclick = () => {
    modal.style.display = 'none';
};

document.getElementById('goalForm').onsubmit = async e => {
    e.preventDefault();

    const data = {
        id_category: e.target.id_category.value,
        limit_amount: e.target.limit_amount.value
    };

    const response = await fetch('/api/budget-category-limits/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        location.reload();
    } else {
        const err = await response.json();
        alert(err.detail || 'Erro ao salvar meta');
    }
};

const err = await response.json();
alert(JSON.stringify(err));
