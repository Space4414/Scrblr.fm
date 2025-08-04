from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
import json

# User table for authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # Last.fm credentials
    lastfm_username = db.Column(db.String, nullable=True)
    lastfm_session_key = db.Column(db.String, nullable=True)
    
    # User preferences
    default_interval = db.Column(db.Integer, default=3)  # minutes
    is_scrobbling_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    playlists = db.relationship('Playlist', backref='user', lazy=True, cascade='all, delete-orphan')
    scrobble_sessions = db.relationship('ScrobbleSession', backref='user', lazy=True, cascade='all, delete-orphan')

# OAuth table for Replit Auth
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)
    
    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Playlist table for storing user playlists
class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_type = db.Column(db.String(50), nullable=False)  # 'custom', 'spotify', 'deezer', 'lastfm'
    source_id = db.Column(db.String(500), nullable=True)  # External playlist ID
    tracks_data = db.Column(db.Text, nullable=False)  # JSON string of tracks
    is_public = db.Column(db.Boolean, default=False)
    total_tracks = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def get_tracks(self):
        """Return tracks as list of dictionaries"""
        try:
            return json.loads(self.tracks_data)
        except:
            return []
    
    def set_tracks(self, tracks):
        """Set tracks from list of dictionaries"""
        self.tracks_data = json.dumps(tracks)
        self.total_tracks = len(tracks)

# Scrobble session for tracking active scrobbling
class ScrobbleSession(db.Model):
    __tablename__ = 'scrobble_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=True)
    
    is_active = db.Column(db.Boolean, default=False)
    interval_minutes = db.Column(db.Integer, default=3)
    shuffle_enabled = db.Column(db.Boolean, default=True)
    current_track_index = db.Column(db.Integer, default=0)
    total_scrobbles = db.Column(db.Integer, default=0)
    
    started_at = db.Column(db.DateTime, nullable=True)
    last_scrobble_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# Track history for analytics and preventing duplicates
class ScrobbleHistory(db.Model):
    __tablename__ = 'scrobble_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    artist = db.Column(db.String(200), nullable=False)
    track = db.Column(db.String(200), nullable=False)
    album = db.Column(db.String(200), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    
    scrobbled_at = db.Column(db.DateTime, default=datetime.now)
    source_type = db.Column(db.String(50), nullable=True)  # 'manual', 'auto', 'import'
    
    # External service IDs
    spotify_id = db.Column(db.String(100), nullable=True)
    deezer_id = db.Column(db.String(100), nullable=True)
    lastfm_mbid = db.Column(db.String(100), nullable=True)

# Public playlists for community sharing
class CommunityPlaylist(db.Model):
    __tablename__ = 'community_playlists'
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # 'trending', 'featured', 'genre'
    featured_by_admin = db.Column(db.Boolean, default=False)
    likes_count = db.Column(db.Integer, default=0)
    uses_count = db.Column(db.Integer, default=0)
    
    playlist = db.relationship('Playlist', backref='community_entry')
    
    created_at = db.Column(db.DateTime, default=datetime.now)

# User statistics
class UserStats(db.Model):
    __tablename__ = 'user_stats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    total_scrobbles = db.Column(db.Integer, default=0)
    total_playlists = db.Column(db.Integer, default=0)
    total_listening_time = db.Column(db.Integer, default=0)  # in minutes
    
    last_scrobble_date = db.Column(db.Date, nullable=True)
    streak_days = db.Column(db.Integer, default=0)
    
    top_artist = db.Column(db.String(200), nullable=True)
    top_track = db.Column(db.String(200), nullable=True)
    top_album = db.Column(db.String(200), nullable=True)
    
    user = db.relationship('User', backref='stats')
    
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)