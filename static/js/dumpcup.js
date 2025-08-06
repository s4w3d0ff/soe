const config = {
    storageKey: 'cupPointLocations',
    defaultPoints: [
        {x:22,y:1436},
        {x:88,y:1684},
        {x:584,y:1716},
        {x:628,y:1614},
        {x:672,y:1612},
        {x:672,y:1694},
        {x:784,y:1664},
        {x:950,y:1828}
    ],
    wallThickness: 10,
    gravity: 0.75,
    ball: {
        radius: 25,
        restitution: 0.36,
        friction: 0.01,
        density: 0.09,
        spawnLocation: { 
            x: 200,
            y: 50
        }
    },
    ballPresets: {
        XL: { radius: 25, density: 0.5 },
        L: { radius: 25, density: 0.25 },
        M: { radius: 25, density: 0.1 },
        S: { radius: 25, density: 0.05 },
        XS: { radius: 25, density: 0.01 }
    }
};

class PolylineManager {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.points = config.defaultPoints;
        this.isDragging = false;
        this.selectedPoint = null;
        this.isHovering = false;
        this.pointRadius = 6;
        this.STORAGE_KEY = config.storageKey;
        this.points = this.loadState();
        // Bind event listeners
        this.setupEventListeners();
        // Create debounced save function
        this.debouncedSave = this.debounce(this.saveState.bind(this), 500);
    }

    loadState() {
        const savedState = localStorage.getItem(this.STORAGE_KEY);
        if (savedState) {
            const state = JSON.parse(savedState);
            return state.points;
        }
        return this.points;
    }

    saveState() {
        const state = {
            points: this.points,
            lastModified: new Date().toISOString()
        };
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(state));
    }

    drawPolyline(showPoints = false) {
        // Clear the canvas first
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw the line
        this.ctx.beginPath();
        this.ctx.moveTo(this.points[0].x, this.points[0].y);
        for (let i = 1; i < this.points.length; i++) {
            this.ctx.lineTo(this.points[i].x, this.points[i].y);
        }
        this.ctx.strokeStyle = 'transparent';
        this.ctx.stroke();
        
        // Draw points if needed
        if (showPoints || this.isDragging) {
            this.points.forEach((point, index) => {
                this.ctx.beginPath();
                this.ctx.arc(point.x, point.y, this.pointRadius, 0, Math.PI * 2);
                this.ctx.fillStyle = this.selectedPoint === index ? '#ff0000' : '#0000ff';
                this.ctx.fill();
            });
        }
    }

    // Utility Methods
    getMousePos(evt) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: evt.clientX - rect.left,
            y: evt.clientY - rect.top
        };
    }

    findClickedPoint(mousePos) {
        for (let i = 0; i < this.points.length; i++) {
            const dx = this.points[i].x - mousePos.x;
            const dy = this.points[i].y - mousePos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= this.pointRadius) {
                return i;
            }
        }
        return null;
    }

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Event Handlers
    handleMouseEnter = () => {
        this.isHovering = true;
        this.drawPolyline(true);
    }

    handleMouseLeave = () => {
        this.isHovering = false;
        this.isDragging = false;
        this.drawPolyline(false);
    }

    handleMouseDown = (e) => {
        const mousePos = this.getMousePos(e);
        const pointIndex = this.findClickedPoint(mousePos);
        
        if (pointIndex !== null) {
            this.isDragging = true;
            this.selectedPoint = pointIndex;
        }
    }

    handleMouseMove = (e) => {
        if (this.isDragging && this.selectedPoint !== null) {
            const mousePos = this.getMousePos(e);
            this.points[this.selectedPoint].x = mousePos.x;
            this.points[this.selectedPoint].y = mousePos.y;
            this.drawPolyline(true);
            this.debouncedSave();
        }
    }

    handleMouseUp = () => {
        if (this.isDragging) {
            this.saveState();
        }
        this.isDragging = false;
        if (this.isHovering) {
            this.drawPolyline(true);
        }
    }

    // Event Listener Setup
    setupEventListeners() {
        this.canvas.addEventListener('mouseenter', this.handleMouseEnter);
        this.canvas.addEventListener('mouseleave', this.handleMouseLeave);
        this.canvas.addEventListener('mousedown', this.handleMouseDown);
        this.canvas.addEventListener('mousemove', this.handleMouseMove);
        this.canvas.addEventListener('mouseup', this.handleMouseUp);
    }

    // Cleanup method
    destroy() {
        this.canvas.removeEventListener('mouseenter', this.handleMouseEnter);
        this.canvas.removeEventListener('mouseleave', this.handleMouseLeave);
        this.canvas.removeEventListener('mousedown', this.handleMouseDown);
        this.canvas.removeEventListener('mousemove', this.handleMouseMove);
        this.canvas.removeEventListener('mouseup', this.handleMouseUp);
    }
};

