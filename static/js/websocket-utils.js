function createWebSocketConnection(endpoint, messageHandler, reconnectDelay = 3000) {
    let ws;

    function connect() {
        ws = new WebSocket('ws://' + window.location.host + endpoint);

        ws.addEventListener('open', () => {
            console.log('WebSocket connection established');
        });

        ws.addEventListener('error', (error) => {
            console.error('WebSocket error:', error);
        });

        ws.addEventListener('close', () => {
            console.log('WebSocket connection closed');
            setTimeout(connect, reconnectDelay);
        });

        ws.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                messageHandler(data);
            } catch (error) {
                console.error('Error processing message:', error);
            }
        });

        return ws;
    }

    return connect();
}