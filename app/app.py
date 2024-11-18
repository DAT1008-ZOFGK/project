from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from prometheus_flask_exporter import PrometheusMetrics
from models import db, User, Song
from auth import authenticate, jwt
import logging
from logging.config import dictConfig
import os

# Logging configuration
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@postgres:5432/musicdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

# Initialize extensions
db.init_app(app)
jwt.init_app(app)
metrics = PrometheusMetrics(app)

# Metrics
metrics.info('music_app_info', 'Music app info', version='1.0.0')
songs_total = metrics.counter('songs_total', 'Total number of songs')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400
    
    user = User(
        username=data['username'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    app.logger.info(f"New user registered: {user.username}")
    return jsonify({"msg": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        app.logger.info(f"User logged in: {user.username}")
        return jsonify({"token": access_token}), 200
    
    return jsonify({"msg": "Invalid credentials"}), 401

@app.route('/songs', methods=['GET'])
@authenticate()
def get_songs():
    songs = Song.query.all()
    return jsonify([{
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "duration": song.duration
    } for song in songs])

@app.route('/songs', methods=['POST'])
@authenticate()
def add_song():
    data = request.get_json()
    song = Song(
        title=data['title'],
        artist=data['artist'],
        album=data.get('album'),
        duration=data.get('duration'),
        user_id=data.get('user_id')
    )
    db.session.add(song)
    db.session.commit()
    songs_total.inc()
    app.logger.info(f"New song added: {song.title}")
    return jsonify({"msg": "Song added successfully"}), 201