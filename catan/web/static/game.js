const socket = io();

// State
let gameState = null;
let playerId = null; // Username
let roomId = null;
let isHost = false;

// DOM Elements
const views = {
    lobby: document.getElementById('lobby-view'),
    game: document.getElementById('game-view')
};

const lobby = {
    usernameInput: document.getElementById('username'),
    createBtn: document.getElementById('create-game-btn'),
    joinBtn: document.getElementById('join-game-btn'),
    roomIdInput: document.getElementById('room-id-input'),
    status: document.getElementById('lobby-status'),
    currentRoomId: document.getElementById('current-room-id'),
    playerList: document.getElementById('player-list'),
    startBtn: document.getElementById('start-game-btn'),
    waitingMsg: document.getElementById('waiting-msg')
};

const gameUI = {
    board: document.getElementById('game-board'),
    playersContainer: document.getElementById('players-container'),
    logContainer: document.getElementById('log-container'),
    turnIndicator: document.getElementById('current-turn-player'),
    rollBtn: document.getElementById('roll-dice-btn'),
    endTurnBtn: document.getElementById('end-turn-btn'),
    diceResult: document.getElementById('dice-result'),
    diceValue: document.getElementById('dice-value'),
    resourceDisplay: document.getElementById('resource-display'),
    buildBtns: document.querySelectorAll('.btn.build')
};

// --- Lobby Logic ---

lobby.createBtn.addEventListener('click', () => {
    const username = lobby.usernameInput.value;
    if (!username) return alert('Please enter a username');
    playerId = username;
    socket.emit('create_game', { username });
});

lobby.joinBtn.addEventListener('click', () => {
    const username = lobby.usernameInput.value;
    const room = lobby.roomIdInput.value;
    if (!username || !room) return alert('Please enter username and room ID');
    playerId = username;
    roomId = room;
    socket.emit('join_game', { username, room_id: room });
});

lobby.startBtn.addEventListener('click', () => {
    socket.emit('start_game');
});

socket.on('game_created', (data) => {
    roomId = data.room_id;
    isHost = true;
    showLobbyStatus(data.players);
});

socket.on('player_joined', (data) => {
    showLobbyStatus(data.players);
});

socket.on('error', (data) => {
    alert(data.message);
});

function showLobbyStatus(players) {
    lobby.status.classList.remove('hidden');
    lobby.currentRoomId.textContent = roomId;
    updatePlayerList(players);

    if (isHost) {
        lobby.startBtn.classList.remove('hidden');
        lobby.waitingMsg.classList.add('hidden');
    } else {
        lobby.startBtn.classList.add('hidden');
        lobby.waitingMsg.classList.remove('hidden');
    }
}

function updatePlayerList(players) {
    lobby.playerList.innerHTML = '';
    players.forEach(p => {
        const li = document.createElement('li');
        li.textContent = p;
        lobby.playerList.appendChild(li);
    });
}

// --- Game Logic ---

socket.on('game_started', (state) => {
    views.lobby.classList.remove('active');
    views.lobby.classList.add('hidden');
    views.game.classList.remove('hidden');
    views.game.classList.add('active');

    gameState = state;
    initBoard();
    updateUI();
});

socket.on('game_state_update', (state) => {
    gameState = state;
    updateUI();
});

socket.on('dice_rolled', (data) => {
    gameUI.diceResult.classList.remove('hidden');
    gameUI.diceValue.textContent = data.roll;
    setTimeout(() => gameUI.diceResult.classList.add('hidden'), 3000);
});

gameUI.rollBtn.addEventListener('click', () => {
    socket.emit('roll_dice');
});

gameUI.endTurnBtn.addEventListener('click', () => {
    socket.emit('end_turn');
});

gameUI.buildBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        alert('Click on the board to build ' + btn.dataset.type);
        currentBuildMode = btn.dataset.type;
    });
});

let currentBuildMode = null;

// --- Rendering ---

