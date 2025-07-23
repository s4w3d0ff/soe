class GoalProgressBar {
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

    formatAsDollars(cents) {
        // Convert cents to dollars and format with 2 decimal places
        return (cents / 100).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

// Initialize the progress bar when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.goalProgressBar = new GoalProgressBar();
});