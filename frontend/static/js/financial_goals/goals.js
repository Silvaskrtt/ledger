// frontend/static/js/financial_goals/goals.js

const goalsList = document.getElementById("goalsList");
const modal = document.getElementById("goalModal");

document.getElementById("openGoalModal").onclick = () => modal.classList.remove("hidden");
document.getElementById("closeGoalModal").onclick = () => modal.classList.add("hidden");

async function loadGoals() {
    const res = await fetch("/api/financial-goals/", {
        credentials: "same-origin"
    });

    if (!res.ok) {
        console.error("Erro ao carregar metas");
        return;
    }

    const goals = await res.json();

    goalsList.innerHTML = "";

    goals.forEach(goal => {
        const card = document.createElement("div");
        card.className = "goal-card";

        card.innerHTML = `
            <h3>${goal.name}</h3>
            <div class="goal-meta status-${goal.status}">
                ${goal.status}
            </div>

            <div class="progress-bar">
                <div class="progress" style="width:${goal.percent}%"></div>
            </div>

            <div class="goal-footer">
                R$ ${goal.current_amount} / R$ ${goal.target_amount} <br/>
                Até ${new Date(goal.deadline).toLocaleDateString()}
            </div>
        `;

        goalsList.appendChild(card);
    });
}

document.getElementById("goalForm").onsubmit = async (e) => {
    e.preventDefault();

    const formData = Object.fromEntries(new FormData(e.target));

    await fetch("/api/financial-goals/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify(formData)
    });

    modal.classList.add("hidden");
    e.target.reset();
    loadGoals();
};

loadGoals();

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(";").forEach(cookie => {
            const c = cookie.trim();
            if (c.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}
