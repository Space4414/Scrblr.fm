#!/usr/bin/env python3
"""
Your Last.fm Scrobbler - Enhanced for 24/7 Operation
Based on your original code with continuous operation capabilities
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

# Get credentials from environment variables
USERNAME = os.getenv('LASTFM_USERNAME')
PASSWORD = os.getenv('LASTFM_PASSWORD')

class ContinuousScrobbler:
    def __init__(self):
        self.session_key = None
        self.running = True
        self.scrobble_count = 0
        self.setup_logging()
        self.setup_signal_handlers()
        
        # Taylor Swift - The Tortured Poets Department (Full Album)
        self.tracks = [
            {'artist': 'Taylor Swift', 'track': 'Fortnight', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Tortured Poets Department', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'My Boy Only Breaks His Favorite Toys', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'So Long, London', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'But Daddy I Love Him', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Fresh Out the Slammer', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Florida!!!', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Guilty as Sin?', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Who\'s Afraid of Little Old Me?', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'I Can Fix Him (No Really I Can)', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'loml', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'I Can Do It With a Broken Heart', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Smallest Man Who Ever Lived', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Alchemy', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Clara Bow', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Black Dog', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'imgonnagetyouback', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Albatross', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Chloe or Sam or Sophia or Marcus', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'How Did It End?', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'So High School', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'I Hate It Here', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'thanK you aIMee', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'I Look in People\'s Windows', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Prophecy', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Cassandra', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Peter', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Bolter', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'Robin', 'album': 'The Tortured Poets Department'},
            {'artist': 'Taylor Swift', 'track': 'The Manuscript', 'album': 'The Tortured Poets Department'}
        ]
        
        self.recent_tracks = []
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('scrobbler_24_7.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger()
        
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
    def stop(self, signum=None, frame=None):
        self.logger.info(f"Scrobbler stopped. Total tracks scrobbled: {self.scrobble_count}")
        self.running = False

    def generate_api_sig(self, params):
        """Your original signature generation function"""
        string = ''.join([f"{k}{params[k]}" for k in sorted(params)])
        string += SHARED_SECRET
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def get_session_key(self):
        """Get session key using mobile session method"""
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

    def scrobble_track(self, artist, track, timestamp=None):
        """Enhanced version of your original scrobble function"""
        if not self.session_key:
            self.logger.error("No session key available")
            return False
            
        if timestamp is None:
            timestamp = int(time.time())
            
        params = {
            'method': 'track.scrobble',
            'api_key': API_KEY,
            'artist': artist,
            'track': track,
            'timestamp': str(timestamp),
            'sk': self.session_key
        }
        params['api_sig'] = self.generate_api_sig(params)
        params['format'] = 'json'
        
        try:
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params, timeout=30)
            data = response.json()
            
            if 'scrobbles' in data:
                self.logger.info(f"Scrobbled: {artist} - {track}")
                self.scrobble_count += 1
                
                # Track recent scrobbles to avoid immediate duplicates
                self.recent_tracks.append({
                    'artist': artist.lower(),
                    'track': track.lower(),
                    'time': time.time()
                })
                
                # Keep only last 10 tracks
                if len(self.recent_tracks) > 10:
                    self.recent_tracks = self.recent_tracks[-10:]
                
                return True
            else:
                self.logger.warning(f"Scrobble response: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"Scrobble error: {e}")
            return False

    def get_next_track(self):
        """Get next track avoiding recent duplicates"""
        available_tracks = []
        current_time = time.time()
        
        # Remove tracks that were scrobbled in the last 2 hours
        recent_artist_tracks = set()
        for recent in self.recent_tracks:
            if current_time - recent['time'] < 7200:  # 2 hours
                recent_artist_tracks.add(f"{recent['artist']}|{recent['track']}")
        
        # Find available tracks
        for track in self.tracks:
            track_key = f"{track['artist'].lower()}|{track['track'].lower()}"
            if track_key not in recent_artist_tracks:
                available_tracks.append(track)
        
        # If no tracks available, use all tracks
        if not available_tracks:
            available_tracks = self.tracks
        
        return random.choice(available_tracks)

    def run_continuous(self, interval_minutes=3):
        """Run scrobbler continuously"""
        if not USERNAME or not PASSWORD:
            self.logger.error("Last.fm credentials not found in environment variables")
            return False
            
        if not self.get_session_key():
            self.logger.error("Failed to authenticate with Last.fm")
            return False
            
        self.logger.info(f"Starting 24/7 scrobbling every {interval_minutes} minutes")
        self.logger.info("Press Ctrl+C to stop")
        
        interval_seconds = interval_minutes * 60
        
        while self.running:
            try:
                # Get and scrobble next track
                track = self.get_next_track()
                success = self.scrobble_track(track['artist'], track['track'])
                
                if success:
                    self.logger.info(f"Total scrobbles this session: {self.scrobble_count}")
                else:
                    self.logger.warning("Scrobble failed, will retry next cycle")
                
                # Wait for next scrobble
                self.logger.info(f"Next scrobble in {interval_minutes} minutes...")
                
                # Sleep in 1-second intervals to allow graceful shutdown
                for i in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.logger.info("Continuing in 30 seconds...")
                time.sleep(30)
        
        return True

if __name__ == "__main__":
    print("Last.fm 24/7 Continuous Scrobbler")
    print("Based on your original code")
    print("=" * 40)
    
    scrobbler = ContinuousScrobbler()
    scrobbler.run_continuous(3)  # Scrobble every 3 minutes