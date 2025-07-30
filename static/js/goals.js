class GoalProgressBar {
    constructor() {
        this.setupWebSocket();
    }
    setupWebSocket() {
        this.ws = new WebSocket('ws://' + window.location.host + '/goalsws');
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleUpdate(data);
        };
        this.ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };
        this.ws.onclose = () => {
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }
    formatAsDollars(cents) {
        return (cents / 100).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    handleUpdate(data) {
        const bar = document.getElementById('progressBar');
        // Find the highest goal_total as the main progress end
        let maxGoal = data.goals.reduce((a, b) => a.goal_total > b.goal_total ? a : b, data.goals[0]);
        let maxTotal = maxGoal.goal_total || 1;
        let current = data.current_total;
        let percent = Math.min(100, (current / maxTotal) * 100);

        document.getElementById('progressFill').style.width = `${percent}%`;

        document.getElementById('currentValueLabel').textContent = `Monthly Total: $${this.formatAsDollars(current)}`;
        document.getElementById('currentBitsLabel').textContent = `Bits: ${data.bits_total}`;
        document.getElementById('currentT1Label').textContent = `T1 Subs: ${data.subs_total.t1.amount}`;
        document.getElementById('currentT2Label').textContent = `T2 Subs: ${data.subs_total.t2.amount}`;
        document.getElementById('currentT3Label').textContent = `T3 Subs: ${data.subs_total.t3.amount}`;
        document.getElementById('maxGoalLabel').textContent = `Top Goal: $${this.formatAsDollars(maxTotal)}`;

        // Clear old
        Array.from(bar.querySelectorAll('.milestone, .milestone-label, .milestone-connector')).forEach(e => e.remove());

        // Place milestones (sorted left to right)
        const barWidth = bar.offsetWidth;
        let usedTops = [];
        // Sort by goal_total ascending (left to right)
        let sortedGoals = data.goals.slice().sort((a, b) => a.goal_total - b.goal_total);
        sortedGoals.forEach((goal, idx) => {
            let ratio = goal.goal_total / maxTotal;
            let left = Math.max(0, Math.min(1, ratio)) * barWidth;

            // Don't draw milestone at 0
            if (ratio === 0) return;

            // Percentage without decimals
            let displayPercent = Math.round(ratio * 100);

            // Label and connector
            const label = document.createElement('div');
            label.className = 'milestone-label';
            label.textContent = `${goal.goal_name} ($${this.formatAsDollars(goal.goal_total)})`;

            // Highlight label if reached
            if (goal.percent_complete >= 100) {
                label.classList.add('goal-reached');
            }

            const ms = document.createElement('div');
            ms.className = 'milestone';
            ms.style.left = `${left - 1}px`;

            // Offset so labels don't overlap vertically
            let labelTop = -89;
            for (let used of usedTops) {
                if (Math.abs(used.left - left) < 800) {
                    labelTop += 90;
                    ms.style.top = `calc(${labelTop}% )`;
                }
            }
            label.style.top = `calc(${labelTop}% )`;
            // Place milestone bar
            bar.appendChild(ms);

            const isSingleGoal = sortedGoals.length === 1;

            // Label and connector on the left
                label.classList.add('milestone-label-left');
                label.style.right = `calc(${barWidth - left + 8}px)`;
                label.style.left = "unset";

                const connector = document.createElement('div');
                connector.className = 'milestone-connector milestone-connector-left';
                connector.style.right = `calc(${barWidth - left - 1}px)`;
                connector.style.top = `calc(${labelTop + 4}% )`;
                bar.appendChild(connector);
            usedTops.push({left, labelTop});
            bar.appendChild(label);
        });

        document.getElementById('goalList').innerHTML = data.goals.map(goal => {
            let displayPercent = Math.round(goal.percent_complete);

            // Highlight goal name if reached
            let nameClass = goal.percent_complete >= 100 ? "goal-reached" : "";

            // Only show "to reach" line if any total needed is > 0
            let details = "";
            if (
                goal.bits_total_needed > 0 ||
                goal.t1_total_needed > 0 ||
                goal.t2_total_needed > 0 ||
                goal.t3_total_needed > 0
            ) {
                details = `<div class="goal-entry-details">
                    <span class="detail-amount">${goal.bits_total_needed}</span> <span class="detail-unit">bits</span> or <br />
                    <span class="detail-amount">${goal.t1_total_needed}</span> <span class="detail-unit">Tier 1 subs</span> or <br />
                    <span class="detail-amount">${goal.t2_total_needed}</span> <span class="detail-unit">Tier 2 subs</span> or <br />
                    <span class="detail-amount">${goal.t3_total_needed}</span> <span class="detail-unit">Tier 3 subs</span>
                </div>`;
            }
            return `<div class="goal-entry">
                <span class="detail-title"><strong class="${nameClass}">${goal.goal_name}</strong> ${displayPercent}%</span>
                ${details}
            </div>`;
        }).join('');
    }
}