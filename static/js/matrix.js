// Matrix animation variables
const canvas = document.getElementById('matrixCanvas');
const ctx = canvas.getContext('2d');
const characters = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ØÐ¥₿ᚠᚡᚢᚣᚤᚥᚦᚧᚨᚩᚪᚫᚬᚭᚮᚯᚰᚱᚴᚳᚵᚶᚸᚷᚹᚺᚻᚼᛄᛃᛇᛈᛉᛊᛋᛒᛗᛘᛝᛞᛟᛠᛢᛣᛤᛥᛦᛩᛨᛪᛰᛯᛱᛲ';

let grid = [];
let drops = [];
let columns;
let rows;

// Parameters object to store adjustable values
const params = {
	baseSpeed: 0.08,
	tailLength: 420,
	fontSize: 42,
	glowIntensity: 5,
	color: '#00241b'
};

class Cell {
	constructor() {
		this.char = characters[Math.floor(Math.random() * characters.length)];
		this.alpha = 0;
		this.active = false;
	}

	setNewChar() {
		this.char = characters[Math.floor(Math.random() * characters.length)];
	}
}

class Drop {
	constructor(x) {
		this.x = x;
		this.y = 0;
		this.speed = params.baseSpeed * (0.25 + Math.random() * 1.5);
		this.active = true;
		this.charChangeCounter = 0;
		this.charChangeDelay = 10;
	}
	
	update() {
		this.y += this.speed;
		const cellY = Math.floor(this.y);
		if (cellY < rows) {
			grid[this.x][cellY].active = true;
			this.charChangeCounter++;
			if (this.charChangeCounter >= this.charChangeDelay) {
				grid[this.x][cellY].setNewChar();
				this.charChangeCounter = 0;
			}
			grid[this.x][cellY].alpha = 1;
		}
		if (cellY >= rows) {
			this.y = 0;
			this.speed = params.baseSpeed * (0.25 + Math.random() * 1.5);
		}
	}
}

function initializeGrid() {
	columns = Math.floor(canvas.width / params.fontSize);
	rows = Math.floor(canvas.height / params.fontSize);
	
	grid = [];
	for (let x = 0; x < columns; x++) {
		grid[x] = [];
		for (let y = 0; y < rows; y++) {
			grid[x][y] = new Cell();
		}
	}
	
	drops = [];
	for (let x = 0; x < columns; x++) {
		drops[x] = new Drop(x);
	}
}

function resizeCanvas() {
	canvas.width = window.innerWidth;
	canvas.height = window.innerHeight;
	initializeGrid();
}

function drawMatrix() {
	ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
	ctx.fillRect(0, 0, canvas.width, canvas.height);
	ctx.font = `${params.fontSize}px monospace`;
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';
	const color = params.color;
	const r = parseInt(color.substr(1,2), 16);
	const g = parseInt(color.substr(3,2), 16);
	const b = parseInt(color.substr(5,2), 16);
	
	for (let x = 0; x < columns; x++) {
		for (let y = 0; y < rows; y++) {
			const cell = grid[x][y];
			if (cell.active) {
				const isHead = Math.floor(drops[x].y) === y;
				if (isHead) {
					ctx.fillStyle = '#FFF';
					ctx.shadowColor = params.color;
					ctx.shadowBlur = params.glowIntensity;
				} else {
					ctx.shadowBlur = 0;
					ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${cell.alpha})`;
				}
				const centerX = (x + 0.5) * params.fontSize;
				const centerY = (y + 0.5) * params.fontSize;
				ctx.fillText(cell.char, centerX, centerY);
				cell.alpha -= 1 / params.tailLength;
				if (cell.alpha <= 0) {
					cell.active = false;
				}
			}
		}
		drops[x].update();
	}
	ctx.shadowBlur = 0;
}

function animate() {
	drawMatrix();
	requestAnimationFrame(animate);
}