class PhysicsManager {
    constructor(canvas, polylineManager) {
        this.canvas = canvas;
        this.polylineManager = polylineManager;
        this.engine = Matter.Engine.create();
        this.world = this.engine.world;
        this.world.gravity.y = config.gravity;
        // Array to store polyline segments
        this.polylineSegments = [];
        // Create walls from polyline
        this.updatePolylineBody();
        // Array to store balls
        this.balls = [];
        // Start the physics simulation
        Matter.Runner.run(this.engine);
        // Start rendering
        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);
    }

    createBall(preset = null, imageUrl = null) {
        const selectedPreset = preset || this.getRandomPreset();

        const ball = Matter.Bodies.circle(
            config.ball.spawnLocation.x,
            config.ball.spawnLocation.y,
            selectedPreset.radius,
            {
                restitution: config.ball.restitution,
                friction: config.ball.friction,
                density: selectedPreset.density
            }
        );

        if (imageUrl) {
            const img = new Image();
            img.src = imageUrl;

            img.onload = () => {
                ball.image = img;
                Matter.World.add(this.world, ball);
                this.balls.push(ball);
            };

            img.onerror = () => {
                console.error(`Failed to load animated image: ${imageUrl}`);
                ball.image = null;
                // Even if image fails, still add the ball
                Matter.World.add(this.world, ball);
                this.balls.push(ball);
            };
        } else {
            // Fallback if no image is provided
            Matter.World.add(this.world, ball);
            this.balls.push(ball);
        }
    }

    getRandomPreset() {
        const presets = Object.values(config.ballPresets);
        const randomIndex = Math.floor(Math.random() * presets.length);
        return presets[randomIndex];
    }

    updatePolylineBody() {
        // Remove old polyline segments
        this.polylineSegments.forEach(segment => {
            Matter.World.remove(this.world, segment);
        });
        this.polylineSegments = [];

        // Create segments between each pair of points
        for (let i = 0; i < this.polylineManager.points.length - 1; i++) {
            const p1 = this.polylineManager.points[i];
            const p2 = this.polylineManager.points[i + 1];

            // Create a static line segment
            const segment = Matter.Bodies.rectangle(
                (p1.x + p2.x) / 2,  // x position (middle of segment)
                (p1.y + p2.y) / 2,  // y position (middle of segment)
                // Calculate length of the segment
                Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2)),
                config.wallThickness,
                {
                    isStatic: true,
                    angle: Math.atan2(p2.y - p1.y, p2.x - p1.x),  // rotation angle
                    render: {
                        fillStyle: 'transparent',
                        strokeStyle: 'transparent'
                    }
                }
            );

            this.polylineSegments.push(segment);
            Matter.World.add(this.world, segment);
        }
    }

    animate() {
        const ctx = this.canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw polyline
        this.polylineManager.drawPolyline(this.polylineManager.isHovering);
        
        // Filter and draw balls
        this.balls = this.balls.filter(ball => {
            // Remove balls that are out of bounds
            if (ball.position.y > this.canvas.height + 50 || 
                ball.position.x < -50 || 
                ball.position.x > this.canvas.width + 50) {
                Matter.World.remove(this.world, ball);
                return false;
            }
            return true;
        });

        // Draw each ball with image or default color
        this.balls.forEach(ball => {
            if (ball.image && ball.image.complete) {
                const desiredHeight = 40; // Fixed height for the image
                const scale = desiredHeight / ball.image.naturalHeight;
                const width = ball.image.naturalWidth * scale;

                ctx.save();
                ctx.translate(ball.position.x, ball.position.y);
                ctx.rotate(ball.angle);

                // Draw image centered at (0, 0) in the rotated context
                ctx.drawImage(
                    ball.image,
                    -width / 2,  // Center the image horizontally
                    -desiredHeight / 2,  // Center the image vertically
                    width,
                    desiredHeight
                );

                ctx.restore();
            } else {
                // Fallback to default color
                ctx.beginPath();
                ctx.arc(
                    ball.position.x,
                    ball.position.y,
                    ball.circleRadius,
                    0,
                    2 * Math.PI
                );
                ctx.fillStyle = '#ff4444';
                ctx.fill();
            }
        });

        requestAnimationFrame(this.animate);
    }

    destroy() {
        Matter.Runner.stop(this.engine);
        Matter.World.clear(this.world);
        Matter.Engine.clear(this.engine);
    }
}