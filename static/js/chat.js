const STORAGE_KEY = 'chatMessages';
const MAX_MESSAGES = 9;

// Function to load saved messages from localStorage
function loadSavedMessages() {
	const savedMessages = localStorage.getItem(STORAGE_KEY);
	if (savedMessages) {
		const messages = JSON.parse(savedMessages);
		// Display messages in reverse order to maintain chronological order
		messages.reverse().forEach(message => updateChatbox(message));
	}
}

// Function to save messages to localStorage
function saveMessages(message) {
	let messages = [];
	const savedMessages = localStorage.getItem(STORAGE_KEY);
	
	if (savedMessages) {
		messages = JSON.parse(savedMessages);
	}

	// Add new message to the beginning of the array
	messages.unshift(message);
	
	// Keep only the most recent MAX_MESSAGES
	if (messages.length > MAX_MESSAGES) {
		messages = messages.slice(0, MAX_MESSAGES);
	}

	localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
}

// Updated updateChatbox function
function updateChatbox(message) {
	const chatbox = document.getElementById('chatbox');
	const msgid = message.id;
	
	if (!document.getElementById(msgid)) {
		const messageDiv = document.createElement('div');
		messageDiv.classList.add('message', 'fade-in');
		messageDiv.setAttribute('id', msgid);
		
		const badgesSpan = document.createElement('span');
		badgesSpan.setAttribute('class', 'badges');
		
		// Loop through the badges array and create img elements
		message.badges.forEach(badgeUrl => {
			const badgeImg = document.createElement('img');
			badgeImg.setAttribute('src', badgeUrl);
			badgeImg.setAttribute('class', 'badge');
			badgesSpan.appendChild(badgeImg);
		});
		
		const usernameSpan = document.createElement('span');
		usernameSpan.setAttribute('class', 'username');
		usernameSpan.setAttribute('style', 'color: ' + message.color + ';');
		usernameSpan.textContent = message.user + ': ';
		
		const textSpan = document.createElement('span');
		textSpan.setAttribute('class', 'text');
		textSpan.innerHTML = message.text;
		
		messageDiv.appendChild(badgesSpan);
		messageDiv.appendChild(usernameSpan);
		messageDiv.appendChild(textSpan);
		
		// Make sure we dont have more than MAX_MESSAGES messages, removing the oldest
		const currentMessages = chatbox.getElementsByClassName('message');
		if (currentMessages.length >= MAX_MESSAGES) {
			chatbox.removeChild(currentMessages[currentMessages.length - 1]);
		}
		
		chatbox.prepend(messageDiv);
		
		// Save the message to localStorage
		saveMessages(message);
	}
}