function formatUSD(cents) {
	// Convert cents to dollars and format as USD
	const dollars = (cents / 100).toFixed(2);
	return `$${dollars.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
}
class GoalBar {
	constructor(containerId, goalTotal = 100000) {
		this.container = document.getElementById(containerId);
		if (!this.container) {
			console.error(`Container with ID "${containerId}" not found`);
			return;
		}
		this.goalTotal = goalTotal;
		this.segments = new Map(); // Using Map to store segments by type
	}

	updateGoalTotal(newTotal) {
		if (!this.container) return;
		this.goalTotal = newTotal;
		this.render();
	}
	updateSegment(type, amount) {
		if (!this.container) return;
		
		// Store the previous value for animation
		const previousValue = this.segments.has(type) ? this.segments.get(type).value : 0;
		
		if (!this.segments.has(type)) {
			this.segments.set(type, {
				value: amount,  // Set the value directly to amount
				label: type,
				targetValue: amount,
				element: null
			});
		} else {
			const segment = this.segments.get(type);
			segment.value = amount;  // Update the value
			segment.targetValue = amount;
		}

		// Only render initially if this is the first segment
		if (this.segments.size === 1) {
			this.render();
		} else {
			this.updateSegmentWidth(type);
		}
	}
	updateSegmentWidth(type) {
		const segment = this.segments.get(type);
		if (!segment) return;

		// Update the legend
		const legend = this.createLegend();
		const oldLegend = this.container.querySelector('.legend-container');
		if (oldLegend) {
			this.container.replaceChild(legend, oldLegend);
		}

		// Find existing segment element or create it if it doesn't exist
		let segmentElement = this.container.querySelector(`.segment-${type}`);
		const isNewSegment = !segmentElement;
		
		if (isNewSegment) {
			// If the segment element doesn't exist, we need to create it
			const goalBar = this.container.querySelector('.goal-container');
			if (!goalBar) {
				this.render(); // Full render if goal bar doesn't exist
				return;
			}
			segmentElement = document.createElement('div');
			segmentElement.className = `progress-segment segment-${type}`;
			segmentElement.style.width = '0%';  // Only set to 0% for new segments
			goalBar.appendChild(segmentElement);
		}

		// Calculate new width
		const percentWidth = (segment.value / this.goalTotal * 100);
		
		// Update width with animation
		requestAnimationFrame(() => {
			if (isNewSegment) {
				// For new segments, add animation class after initial width of 0% is rendered
				requestAnimationFrame(() => {
					segmentElement.classList.add('animated');
					segmentElement.style.width = `${percentWidth}%`;
				});
			} else {
				// For existing segments, just update to the new width
				// The animation class should already be present
				segmentElement.style.width = `${percentWidth}%`;
			}
		});
	}

	getProgressTotal() {
		let total = 0;
		for (let segment of this.segments.values()) {
			total += segment.value;
		}
		return total;
	}
	createLegend() {
		const legendContainer = document.createElement('div');
		legendContainer.className = 'legend-container';

		const legendItems = document.createElement('div');
		legendItems.className = 'legend-items';

		// Create legend items for each segment
		for (let [type, segment] of this.segments) {
			const legendItem = document.createElement('div');
			legendItem.className = 'legend-item';

			const colorDot = document.createElement('span');
			colorDot.className = `color-dot ${type}`;

			const label = document.createElement('span');
			const percentOfTotal = (segment.value / this.goalTotal * 100).toFixed(1);
			label.textContent = `${type} ${percentOfTotal}%`;

			legendItem.appendChild(colorDot);
			legendItem.appendChild(label);
			legendItems.appendChild(legendItem);
		}

		// Add total progress to the right
		const totalProgress = document.createElement('div');
		const progressTotal = this.getProgressTotal();
		const totalProgressPercent = (progressTotal / this.goalTotal * 100).toFixed(1);
		totalProgress.textContent = `Monthly Goal: ${totalProgressPercent}% (${formatUSD(progressTotal)}/${formatUSD(this.goalTotal)})`;

		legendContainer.appendChild(legendItems);
		legendContainer.appendChild(totalProgress);

		return legendContainer;
	}
	render() {
		if (!this.container) return;
		
		this.container.innerHTML = '';
		const legend = this.createLegend();
		this.container.appendChild(legend);

		const goalBar = document.createElement('div');
		goalBar.className = 'goal-container';

		// Add all segments with their current widths
		for (let [type, segment] of this.segments) {
			const percentWidth = (segment.value / this.goalTotal * 100);
			
			const progressSegment = document.createElement('div');
			progressSegment.className = `progress-segment segment-${type}`;
			progressSegment.style.width = `${percentWidth}%`; // Set width immediately
			progressSegment.classList.add('animated');
			goalBar.appendChild(progressSegment);
		}

		this.container.appendChild(goalBar);
	}
}