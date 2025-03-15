class GoalProgressBar {
    constructor() {
        this.multipliers = {
            t1: 250,
            t2: 400,
            t3: 1200,
            bits: 1
        };
        
        this.currentValues = {
            t1: 0,
            t2: 0,
            t3: 1,
            bits: 0
        };
        
        this.goalTotal = 84000;
        this.setupWebSocket();
        this.updateDisplay();
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
            console.log('WebSocket connection closed. Attempting to reconnect...');
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }

    handleUpdate(data) {
        const { progress_type, amount } = data;
        
        if (progress_type === 'total') {
            this.goalTotal = amount;
        } else if (this.currentValues.hasOwnProperty(progress_type)) {
            this.currentValues[progress_type] = amount;
        }
        
        this.updateDisplay();
    }
    calculateCurrentTotal() {
        return Object.entries(this.currentValues).reduce((total, [type, amount]) => {
            return total + (amount * this.multipliers[type]);
        }, 0);
    }

    calculateTypeContribution(type) {
        return this.currentValues[type] * this.multipliers[type];
    }

    calculateTypePercentage(type) {
        const currentTotal = this.calculateCurrentTotal();
        if (currentTotal === 0) return 0;
        return (this.calculateTypeContribution(type) / this.goalTotal) * 100;
    }

    calculateNeededAmount(type) {
        if (this.goalTotal === 0) return 0;
        
        const currentTotal = this.calculateCurrentTotal();
        const remaining = Math.max(0, this.goalTotal - currentTotal);
        
        return Math.ceil(remaining / this.multipliers[type]);
    }

    handleUpdate(data) {
        const { progress_type, amount } = data;
        
        if (progress_type === 'total') {
            this.goalTotal = amount;
        } else if (this.currentValues.hasOwnProperty(progress_type)) {
            this.currentValues[progress_type] = amount;
        }
        
        this.updateDisplay();
    }

    updateDisplay() {
        // Update current values and needed values
        Object.keys(this.currentValues).forEach(type => {
            document.getElementById(`${type}-current`).textContent = 
                this.currentValues[type].toLocaleString();
            document.getElementById(`${type}-needed`).textContent = 
                this.calculateNeededAmount(type).toLocaleString();
            
            // Update progress bar segments
            const percentage = this.calculateTypePercentage(type);
            const segment = document.getElementById(`segment-${type}`);
            segment.style.width = `${percentage}%`;
            
            // Only show percentage text if there's enough room (more than 5%)
            if (percentage > 5) {
                segment.textContent = `${percentage.toFixed(1)}%`;
            } else {
                segment.textContent = '';
            }
        });

        // Update total progress
        const currentTotal = this.calculateCurrentTotal();
        const percentComplete = this.goalTotal > 0 
            ? Math.min(100, (currentTotal / this.goalTotal) * 100) 
            : 0;

        document.getElementById('goal-percent').textContent = percentComplete.toFixed(1);
        document.getElementById('current-amount').textContent = currentTotal.toLocaleString();
        document.getElementById('goal-total').textContent = this.goalTotal.toLocaleString();
    }
}

// Initialize the progress bar when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.goalProgressBar = new GoalProgressBar();
});