const hexSize = 60;
// Coordinates for hex centers (Standard Catan Layout)
const tileCoords = [
    { x: 300, y: 200 }, { x: 400, y: 200 }, { x: 500, y: 200 },
    { x: 250, y: 286 }, { x: 350, y: 286 }, { x: 450, y: 286 }, { x: 550, y: 286 },
    { x: 200, y: 372 }, { x: 300, y: 372 }, { x: 400, y: 372 }, { x: 500, y: 372 }, { x: 600, y: 372 },
    { x: 250, y: 458 }, { x: 350, y: 458 }, { x: 450, y: 458 }, { x: 550, y: 458 },
    { x: 300, y: 544 }, { x: 400, y: 544 }, { x: 500, y: 544 }
];

function initBoard() {
    gameUI.board.innerHTML = ''; // Clear previous board

    // Create SVG
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("viewBox", "0 0 800 800");
    gameUI.board.appendChild(svg);

    // Define Patterns
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const resources = ['brick', 'wood', 'wool', 'grain', 'ore', 'desert'];
    resources.forEach(res => {
        const pattern = document.createElementNS("http://www.w3.org/2000/svg", "pattern");
        pattern.setAttribute("id", `pattern-${res}`);
        pattern.setAttribute("patternUnits", "objectBoundingBox");
        pattern.setAttribute("width", "1");
        pattern.setAttribute("height", "1");

        const image = document.createElementNS("http://www.w3.org/2000/svg", "image");
        image.setAttributeNS("http://www.w3.org/1999/xlink", "href", `/static/assets/${res}.png`);
        image.setAttribute("width", "120");
        image.setAttribute("height", "120");
        image.setAttribute("preserveAspectRatio", "xMidYMid slice");
        image.setAttribute("x", "0");
        image.setAttribute("y", "0");

        pattern.appendChild(image);
        defs.appendChild(pattern);
    });
    svg.appendChild(defs);

    renderTiles(svg);
    renderEdges(svg);
    renderVertices(svg);
}

function renderTiles(svg) {
    gameState.board.tiles.forEach((tile, index) => {
        if (index >= tileCoords.length) return;
        const { x, y } = tileCoords[index];

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

        // Hexagon
        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        const points = calculateHexPoints(x, y, hexSize);
        polygon.setAttribute("points", points);
        polygon.setAttribute("class", "hex");

        const resourceMap = {
            'BRICK': 'brick',
            'LUMBER': 'wood',
            'WOOL': 'wool',
            'GRAIN': 'grain',
            'ORE': 'ore',
            'DESERT': 'desert'
        };
        const patternId = `pattern-${resourceMap[tile.resource] || 'desert'}`;
        polygon.setAttribute("fill", `url(#${patternId})`);

        g.appendChild(polygon);

        // Number Token
        if (tile.number !== 0) {
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", x);
            circle.setAttribute("cy", y);
            circle.setAttribute("r", 15);
            circle.setAttribute("fill", "rgba(255, 255, 255, 0.8)");
            g.appendChild(circle);

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", x);
            text.setAttribute("y", y + 5);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("fill", "black");
            text.setAttribute("font-weight", "bold");
            text.textContent = tile.number;
            g.appendChild(text);
        }

        svg.appendChild(g);
    });
}

function calculateHexPoints(cx, cy, size) {
    let points = [];
    for (let i = 0; i < 6; i++) {
        const angle_deg = 60 * i - 30;
        const angle_rad = Math.PI / 180 * angle_deg;
        const x = cx + size * Math.cos(angle_rad);
        const y = cy + size * Math.sin(angle_rad);
        points.push(`${x},${y}`);
    }
    return points.join(" ");
}

// Vertex map: vertex_id -> {x, y}
const vertexMap = {};

