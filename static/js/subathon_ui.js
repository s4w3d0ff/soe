function showStatus(message, type) {
    const statusElement = document.getElementById('statusMessage');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
    statusElement.style.display = 'block';

    setTimeout(() => {
        statusElement.style.display = 'none';
    }, 5000);
}

class SubathonController {
    constructor() {
        this.apiBaseUrl = '/subathon';
        this.previousStats = null;
        this.initializeEventListeners();
        this.setupWebSocket();
    }
    setupWebSocket() {
        this.ws = new WebSocket('ws://' + window.location.host + '/subathonws');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateStats(data.data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket connection closed. Attempting to reconnect...');
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }
    // API Methods
    async callApi(cmd, args = {}, method = 'POST') {
        try {
            const url = `${this.apiBaseUrl}/${cmd}`;

            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: method === 'POST' ? JSON.stringify(args) : undefined
            };

            const response = await fetch(url, options);
            const text = await response.text();

            let data;
            try {
                data = JSON.parse(text);
            } catch (error) {
                showStatus(`Failed to parse JSON: ${text}`, 'error');
                throw new Error(`Failed to parse JSON: ${text}`);
            }
            return data;
        } catch (error) {
            console.error('API Error:', error);
            showStatus(error.message, 'error');
            return null;
        }
    }
    updateStats(stats) {
        // Always update the remaining time
        const remainingTime = Math.round(stats.remaining);  // Round to the nearest integer
        document.getElementById('timeRemaining').textContent = this.formatTime(remainingTime);
        
        // Create a copy of stats without the 'remaining' field for comparison
        const statsForComparison = { ...stats };
        delete statsForComparison.remaining;
        
        // If we haven't stored previous stats or if the stats have changed
        if (!this.previousStats || !this.areStatsEqual(this.previousStats, statsForComparison)) {
            const statsDisplay = document.getElementById('statsDisplay');
            statsDisplay.innerHTML = '';
            
            for (const [key, value] of Object.entries(stats)) {
                if (key === "remaining") continue;  // Skip the remaining time field
                
                const labelElement = document.createElement('div');
                labelElement.className = 'stat-label';
                // Capitalize the first letter of the key and replace underscores with spaces
                const formattedKey = key.charAt(0).toUpperCase() + 
                                    key.slice(1).replace(/_/g, ' ');
                labelElement.innerHTML = `${formattedKey}: <span>${value}</span>`;
                statsDisplay.appendChild(labelElement);
            }
            
            // Update the stored previous stats
            this.previousStats = statsForComparison;
        }
    }
    
    areStatsEqual(stats1, stats2) {
        const keys1 = Object.keys(stats1);
        const keys2 = Object.keys(stats2);
        
        if (keys1.length !== keys2.length) return false;
        
        return keys1.every(key => {
            return stats1[key] === stats2[key];
        });
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        return `${hours}h ${minutes}m ${remainingSeconds}s`;
    }

    // Control Methods
    async controlSubathon(cmd) {
        const method = cmd === 'pause' || cmd === 'resume' || cmd === 'stats' ? 'GET' : 'POST';
        const response = await this.callApi(cmd, {}, method);
        if (response?.status) {
            this.updateStats(response.data);
        }
    }

    async startNewSubathon() {
        const init_mins = parseFloat(document.getElementById('initialMinutes').value) * 60
        const init_time = init_mins + parseFloat(document.getElementById('initialSeconds').value);
        const response = await this.callApi(`new/${init_time}`, {}, 'POST');
        if (response?.status) {
            this.updateStats(response.data);
        }
    }

    async addTime() {
        const amount = parseInt(document.getElementById('amount').value);
        const multiplier = document.getElementById('multiplier').value || null;
        const response = await this.callApi('addtime', { amount, multiplier }, 'POST');
        if (response?.status) {
            this.updateStats(response.data);
        }
    }

    async removeTime() {
        const amount = parseInt(document.getElementById('amount').value);
        const multiplier = document.getElementById('multiplier').value || null;
        const response = await this.callApi('removetime', { amount, multiplier }, 'POST');
        if (response?.status) {
            this.updateStats(response.data);
        }
    }

    // Initialization Methods
    initializeEventListeners() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button');
            if (!button) return;

            const action = button.dataset.action;
            if (!action) return;

            switch (action) {
                case 'pause':
                case 'resume':
                    this.controlSubathon(action);
                    break;
                case 'startNew':
                    this.startNewSubathon();
                    break;
                case 'addTime':
                    this.addTime();
                    break;
                case 'removeTime':
                    this.removeTime();
                    break;
            }
        });
    }
}