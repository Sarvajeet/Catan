import sys
import os
import uuid
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from catan.src.game import Game
from catan.src.components import Resource

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active games: {room_id: Game}
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_game')
def on_create_game(data):
    username = data['username']
    room_id = str(uuid.uuid4())[:8]
    session['username'] = username
    session['room_id'] = room_id
    
    # Initialize game with the host
    # We'll add more players as they join
    games[room_id] = {
        'game': None, # Game instance will be created when started
        'players': [username],
        'host': username,
        'started': False
    }
    
    join_room(room_id)
    emit('game_created', {'room_id': room_id, 'players': games[room_id]['players']})

@socketio.on('join_game')
def on_join_game(data):
    username = data['username']
    room_id = data['room_id']
    
    if room_id not in games:
        emit('error', {'message': 'Room not found'})
        return
        
    if games[room_id]['started']:
        emit('error', {'message': 'Game already started'})
        return
        
    if len(games[room_id]['players']) >= 4:
        emit('error', {'message': 'Room is full'})
        return
        
    if username in games[room_id]['players']:
        emit('error', {'message': 'Username already taken'})
        return

    session['username'] = username
    session['room_id'] = room_id
    
    games[room_id]['players'].append(username)
    join_room(room_id)
    
    emit('player_joined', {'players': games[room_id]['players']}, room=room_id)

@socketio.on('start_game')
def on_start_game():
    room_id = session.get('room_id')
    username = session.get('username')
    
    if not room_id or room_id not in games:
        return
        
    if games[room_id]['host'] != username:
        return
        
    player_names = games[room_id]['players']
    if len(player_names) < 2: # Minimum 2 players for testing, usually 3-4
         emit('error', {'message': 'Need at least 2 players to start'})
         return

    # Create the game instance
    game_instance = Game(player_names)
    
    # Setup initial placements (Random/Predefined for now to simplify start)
    # In a real game, we'd have a setup phase. For this MVP, we'll auto-setup.
    # We need to generate valid initial placements for N players.
    # This is a bit complex to do dynamically perfectly, so we'll use a simple strategy
    # or just let the game start and have players place them (if game logic supports it).
    # Looking at game.py, start_game takes initial_placements.
    # Let's generate some valid dummy placements to get things moving.
    
    # Simplified: Just picking some non-overlapping spots.
    # This is a hack for the MVP.
    placements = []
    # Hardcoded spots for up to 4 players
    possible_spots = [
        {"settlement": 8, "road": (8, 9)}, 
        {"settlement": 14, "road": (14, 13)}, 
        {"settlement": 40, "road": (40, 41)},
        {"settlement": 45, "road": (45, 46)}, 
        {"settlement": 33, "road": (33, 32)}, 
        {"settlement": 22, "road": (22, 21)},
        {"settlement": 10, "road": (10, 11)},
        {"settlement": 20, "road": (20, 19)}
    ]
    
    for i in range(len(player_names) * 2): # 2 placements per player
        if i < len(possible_spots):
            placements.append(possible_spots[i])
        else:
             # Fallback if we run out of hardcoded spots (shouldn't happen for 4 players)
             placements.append({"settlement": 0, "road": (0, 1)}) 

    game_instance.start_game(placements[:len(player_names)*2])
    
    games[room_id]['game'] = game_instance
    games[room_id]['started'] = True
    
    emit('game_started', game_instance.to_dict(), room=room_id)

@socketio.on('get_game_state')
def on_get_game_state():
    room_id = session.get('room_id')
    if room_id and room_id in games and games[room_id]['started']:
        emit('game_state_update', games[room_id]['game'].to_dict())

@socketio.on('roll_dice')
def on_roll_dice():
    room_id = session.get('room_id')
    username = session.get('username')
    
    if not room_id or room_id not in games or not games[room_id]['started']:
        return

    game = games[room_id]['game']
    if game.current_player.name != username:
        emit('error', {'message': 'Not your turn'})
        return
        
    roll = game.roll_dice()
    emit('dice_rolled', {'roll': roll, 'log': game.log[-1]}, room=room_id)
    emit('game_state_update', game.to_dict(), room=room_id)

@socketio.on('build_road')
def on_build_road(data):
    room_id = session.get('room_id')
    username = session.get('username')
    game = games[room_id]['game']
    
    if game.current_player.name != username:
        return

    location = tuple(data['location'])
    if game.build_road(game.current_player, location):
        emit('game_state_update', game.to_dict(), room=room_id)
    else:
        emit('error', {'message': 'Cannot build road there'})

@socketio.on('build_settlement')
def on_build_settlement(data):
    room_id = session.get('room_id')
    username = session.get('username')
    game = games[room_id]['game']
    
    if game.current_player.name != username:
        return

    location = data['location']
    if game.build_settlement(game.current_player, location):
        emit('game_state_update', game.to_dict(), room=room_id)
    else:
        emit('error', {'message': 'Cannot build settlement there'})

@socketio.on('end_turn')
def on_end_turn():
    room_id = session.get('room_id')
    username = session.get('username')
    game = games[room_id]['game']
    
    if game.current_player.name != username:
        return
        
    game.next_turn()
    emit('game_state_update', game.to_dict(), room=room_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)