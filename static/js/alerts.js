function addAlert(alert) {
	// Create the alert div
	const alertDiv = document.createElement('div');
	alertDiv.className = 'alert';
	alertDiv.id = alert.notice_type;

	// Create the system message span
	const sysMessageSpan = document.createElement('span');
	sysMessageSpan.className = 'sys_message';
	sysMessageSpan.textContent = alert.sys_message;

	// Append span to the alert div
	alertDiv.appendChild(sysMessageSpan);

	// Get the alerts container
	const container = document.getElementById('alerts-container');

	// Add the alert to the container
	container.appendChild(alertDiv);

	// Force a reflow before adding the show class
	alertDiv.offsetHeight;

	// Add show class to trigger the animation
	requestAnimationFrame(() => {
		alertDiv.classList.add('show');
	});

	// Set up removal timer
	setTimeout(() => {
		// Add the removing class to trigger the slide out animation
		alertDiv.classList.add('removing');
		
		// Remove the element after the animation completes
		setTimeout(() => {
			alertDiv.remove();
		}, 700); // Match the transition duration
	}, 7000);
}