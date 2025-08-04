#!/usr/bin/env python3
"""
Continuous Last.fm Scrobbler Bot - 24/7 Operation
Based on your code but enhanced for continuous operation
"""

import hashlib
import requests
import time
import random
import json
import logging
from datetime import datetime
import signal
import sys

# Your Last.fm API credentials
API_KEY = '45905c9b4239a9ec7b245f8a3711e87b'
SHARED_SECRET = 'afcbf283834eaea726d3176d1ab946d0'

# You'll need to provide your Last.fm username and password
USERNAME = input("Enter your Last.fm username: ").strip()
PASSWORD = input("Enter your Last.fm password: ").strip()

class ContinuousScrobbler:
    def __init__(self):
        self.session_key = None
        self.running = True
        self.scrobble_history = []
        self.setup_logging()
        self.setup_signal_handlers()
        
        # Default music library - classic tracks that are safe to scrobble
        self.music_library = [
            {'artist': 'The Beatles', 'track': 'Hey Jude', 'album': 'The Beatles 1967-1970', 'duration': 431},
            {'artist': 'Queen', 'track': 'Bohemian Rhapsody', 'album': 'A Night at the Opera', 'duration': 355},
            {'artist': 'Pink Floyd', 'track': 'Comfortably Numb', 'album': 'The Wall', 'duration': 382},
            {'artist': 'Led Zeppelin', 'track': 'Stairway to Heaven', 'album': 'Led Zeppelin IV', 'duration': 482},
            {'artist': 'The Rolling Stones', 'track': 'Paint It Black', 'album': 'Aftermath', 'duration': 202},
            {'artist': 'David Bowie', 'track': 'Space Oddity', 'album': 'David Bowie', 'duration': 317},
            {'artist': 'The Who', 'track': 'Baba O\'Riley', 'album': 'Who\'s Next', 'duration': 300},
            {'artist': 'Fleetwood Mac', 'track': 'Go Your Own Way', 'album': 'Rumours', 'duration': 217},
            {'artist': 'Eagles', 'track': 'Hotel California', 'album': 'Hotel California', 'duration': 391},
            {'artist': 'AC/DC', 'track': 'Back in Black', 'album': 'Back in Black', 'duration': 255},
            {'artist': 'Coldplay', 'track': 'Yellow', 'album': 'Parachutes', 'duration': 269},
            {'artist': 'Imagine Dragons', 'track': 'Believer', 'album': 'Evolve', 'duration': 204},
            {'artist': 'Radiohead', 'track': 'Creep', 'album': 'Pablo Honey', 'duration': 238},
            {'artist': 'Nirvana', 'track': 'Smells Like Teen Spirit', 'album': 'Nevermind', 'duration': 301},
            {'artist': 'Red Hot Chili Peppers', 'track': 'Under the Bridge', 'album': 'Blood Sugar Sex Magik', 'duration': 264}
        ]
        
    def setup_logging(self):
        """Setup logging for the bot"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scrobbler_24_7.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def generate_api_sig(self, params):
        """Generate API signature"""
        string = ''.join([f"{k}{params[k]}" for k in sorted(params)])
        string += SHARED_SECRET
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def get_session_key(self):
        """Get session key using username/password authentication"""
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
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params)
            data = response.json()
            
            if 'session' in data:
                self.session_key = data['session']['key']
                self.logger.info("✅ Successfully authenticated with Last.fm")
                return True
            else:
                self.logger.error(f"❌ Authentication failed: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error during authentication: {e}")
            return False

    def scrobble_track(self, track_info):
        """Scrobble a single track"""
        if not self.session_key:
            self.logger.error("No session key available")
            return False
            
        timestamp = int(time.time())
        
        params = {
            'method': 'track.scrobble',
            'api_key': API_KEY,
            'artist': track_info['artist'],
            'track': track_info['track'],
            'timestamp': str(timestamp),
            'sk': self.session_key,
            'format': 'json'
        }
        
        # Add optional parameters
        if 'album' in track_info:
            params['album'] = track_info['album']
        if 'duration' in track_info:
            params['duration'] = str(track_info['duration'])
            
        params['api_sig'] = self.generate_api_sig(params)
        
        try:
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params)
            data = response.json()
            
            if 'scrobbles' in data:
                self.logger.info(f"🎧 Successfully scrobbled: {track_info['artist']} - {track_info['track']}")
                
                # Add to history
                self.scrobble_history.append({
                    'artist': track_info['artist'],
                    'track': track_info['track'],
                    'timestamp': timestamp
                })
                
                # Keep only last 100 scrobbles in memory
                if len(self.scrobble_history) > 100:
                    self.scrobble_history = self.scrobble_history[-100:]
                    
                return True
            else:
                self.logger.warning(f"⚠️ Scrobble failed: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error scrobbling track: {e}")
            return False

    def was_recently_scrobbled(self, track_info):
        """Check if track was recently scrobbled (within last hour)"""
        current_time = time.time()
        for scrobble in reversed(self.scrobble_history):
            if current_time - scrobble['timestamp'] > 3600:  # 1 hour
                break
            if (scrobble['artist'].lower() == track_info['artist'].lower() and 
                scrobble['track'].lower() == track_info['track'].lower()):
                return True
        return False

    def get_next_track(self):
        """Get next track from library, avoiding recent duplicates"""
        attempts = 0
        while attempts < 10:  # Avoid infinite loop
            track = random.choice(self.music_library)
            if not self.was_recently_scrobbled(track):
                return track
            attempts += 1
        
        # If all tracks were recent, just return a random one
        return random.choice(self.music_library)

    def run_continuous(self, interval_minutes=3):
        """Run the scrobbler continuously"""
        if not self.get_session_key():
            self.logger.error("Failed to authenticate. Cannot start continuous scrobbling.")
            return
            
        self.logger.info(f"🚀 Starting continuous scrobbling every {interval_minutes} minutes")
        self.logger.info("Press Ctrl+C to stop")
        
        interval_seconds = interval_minutes * 60
        
        while self.running:
            try:
                # Get next track
                track = self.get_next_track()
                
                # Scrobble it
                success = self.scrobble_track(track)
                
                if success:
                    self.logger.info(f"📊 Total scrobbles this session: {len(self.scrobble_history)}")
                else:
                    self.logger.warning("Failed to scrobble, will retry next cycle")
                
                # Wait for next scrobble
                self.logger.info(f"💤 Waiting {interval_minutes} minutes until next scrobble...")
                
                # Sleep in small chunks to allow for graceful shutdown
                for i in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.logger.info("Continuing in 30 seconds...")
                time.sleep(30)
        
        self.logger.info("🛑 Scrobbling stopped")

if __name__ == "__main__":
    print("🎵 Last.fm 24/7 Continuous Scrobbler")
    print("=" * 40)
    
    if not USERNAME or not PASSWORD:
        print("❌ Username and password are required")
        sys.exit(1)
    
    scrobbler = ContinuousScrobbler()
    
    # Ask for scrobbling interval
    try:
        interval = int(input("Enter scrobbling interval in minutes (default 3): ") or "3")
        if interval < 1:
            interval = 3
    except ValueError:
        interval = 3
    
    print(f"\n🚀 Starting continuous scrobbling every {interval} minutes...")
    scrobbler.run_continuous(interval)