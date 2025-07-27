// Add this to your existing script section
document.addEventListener('DOMContentLoaded', function() {
    const noticeTypeSelect = document.getElementById('noticeType');
    noticeTypeSelect.addEventListener('change', updateDynamicFields);
    updateDynamicFields(); // Initialize fields
});

function updateDynamicFields() {
    const noticeType = document.getElementById('noticeType').value;
    const dynamicFields = document.getElementById('dynamicFields');
    dynamicFields.innerHTML = ''; // Clear existing fields

    const fields = {
        sub: `
            <div class="input-group">
                <label>Sub Tier:</label>
                <input type="text" id="subTier" value="1000">
                <label>Is Prime:</label>
                <input type="checkbox" id="isPrime">
            </div>
            <div class="input-group">
                <label>Months in Advance:</label>
                <input type="number" id="durationMonths" value="1">
            </div>
        `,
        resub: `
            <div class="input-group">
                <label>Cumulative Months:</label>
                <input type="number" id="cumulativeMonths" value="10">
                <label>Duration Months:</label>
                <input type="number" id="durationMonths" value="1">
                <label>Streak Months:</label>
                <input type="number" id="streakMonths" value="0">
            </div>
            <div class="input-group">
                <label>Sub Tier:</label>
                <input type="text" id="subTier" value="1000">
                <label>Is Prime:</label>
                <input type="checkbox" id="isPrime">
                <label>Is Gift:</label>
                <input type="checkbox" id="isGift">
            </div>
        `,
        sub_gift: `
            <div class="input-group">
                <label>Duration Months:</label>
                <input type="number" id="durationMonths" value="1">
                <label>Cumulative Months:</label>
                <input type="number" id="cumulativeMonths" value="10">
                <label>Sub Tier:</label>
                <input type="text" id="subTier" value="1000">
                <label>Recipient Username:</label>
                <input type="text" id="recipientUserName" value="recipient_user">
            </div>
        `,
        community_sub_gift: `
            <div class="input-group">
                <label>Sub Tier:</label>
                <input type="text" id="subTier" value="1000">
                <label>Total:</label>
                <input type="number" id="total" value="5">
            </div>
        `,
        gift_paid_upgrade: `
            <div class="input-group">
                <label>Gifter Is Anonymous:</label>
                <input type="checkbox" id="gifterIsAnonymous">
                <label>Gifter Username:</label>
                <input type="text" id="gifterUserName" value="gifter_user">
            </div>
        `,
        prime_paid_upgrade: `
            <div class="input-group">
                <label>Sub Tier:</label>
                <input type="text" id="subTier" value="1000">
            </div>
        `,
        raid: `
            <div class="input-group">
                <label>Viewers:</label>
                <input type="number" id="viewers" value="100">
                <label>User Name:</label>
                <input type="text" id="raidUserName" value="raider_user">
            </div>
        `,
        pay_it_forward: `
            <div class="input-group">
                <label>Gifter Is Anonymous:</label>
                <input type="checkbox" id="gifterIsAnonymous">
                <label>Gifter Username:</label>
                <input type="text" id="gifterUserName" value="gifter_user">
            </div>
        `,
        announcement: `
            <div class="input-group">
                <label>Color:</label>
                <input type="color" id="announcementColor" value="#0000FF">
            </div>
        `,
        bits_badge_tier: `
            <div class="input-group">
                <label>Tier:</label>
                <input type="number" id="bitsTier" value="1000">
            </div>
        `,
        charity_donation: `
            <div class="input-group">
                <label>Charity Name:</label>
                <input type="text" id="charityName" value="Charity Name">
                <label>Amount:</label>
                <input type="number" id="charityAmount" value="10.0" step="0.1">
            </div>
        `
    };

    if (fields[noticeType]) {
        dynamicFields.innerHTML = fields[noticeType];
    }
}


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
        case 'channel.follow':
            data.user_name = document.getElementById('followUsername').value;
            break;
        case 'channel.chat.notification':
            data.notice_type = document.getElementById('noticeType').value;
            data.system_message = document.getElementById('systemMessage').value;
            data.user_name = document.getElementById('chatUserName').value;
            data.message = document.getElementById('userMessage').value;
            data.color = document.getElementById('chatColor').value;

            switch(data.notice_type) {
                case 'sub':
                    data.sub_tier = document.getElementById('subTier').value;
                    data.is_prime = document.getElementById('isPrime').checked;
                    data.duration_months = parseInt(document.getElementById('durationMonths').value);
                    break;
                case 'resub':
                    data.cumulative_months = parseInt(document.getElementById('cumulativeMonths').value);
                    data.duration_months = parseInt(document.getElementById('durationMonths').value);
                    data.streak_months = parseInt(document.getElementById('streakMonths').value);
                    data.sub_tier = document.getElementById('subTier').value;
                    data.is_prime = document.getElementById('isPrime').checked;
                    data.is_gift = document.getElementById('isGift').checked;
                    break;
                case 'sub_gift':
                    data.duration_months = parseInt(document.getElementById('durationMonths').value);
                    data.cumulative_months = parseInt(document.getElementById('cumulativeMonths').value);
                    data.sub_tier = document.getElementById('subTier').value;
                    data.recipient_user_name = document.getElementById('recipientUserName').value;
                    break;
                case 'community_sub_gift':
                    data.sub_tier = document.getElementById('subTier').value;
                    data.total = parseInt(document.getElementById('total').value);
                    break;
                case 'gift_paid_upgrade':
                    data.gifter_is_anonymous = document.getElementById('gifterIsAnonymous').checked;
                    data.gifter_user_name = document.getElementById('gifterUserName').value;
                    break;
                case 'prime_paid_upgrade':
                    data.sub_tier = document.getElementById('subTier').value;
                    break;
                case 'raid':
                    data.viewer_count = parseInt(document.getElementById('viewers').value);
                    data.user_name = document.getElementById('raidUserName').value;
                    break;
                case 'pay_it_forward':
                    data.gifter_is_anonymous = document.getElementById('gifterIsAnonymous').checked;
                    data.gifter_user_name = document.getElementById('gifterUserName').value;
                    break;
                case 'announcement':
                    data.color = document.getElementById('announcementColor').value;
                    break;
                case 'bits_badge_tier':
                    data.tier = parseInt(document.getElementById('bitsTier').value);
                    break;
                case 'charity_donation':
                    data.charity_name = document.getElementById('charityName').value;
                    data.amount = parseFloat(document.getElementById('charityAmount').value);
                    break;
            }
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

async function injectEvent(eventType) {
    const data = {};
    
    switch(eventType) {
        case 'channel.bits.use':
            data.bits = document.getElementById('injBitsAmount').value;
            break;
    }

    try {
        const response = await fetch(`/inject/${eventType}/`, {
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