function calculateVertexCoords() {
    const tileToVerts = gameState.board.tile_to_vertices;

    Object.keys(tileToVerts).forEach(tileIndex => {
        const tIdx = parseInt(tileIndex);
        if (tIdx >= tileCoords.length) return;

        const { x, y } = tileCoords[tIdx];
        const vertIds = tileToVerts[tileIndex];

        for (let i = 0; i < 6; i++) {
            const angle_deg = 60 * i - 30;
            const angle_rad = Math.PI / 180 * angle_deg;
            const vx = x + hexSize * Math.cos(angle_rad);
            const vy = y + hexSize * Math.sin(angle_rad);

            const vId = vertIds[i];
            vertexMap[vId] = { x: vx, y: vy };
        }
    });
}

function renderVertices(svg) {
    calculateVertexCoords();

    Object.keys(vertexMap).forEach(vId => {
        const { x, y } = vertexMap[vId];

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", 6);
        circle.setAttribute("class", "vertex");
        circle.dataset.id = vId;

        const owner = getVertexOwner(vId);
        if (owner) {
            circle.setAttribute("fill", owner.color);
            circle.setAttribute("r", owner.type === 'city' ? 10 : 8);
            circle.setAttribute("stroke", "white");
            circle.setAttribute("stroke-width", 2);
        }

        circle.addEventListener('click', () => handleVertexClick(vId));
        svg.appendChild(circle);
    });
}

function getVertexOwner(vId) {
    vId = parseInt(vId);
    for (const name in gameState.players) {
        const p = gameState.players[name];
        if (p.settlements.includes(vId)) return { color: p.color, type: 'settlement' };
        if (p.cities.includes(vId)) return { color: p.color, type: 'city' };
    }
    return null;
}

function renderEdges(svg) {
    Object.values(gameState.players).forEach(p => {
        p.roads.forEach(road => {
            const v1 = road[0];
            const v2 = road[1];

            if (vertexMap[v1] && vertexMap[v2]) {
                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", vertexMap[v1].x);
                line.setAttribute("y1", vertexMap[v1].y);
                line.setAttribute("x2", vertexMap[v2].x);
                line.setAttribute("y2", vertexMap[v2].y);
                line.setAttribute("stroke", p.color);
                line.setAttribute("stroke-width", 6);
                svg.appendChild(line);
            }
        });
    });
}

function handleVertexClick(vId) {
    if (currentBuildMode === 'settlement') {
        socket.emit('build_settlement', { location: parseInt(vId) });
        currentBuildMode = null;
    } else if (currentBuildMode === 'city') {
        socket.emit('build_city', { location: parseInt(vId) });
        currentBuildMode = null;
    } else if (currentBuildMode === 'road') {
        alert("Road building via UI not fully implemented yet. Use console or hardcoded for now.");
    }
}

function updateUI() {
    gameUI.playersContainer.innerHTML = '';
    Object.values(gameState.players).forEach(p => {
        const div = document.createElement('div');
        div.className = `player-card ${p.name === gameState.currentPlayer ? 'active' : ''}`;
        div.style.borderLeft = `5px solid ${p.color}`;
        div.innerHTML = `
            <strong>${p.name}</strong><br>
            VP: ${p.victory_points} | Cards: ${sumResources(p.resources)} | Knights: ${p.knights}
        `;
        gameUI.playersContainer.appendChild(div);
    });

    gameUI.logContainer.innerHTML = '';
    gameState.log.slice().reverse().forEach(entry => {
        const div = document.createElement('div');
        div.textContent = entry;
        gameUI.logContainer.appendChild(div);
    });

    gameUI.turnIndicator.textContent = gameState.currentPlayer;

    const myPlayer = gameState.players[playerId];
    if (myPlayer) {
        gameUI.resourceDisplay.innerHTML = '';
        Object.entries(myPlayer.resources).forEach(([res, count]) => {
            const div = document.createElement('div');
            div.className = 'resource-item';
            div.innerHTML = `<span>${res}</span><span>${count}</span>`;
            gameUI.resourceDisplay.appendChild(div);
        });
    }

    // Re-render board
    initBoard();
}

function sumResources(res) {
    return Object.values(res).reduce((a, b) => a + b, 0);
}
