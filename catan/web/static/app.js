document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const gameBoard = document.getElementById('game-board');
    const rollDiceBtn = document.getElementById('roll-dice-btn');
    const buildRoadBtn = document.getElementById('build-road-btn');
    const buildSettlementBtn = document.getElementById('build-settlement-btn');
    const buildCityBtn = document.getElementById('build-city-btn');
    const tradeBtn = document.getElementById('trade-btn');
    const statusMessages = document.getElementById('status-messages');
    const tradeModal = document.getElementById('trade-modal');
    const closeBtn = document.querySelector('.close-btn');
    const tradeForm = document.getElementById('trade-form');
    const gameLog = document.getElementById('game-log');

    // --- Game State ---
    let currentPlayers = [];
    let currentPlayerName = '';
    let buildMode = null; // null, 'settlement', 'city', 'road'
    let roadBuildingVertices = [];
    const resourceTypes = ['LUMBER', 'BRICK', 'WOOL', 'GRAIN', 'ORE'];
    let vertexCoords = {};

    // --- Initial Setup ---
    fetchGameState();

    // --- Event Listeners ---
    rollDiceBtn.addEventListener('click', () => {
        fetch('/roll_dice', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                updateStatus(`You rolled a ${data.roll}`);
                fetchGameState();
            });
    });

    buildRoadBtn.addEventListener('click', () => {
        buildMode = 'road';
        roadBuildingVertices = [];
        updateStatus('Select the first vertex for your road.');
    });

    buildSettlementBtn.addEventListener('click', () => {
        buildMode = 'settlement';
        updateStatus('Select a vertex to build a settlement.');
    });

    buildCityBtn.addEventListener('click', () => {
        buildMode = 'city';
        updateStatus('Select a settlement to upgrade to a city.');
    });

    tradeBtn.addEventListener('click', () => openTradeModal());
    closeBtn.addEventListener('click', () => tradeModal.style.display = 'none');
    window.addEventListener('click', (event) => {
        if (event.target == tradeModal) {
            tradeModal.style.display = 'none';
        }
    });
    tradeForm.addEventListener('submit', handleTradeSubmit);

    // --- Core Functions ---
    function fetchGameState() {
        fetch('/game_state')
            .then(response => response.json())
            .then(data => {
                console.log('Game state:', data);
                currentPlayers = Object.keys(data.players);
                currentPlayerName = data.currentPlayer;
                renderBoard(data.board, data.players);
                renderPlayers(data.players);
                renderLog(data.log);
            });
    }

    function updateStatus(message, isError = false) {
        statusMessages.textContent = message;
        statusMessages.style.color = isError ? 'red' : 'black';
    }

    function sendBuildRequest(url, body) {
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatus('Build successful!');
                fetchGameState();
            } else {
                updateStatus('Build failed. Check resources or placement rules.', true);
            }
        });
    }

    function onVertexClick(vertexId) {
        if (!buildMode) return;

        if (buildMode === 'settlement' || buildMode === 'city') {
            sendBuildRequest(`/build/${buildMode}`, { location: parseInt(vertexId) });
        } else if (buildMode === 'road') {
            roadBuildingVertices.push(parseInt(vertexId));
            const vertexDiv = document.querySelector(`.vertex[data-id='${vertexId}']`);
            if(vertexDiv) vertexDiv.style.backgroundColor = 'gold';

            if (roadBuildingVertices.length === 1) {
                updateStatus('Select the second vertex for your road.');
            } else if (roadBuildingVertices.length === 2) {
                sendBuildRequest('/build/road', { location: roadBuildingVertices });
                roadBuildingVertices = [];
            }
        }

        if (buildMode !== 'road' || roadBuildingVertices.length === 0) {
             updateStatus(`Exited ${buildMode} mode.`);
             buildMode = null;
        }
    }

    // --- Rendering ---
    function renderBoard(board, players) {
        gameBoard.innerHTML = '';
        const hexWidth = 100;
        const hexHeight = 115.47;
        const horizSpacing = hexWidth * 0.75;
        const vertSpacing = hexHeight;

        const tileCoordinates = [
            [2, 0], [3, 0], [4, 0],
            [1.5, 1], [2.5, 1], [3.5, 1], [4.5, 1],
            [1, 2], [2, 2], [3, 2], [4, 2], [5, 2],
            [1.5, 3], [2.5, 3], [3.5, 3], [4.5, 3],
            [2, 4], [3, 4], [4, 4]
        ];

        vertexCoords = {};

        board.tiles.forEach((tile, i) => {
            const [col, row] = tileCoordinates[i];
            const x = col * horizSpacing;
            const y = row * (vertSpacing / 2);

            const hex = document.createElement('div');
            hex.classList.add('hex', tile.resource);
            hex.style.left = `${x}px`;
            hex.style.top = `${y}px`;

            const resourceDiv = document.createElement('div');
            resourceDiv.classList.add('resource');
            resourceDiv.textContent = tile.resource;
            hex.appendChild(resourceDiv);

            if (tile.number !== 7) {
                const numberDiv = document.createElement('div');
                numberDiv.classList.add('number');
                numberDiv.textContent = tile.number;
                hex.appendChild(numberDiv);
            }
            gameBoard.appendChild(hex);

            const hexVertexPositions = [
                { x: x + hexWidth / 2, y: y },
                { x: x + hexWidth, y: y + hexHeight * 0.25 },
                { x: x + hexWidth, y: y + hexHeight * 0.75 },
                { x: x + hexWidth / 2, y: y + hexHeight },
                { x: x, y: y + hexHeight * 0.75 },
                { x: x, y: y + hexHeight * 0.25 },
            ];
            const tileVertexIds = board.tile_to_vertices[i];
            if (tileVertexIds) {
                hexVertexPositions.forEach((pos, j) => {
                    const vertexId = tileVertexIds[j];
                    if (!vertexCoords[vertexId]) vertexCoords[vertexId] = pos;
                });
            }
        });

        // Render Vertices (for clicking)
        for (const vertexId in vertexCoords) {
            const pos = vertexCoords[vertexId];
            const vertexDiv = document.createElement('div');
            vertexDiv.classList.add('vertex');
            vertexDiv.style.left = `${pos.x}px`;
            vertexDiv.style.top = `${pos.y}px`;
            vertexDiv.dataset.id = vertexId;
            vertexDiv.title = `Vertex ${vertexId}`;
            vertexDiv.addEventListener('click', () => onVertexClick(vertexId));
            gameBoard.appendChild(vertexDiv);
        }

        // Render Player Pieces
        for (const playerName in players) {
            const player = players[playerName];

            player.settlements.forEach(vertexId => {
                const vertexDiv = document.querySelector(`.vertex[data-id='${vertexId}']`);
                if(vertexDiv) vertexDiv.classList.add('settlement', player.color);
            });

            player.cities.forEach(vertexId => {
                const vertexDiv = document.querySelector(`.vertex[data-id='${vertexId}']`);
                if(vertexDiv) vertexDiv.classList.add('city', player.color);
            });

            player.roads.forEach(road => {
                const [v1, v2] = road;
                const pos1 = vertexCoords[v1];
                const pos2 = vertexCoords[v2];
                if (pos1 && pos2) {
                    const roadSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    roadSvg.classList.add('road');
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', pos1.x);
                    line.setAttribute('y1', pos1.y);
                    line.setAttribute('x2', pos2.x);
                    line.setAttribute('y2', pos2.y);
                    line.classList.add('road', player.color);
                    roadSvg.appendChild(line);
                    gameBoard.appendChild(roadSvg);
                }
            });
        }
    }

    function renderPlayers(players) {
        const playersContainer = document.getElementById('players-container');
        playersContainer.innerHTML = '';
        for (const playerName in players) {
            const player = players[playerName];
            const playerDiv = document.createElement('div');
            playerDiv.classList.add('player-info');
            const nameHeader = document.createElement('h3');
            nameHeader.textContent = `${playerName} (${player.color})`;
            playerDiv.appendChild(nameHeader);
            const resourcesList = document.createElement('ul');
            resourcesList.classList.add('resources');
            for (const resourceName in player.resources) {
                const resourceItem = document.createElement('li');
                resourceItem.textContent = `${resourceName}: ${player.resources[resourceName]}`;
                resourcesList.appendChild(resourceItem);
            }
            playerDiv.appendChild(resourcesList);
            playersContainer.appendChild(playerDiv);
        }
    }

    function renderLog(logMessages) {
        gameLog.innerHTML = '';
        logMessages.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = msg;
            gameLog.appendChild(li);
        });
        // Auto-scroll to the bottom
        gameLog.parentElement.scrollTop = gameLog.parentElement.scrollHeight;
    }

    // --- Trade Modal Logic ---
    function openTradeModal() {
        const tradePartnerSelect = document.getElementById('trade-partner');
        tradePartnerSelect.innerHTML = '';
        currentPlayers.filter(p => p !== currentPlayerName).forEach(pName => {
            const option = document.createElement('option');
            option.value = pName;
            option.textContent = pName;
            tradePartnerSelect.appendChild(option);
        });

        const offerResourcesDiv = document.getElementById('offer-resources');
        const requestResourcesDiv = document.getElementById('request-resources');
        offerResourcesDiv.innerHTML = '<h3>You Offer:</h3>';
        requestResourcesDiv.innerHTML = '<h3>You Request:</h3>';

        resourceTypes.forEach(resource => {
            const offerInput = document.createElement('input');
            offerInput.type = 'number';
            offerInput.name = `offer-${resource}`;
            offerInput.min = 0;
            offerInput.value = 0;
            const offerLabel = document.createElement('label');
            offerLabel.textContent = resource;
            offerLabel.appendChild(offerInput);
            offerResourcesDiv.appendChild(offerLabel);

            const requestInput = document.createElement('input');
            requestInput.type = 'number';
            requestInput.name = `request-${resource}`;
            requestInput.min = 0;
            requestInput.value = 0;
            const requestLabel = document.createElement('label');
            requestLabel.textContent = resource;
            requestLabel.appendChild(requestInput);
            requestResourcesDiv.appendChild(requestLabel);
        });
        tradeModal.style.display = 'block';
    }

    function handleTradeSubmit(event) {
        event.preventDefault();
        const formData = new FormData(tradeForm);
        const receiving_player = formData.get('trade-partner');
        const offered_resources = {};
        const requested_resources = {};

        resourceTypes.forEach(resource => {
            const offerAmount = parseInt(formData.get(`offer-${resource}`), 10);
            if (offerAmount > 0) offered_resources[resource] = offerAmount;
            const requestAmount = parseInt(formData.get(`request-${resource}`), 10);
            if (requestAmount > 0) requested_resources[resource] = requestAmount;
        });

        if (Object.keys(offered_resources).length === 0 || Object.keys(requested_resources).length === 0) {
            updateStatus('You must offer and request at least one resource.', true);
            return;
        }

        fetch('/trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiving_player, offered_resources, requested_resources })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatus('Trade successful!');
                fetchGameState();
            } else {
                updateStatus(`Trade failed: ${data.error || 'Check resources.'}`, true);
            }
            tradeModal.style.display = 'none';
        });
    }
});