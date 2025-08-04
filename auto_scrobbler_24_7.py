#!/usr/bin/env python3
"""
24/7 Automatic Last.fm Scrobbler
Runs continuously in the background
"""

import hashlib
import requests
import time
import random
import logging
import signal
import sys
import os
from datetime import datetime

# Your Last.fm API credentials
API_KEY = '45905c9b4239a9ec7b245f8a3711e87b'
SHARED_SECRET = 'afcbf283834eaea726d3176d1ab946d0'

# Get credentials from environment variables or prompt
USERNAME = os.getenv('LASTFM_USERNAME') or input("Enter your Last.fm username: ").strip()
PASSWORD = os.getenv('LASTFM_PASSWORD') or input("Enter your Last.fm password: ").strip()

class AutoScrobbler:
    def __init__(self):
        self.session_key = None
        self.running = True
        self.setup_logging()
        self.setup_signal_handlers()
        
        # Music tracks to rotate through
        self.tracks = [
            {'artist': 'The Beatles', 'track': 'Yesterday'},
            {'artist': 'Queen', 'track': 'We Will Rock You'},
            {'artist': 'Pink Floyd', 'track': 'Wish You Were Here'},
            {'artist': 'Led Zeppelin', 'track': 'Kashmir'},
            {'artist': 'The Rolling Stones', 'track': 'Satisfaction'},
            {'artist': 'David Bowie', 'track': 'Heroes'},
            {'artist': 'Coldplay', 'track': 'Fix You'},
            {'artist': 'Imagine Dragons', 'track': 'Thunder'},
            {'artist': 'Radiohead', 'track': 'Karma Police'},
            {'artist': 'Nirvana', 'track': 'Come As You Are'},
        ]
        
        self.last_scrobbled = {}
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_scrobbler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger()
        
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
    def stop(self, signum=None, frame=None):
        self.logger.info("Stopping scrobbler...")
        self.running = False
        
    def generate_api_sig(self, params):
        string = ''.join([f"{k}{params[k]}" for k in sorted(params)])
        string += SHARED_SECRET
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def authenticate(self):
        self.logger.info("Authenticating with Last.fm...")
        
        params = {
            'method': 'auth.getMobileSession',
            'api_key': API_KEY,
            'username': USERNAME,
            'password': PASSWORD,
        }
        params['api_sig'] = self.generate_api_sig(params)
        params['format'] = 'json'
        
        try:
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params, timeout=30)
            data = response.json()
            
            if 'session' in data:
                self.session_key = data['session']['key']
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error(f"Authentication failed: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    def scrobble_track(self, artist, track):
        if not self.session_key:
            return False
            
        timestamp = int(time.time())
        
        params = {
            'method': 'track.scrobble',
            'api_key': API_KEY,
            'artist': artist,
            'track': track,
            'timestamp': str(timestamp),
            'sk': self.session_key,
            'format': 'json'
        }
        params['api_sig'] = self.generate_api_sig(params)
        
        try:
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params, timeout=30)
            data = response.json()
            
            if 'scrobbles' in data and data['scrobbles'].get('@attr', {}).get('accepted') == '1':
                self.logger.info(f"Scrobbled: {artist} - {track}")
                return True
            else:
                self.logger.warning(f"Scrobble failed: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"Scrobble error: {e}")
            return False

    def get_next_track(self):
        """Get next track, avoiding recent duplicates"""
        available_tracks = []
        current_time = time.time()
        
        for track in self.tracks:
            track_key = f"{track['artist']}|{track['track']}"
            last_time = self.last_scrobbled.get(track_key, 0)
            
            # Only allow if not scrobbled in last 2 hours
            if current_time - last_time > 7200:
                available_tracks.append(track)
        
        if not available_tracks:
            # If all tracks were recent, use the oldest one
            available_tracks = [self.tracks[0]]
        
        selected = random.choice(available_tracks)
        track_key = f"{selected['artist']}|{selected['track']}"
        self.last_scrobbled[track_key] = current_time
        
        return selected

    def run(self):
        if not self.authenticate():
            self.logger.error("Failed to authenticate, exiting")
            return
            
        self.logger.info("Starting 24/7 scrobbling (every 3 minutes)")
        self.logger.info("Press Ctrl+C to stop")
        
        scrobble_count = 0
        
        while self.running:
            try:
                track = self.get_next_track()
                success = self.scrobble_track(track['artist'], track['track'])
                
                if success:
                    scrobble_count += 1
                    self.logger.info(f"Total scrobbles: {scrobble_count}")
                
                # Wait 3 minutes (180 seconds)
                for _ in range(180):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(30)
        
        self.logger.info("Scrobbler stopped")

if __name__ == "__main__":
    print("Last.fm 24/7 Auto Scrobbler")
    print("=" * 30)
    
    if not USERNAME or not PASSWORD:
        print("Error: Username and password required")
        sys.exit(1)
    
    scrobbler = AutoScrobbler()
    scrobbler.run()