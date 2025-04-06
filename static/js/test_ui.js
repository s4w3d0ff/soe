function showStatus(message, type) {
    const statusElement = document.getElementById('statusMessage');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
    statusElement.style.display = 'block';

    setTimeout(() => {
        statusElement.style.display = 'none';
    }, 5000);
}

async function testEvent(eventType) {
    const data = {};
    
    switch(eventType) {
        case 'channel.cheer':
        case 'channel.bits.use':
            data.bits = document.getElementById('bitsAmount').value;
            data.anon = document.getElementById('bitsAnon').checked;
            break;
        case 'channel.raid':
            data.viewers = document.getElementById('viewerAmount').value;
            data.from = document.getElementById('raidFrom').value;
            break;

        case 'channel.subscribe':
            data.tier = document.getElementById('subTier').value;
            data.gifted = document.getElementById('subGifted').checked;
            break;
        case 'channel.subscription.gift':
            data.total = document.getElementById('giftTotal').value;
            data.tier = document.getElementById('giftTier').value;
            data.anon = document.getElementById('giftAnon').checked;
            break;
        case 'channel.subscription.message':
            data.tier = document.getElementById('resubTier').value;
            data.months = document.getElementById('resubMonths').value;
            data.streak = document.getElementById('resubStreak').value;
            data.msg = document.getElementById('resubMsg').value;
            break;
        case 'channel.goal.progress':
            data.type = document.getElementById('goalType').value;
            data.current = document.getElementById('goalCurrent').value;
            data.target = document.getElementById('goalTarget').value;
            break;
        case 'channel.hype_train.progress':
        case 'channel.hype_train.end':
            data.level = document.getElementById('hypeLevel').value;
            data.total = document.getElementById('hypeTotal').value;
            data.progress = document.getElementById('hypeProgress').value;
            break;
        case 'channel.chat.notification':
            data.system_message = document.getElementById('notificationMsg').value;
            break;
        case 'channel.follow':
            data.user_name = document.getElementById('followUsername').value;
            break;
    }

    try {
        const response = await fetch(`/test/${eventType}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showStatus('Event sent successfully!', 'success');
        } else {
            showStatus('Failed to send event!', 'error');
        }
    } catch (error) {
        showStatus('Error sending event!', 'error');
    }
}