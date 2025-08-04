import os
import requests
import hashlib
import time
import json
import threading
from datetime import datetime, timedelta
from app import db
from models import User, Playlist, ScrobbleSession, ScrobbleHistory, UserStats
import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
try:
    import deezer
except ImportError:
    deezer = None

class UniversalScrobbler:
    def __init__(self):
        self.lastfm_api_key = '45905c9b4239a9ec7b245f8a3711e87b'
        self.lastfm_secret = 'afcbf283834eaea726d3176d1ab946d0'
        self.lastfm_api_url = 'https://ws.audioscrobbler.com/2.0/'
        
        # Initialize Spotify
        self.spotify_client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        self.spotify = None
        if self.spotify_client_id and self.spotify_client_secret:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=self.spotify_client_id,
                    client_secret=self.spotify_client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            except Exception as e:
                logging.error(f"Spotify initialization failed: {e}")
        
        # Initialize Deezer
        self.deezer_client = None
        if deezer:
            try:
                self.deezer_client = deezer.Client()
            except Exception as e:
                logging.error(f"Deezer initialization failed: {e}")
        
        # Active sessions
        self.active_sessions = {}
        self.session_threads = {}
        
        logging.info("Universal Scrobbler initialized")
    
    def generate_api_sig(self, params):
        """Generate API signature for Last.fm"""
        sorted_params = sorted(params.items())
        sig_string = ''.join([f'{k}{v}' for k, v in sorted_params])
        sig_string += self.lastfm_secret
        return hashlib.md5(sig_string.encode('utf-8')).hexdigest()
    
    def authenticate_lastfm(self, username, password):
        """Authenticate user with Last.fm and return session key"""
        params = {
            'method': 'auth.getMobileSession',
            'username': username,
            'password': password,
            'api_key': self.lastfm_api_key
        }
        
        params['api_sig'] = self.generate_api_sig(params)
        params['format'] = 'json'
        
        try:
            response = requests.post(self.lastfm_api_url, data=params)
            data = response.json()
            
            if 'session' in data:
                return data['session']['key']
            else:
                logging.error(f"Last.fm auth failed: {data}")
                return None
                
        except Exception as e:
            logging.error(f"Last.fm authentication error: {e}")
            return None
    
    def scrobble_track(self, user_id, artist, track, album=None, timestamp=None, duration=None):
        """Scrobble a single track for a user"""
        user = User.query.get(user_id)
        if not user or not user.lastfm_session_key:
            return False, "User not authenticated with Last.fm"
        
        if timestamp is None:
            timestamp = int(time.time())
        
        params = {
            'method': 'track.scrobble',
            'artist': artist,
            'track': track,
            'timestamp': str(timestamp),
            'api_key': self.lastfm_api_key,
            'sk': user.lastfm_session_key
        }
        
        if album:
            params['album'] = album
        if duration:
            params['duration'] = str(duration)
        
        params['api_sig'] = self.generate_api_sig(params)
        params['format'] = 'json'
        
        try:
            response = requests.post(self.lastfm_api_url, data=params)
            data = response.json()
            
            if 'scrobbles' in data:
                # Save to history
                history = ScrobbleHistory(
                    user_id=user_id,
                    artist=artist,
                    track=track,
                    album=album,
                    duration=duration,
                    scrobbled_at=datetime.fromtimestamp(timestamp),
                    source_type='auto'
                )
                db.session.add(history)
                
                # Update user stats
                self.update_user_stats(user_id, artist, track, album)
                
                db.session.commit()
                logging.info(f"Scrobbled: {artist} - {track} for user {user_id}")
                return True, f"Scrobbled: {artist} - {track}"
            else:
                error_msg = data.get('message', 'Unknown error')
                logging.error(f"Scrobble failed: {error_msg}")
                return False, f"Scrobble failed: {error_msg}"
                
        except Exception as e:
            logging.error(f"Scrobble error: {e}")
            return False, f"Network error: {str(e)}"
    
    def update_user_stats(self, user_id, artist, track, album=None):
        """Update user statistics"""
        stats = UserStats.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = UserStats(user_id=user_id)
            db.session.add(stats)
        
        stats.total_scrobbles += 1
        stats.last_scrobble_date = datetime.now().date()
        stats.top_artist = artist  # Simplified - could be more sophisticated
        stats.top_track = track
        if album:
            stats.top_album = album
        
        db.session.commit()
    
    def get_spotify_playlist(self, playlist_id):
        """Get tracks from Spotify playlist"""
        if not self.spotify:
            return None, "Spotify not configured"
        
        try:
            playlist = self.spotify.playlist(playlist_id)
            tracks = []
            
            for item in playlist['tracks']['items']:
                if item['track']:
                    track_data = {
                        'artist': item['track']['artists'][0]['name'],
                        'track': item['track']['name'],
                        'album': item['track']['album']['name'],
                        'duration': item['track']['duration_ms'] // 1000,
                        'spotify_id': item['track']['id']
                    }
                    tracks.append(track_data)
            
            return tracks, None
            
        except Exception as e:
            logging.error(f"Spotify playlist error: {e}")
            return None, str(e)
    
    def get_deezer_playlist(self, playlist_id):
        """Get tracks from Deezer playlist"""
        if not self.deezer_client:
            return None, "Deezer not available"
            
        try:
            playlist = self.deezer_client.get_playlist(playlist_id)
            tracks = []
            
            for track in playlist.tracks:
                track_data = {
                    'artist': track.artist.name,
                    'track': track.title,
                    'album': track.album.title,
                    'duration': track.duration,
                    'deezer_id': str(track.id)
                }
                tracks.append(track_data)
            
            return tracks, None
            
        except Exception as e:
            logging.error(f"Deezer playlist error: {e}")
            return None, str(e)
    
    def search_spotify(self, query, type='track', limit=20):
        """Search Spotify for tracks, albums, or playlists"""
        if not self.spotify:
            return None, "Spotify not configured"
        
        try:
            results = self.spotify.search(q=query, type=type, limit=limit)
            return results, None
        except Exception as e:
            return None, str(e)
    
    def search_deezer(self, query, type='track', limit=20):
        """Search Deezer for tracks, albums, or playlists"""
        if not self.deezer_client:
            return None, "Deezer not available"
            
        try:
            if type == 'track':
                results = self.deezer_client.search(query, limit=limit)
            elif type == 'album':
                results = self.deezer_client.search_album(query, limit=limit)
            elif type == 'playlist':
                results = self.deezer_client.search_playlist(query, limit=limit)
            else:
                results = self.deezer_client.search(query, limit=limit)
            
            return results, None
        except Exception as e:
            return None, str(e)
    
    def start_auto_scrobbling(self, user_id, playlist_id, interval_minutes=3, shuffle=True):
        """Start automatic scrobbling session"""
        session_key = f"{user_id}_{playlist_id}"
        
        # Stop existing session if running
        self.stop_auto_scrobbling(user_id)
        
        # Create new session
        session = ScrobbleSession(
            user_id=user_id,
            playlist_id=playlist_id,
            is_active=True,
            interval_minutes=interval_minutes,
            shuffle_enabled=shuffle,
            started_at=datetime.now()
        )
        db.session.add(session)
        db.session.commit()
        
        # Start scrobbling thread
        thread = threading.Thread(
            target=self._scrobbling_worker,
            args=(session.id, user_id, playlist_id, interval_minutes, shuffle),
            daemon=True
        )
        thread.start()
        
        self.active_sessions[user_id] = session.id
        self.session_threads[user_id] = thread
        
        logging.info(f"Started auto scrobbling for user {user_id}")
        return True, "Auto scrobbling started"
    
    def stop_auto_scrobbling(self, user_id):
        """Stop automatic scrobbling session"""
        if user_id in self.active_sessions:
            session_id = self.active_sessions[user_id]
            session = ScrobbleSession.query.get(session_id)
            if session:
                session.is_active = False
                db.session.commit()
            
            del self.active_sessions[user_id]
            if user_id in self.session_threads:
                del self.session_threads[user_id]
            
            logging.info(f"Stopped auto scrobbling for user {user_id}")
            return True, "Auto scrobbling stopped"
        
        return False, "No active session found"
    
    def _scrobbling_worker(self, session_id, user_id, playlist_id, interval_minutes, shuffle):
        """Worker thread for automatic scrobbling"""
        import random
        
        while True:
            session = ScrobbleSession.query.get(session_id)
            if not session or not session.is_active:
                break
            
            playlist = Playlist.query.get(playlist_id)
            if not playlist:
                break
            
            tracks = playlist.get_tracks()
            if not tracks:
                break
            
            # Select track
            if shuffle:
                track = random.choice(tracks)
            else:
                track = tracks[session.current_track_index % len(tracks)]
                session.current_track_index += 1
            
            # Scrobble track
            success, message = self.scrobble_track(
                user_id,
                track['artist'],
                track['track'],
                track.get('album'),
                duration=track.get('duration')
            )
            
            if success:
                session.total_scrobbles += 1
                session.last_scrobble_at = datetime.now()
                db.session.commit()
            
            # Wait for next scrobble
            time.sleep(interval_minutes * 60)
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        stats = UserStats.query.filter_by(user_id=user_id).first()
        if not stats:
            return {
                'total_scrobbles': 0,
                'total_playlists': 0,
                'streak_days': 0,
                'top_artist': None,
                'top_track': None
            }
        
        return {
            'total_scrobbles': stats.total_scrobbles,
            'total_playlists': stats.total_playlists,
            'streak_days': stats.streak_days,
            'top_artist': stats.top_artist,
            'top_track': stats.top_track,
            'top_album': stats.top_album,
            'last_scrobble': stats.last_scrobble_date
        }
    
    def get_recent_scrobbles(self, user_id, limit=20):
        """Get recent scrobbles for user"""
        history = ScrobbleHistory.query.filter_by(user_id=user_id)\
                                      .order_by(ScrobbleHistory.scrobbled_at.desc())\
                                      .limit(limit).all()
        
        return [{
            'artist': h.artist,
            'track': h.track,
            'album': h.album,
            'scrobbled_at': h.scrobbled_at.isoformat(),
            'source_type': h.source_type
        } for h in history]

# Global scrobbler instance
scrobbler = UniversalScrobbler()