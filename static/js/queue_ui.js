function showStatus(message, type) {
    const statusElement = document.getElementById('statusMessage');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
    statusElement.style.display = 'block';

    setTimeout(() => {
        statusElement.style.display = 'none';
    }, 2000);
}

class QueueManager {
    constructor() {
        this.queueContainer = document.getElementById('queueItems');
        this.initialize();
    }

    initialize() {
        this.refreshQueueItems();
        // Refresh queue every 1 second
        setInterval(() => this.refreshQueueItems(), 3000);
    }

    async refreshQueueItems() {
        try {
            const response = await fetch('/queue/current');
            const data = await response.json();
            
            if (data.status) {
                this.displayQueueItems(data.data);
                this.displayPausedStatus(data.paused);
            } else {
                console.error('Failed to fetch queue items');
            }
        } catch (error) {
            console.error('Error fetching queue:', error);
        }
    }
    async pauseQueue() {
        try {
            const response = await fetch('/queue/pause');
            const data = await response.json();
            
            if (data.status) {
                showStatus('Queue paused', 'success');
                console.log('Queue paused successfully');
            } else {
                showStatus('Queue failed to pause', 'error');
                console.error('Failed to pause queue');
            }
        } catch (error) {
            console.error('Error pausing queue:', error);
        }
    }
    async resumeQueue() {
        try {
            const response = await fetch('/queue/resume');
            const data = await response.json();
            
            if (data.status) {
                showStatus('Queue resumed', 'success');
                console.log('Queue resumed successfully');
            } else {
                showStatus('Queue failed to resume', 'error');
                console.error('Failed to resume queue');
            }
        } catch (error) {
            console.error('Error resuming queue:', error);
        }
    }
    async removeItem(itemId) {
        try {
            const response = await fetch(`/queue/remove/${itemId}`);
            const data = await response.json();
            
            if (data.status) {
                // Refresh the queue after removal
                this.refreshQueueItems();
            } else {
                console.error('Failed to remove item');
            }
        } catch (error) {
            console.error('Error removing item:', error);
        }
    }

    formatTimestamp(timestamp) {
        return new Date(timestamp * 1000).toLocaleString();
    }

    displayPausedStatus(status) {
        if (status) {
            showStatus('Queue is paused', 'error');
        } else {
            console.log('Queue is not paused');
        }
    }
    displayQueueItems(items) {
        this.queueContainer.innerHTML = '';
        
        if (items.length === 0) {
            this.queueContainer.innerHTML = '<div class="queue-item" style="text-align: center; font-size: 1.5em;">Queue is empty</div>';
            return;
        }

        items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'queue-item';
            
            const priorityLabel = document.createElement('span');
            priorityLabel.className = `queue-item-priority priority-${item.priority}`;
            priorityLabel.textContent = `P${item.priority}`;

            const itemContent = `
                <div class="queue-item-header">
                    ${priorityLabel.outerHTML}
                    <span class="q-item-channel">${item.channel}</span>
                    <span class="queue-item-username">${item.user_name}</span>
                </div>
                <div class="queue-item-info">
                    <span class="timestamp">${this.formatTimestamp(item.timestamp)}</span>
                </div>
                <div class="queue-item-actions">
                    <div class="data-content">
                        ${this.formatData(item.data)}
                    </div>
                    <button onclick="queueManager.removeItem('${item.item_id}')">Remove</button>
                </div>
            `;

            itemElement.innerHTML = itemContent;
            this.queueContainer.appendChild(itemElement);
        });
    }

    formatData(data) {
        // Format the data object for display
        // Customize this based on your data structure
        return Object.entries(data)
            .map(([key, value]) => `<div><strong>${key}:</strong> ${value}</div>`)
            .join('');
    }
}

