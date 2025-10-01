import sys
import os
from flask import Flask, render_template, jsonify, request

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from catan.src.game import Game
from catan.src.components import Resource

app = Flask(__name__)

# Initialize the game engine
game = Game(player_names=["Player 1", "Player 2", "Player 3"])
initial_placements = [
    {"settlement": 8, "road": (8, 9)}, {"settlement": 14, "road": (14, 13)}, {"settlement": 40, "road": (40, 41)},
    {"settlement": 45, "road": (45, 46)}, {"settlement": 33, "road": (33, 32)}, {"settlement": 22, "road": (22, 21)},
]
game.start_game(initial_placements)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game_state')
def game_state():
    # This will be expanded to provide a full JSON representation of the game state
    state = {
        'currentPlayer': game.current_player.name,
        'turn': game.turn,
        'players': {
            p.name: {
                'resources': {res.name: count for res, count in p.resources.items()},
                'settlements': p.settlements,
                'cities': p.cities,
                'roads': p.roads,
                'color': p.color
            } for p in game.players
        },
        'board': {
            'tiles': [
                {
                    'resource': tile.resource.name if tile.resource else 'DESERT',
                    'number': tile.number
                } for tile in game.board.tiles
            ],
            'robber_location': game.board.robber_location,
            'tile_to_vertices': game.board.tile_to_vertices,
        },
        'log': game.log
    }
    return jsonify(state)

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    roll = game.roll_dice()
    return jsonify({'roll': roll})

@app.route('/build/road', methods=['POST'])
def build_road():
    data = request.json
    player = game.current_player
    # The location will be a tuple of two vertices, e.g., (0, 1)
    location = tuple(data['location'])
    success = game.build_road(player, location)
    return jsonify({'success': success})

@app.route('/build/settlement', methods=['POST'])
def build_settlement():
    data = request.json
    player = game.current_player
    location = data['location']
    success = game.build_settlement(player, location)
    return jsonify({'success': success})

@app.route('/build/city', methods=['POST'])
def build_city():
    data = request.json
    player = game.current_player
    location = data['location']
    success = game.build_city(player, location)
    return jsonify({'success': success})

@app.route('/trade', methods=['POST'])
def trade():
    data = request.json
    offering_player = game.current_player

    # Find the receiving player object by name
    receiving_player_name = data['receiving_player']
    receiving_player = next((p for p in game.players if p.name == receiving_player_name), None)
    if not receiving_player:
        return jsonify({'success': False, 'error': 'Player not found'})

    # Convert resource names back to enums
    offered_resources = {Resource[k]: v for k, v in data['offered_resources'].items()}
    requested_resources = {Resource[k]: v for k, v in data['requested_resources'].items()}

    success = game.trade(offering_player, receiving_player, offered_resources, requested_resources)
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)