"""
Last.fm Scrobbler Module
Handles authentication and scrobbling to Last.fm API
"""

import time
import json
import hashlib
import urllib.parse
import logging
import requests
from typing import Dict, Optional

class LastFMScrobbler:
    """Last.fm API scrobbler with authentication and retry logic"""
    
    BASE_URL = 'http://ws.audioscrobbler.com/2.0/'
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.api_key = config.get('lastfm', 'api_key')
        self.api_secret = config.get('lastfm', 'api_secret')
        self.username = config.get('lastfm', 'username')
        self.password = config.get('lastfm', 'password')
        self.session_key = None
        self.retry_attempts = config.getint('general', 'retry_attempts', fallback=3)
        self.retry_delay = config.getint('general', 'retry_delay', fallback=5)
    
    def _generate_signature(self, params: Dict[str, str]) -> str:
        """Generate API signature for authentication"""
        # Sort parameters and create signature string
        sorted_params = sorted(params.items())
        signature_string = ''.join([f"{k}{v}" for k, v in sorted_params])
        signature_string += self.api_secret
        
        # Return MD5 hash
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest()
    
    def _make_request(self, method: str, params: Dict[str, str], use_post: bool = False) -> Optional[Dict]:
        """Make authenticated request to Last.fm API with retry logic"""
        params.update({
            'method': method,
            'api_key': self.api_key,
            'format': 'json'
        })
        
        # Add session key if available
        if self.session_key:
            params['sk'] = self.session_key
        
        # Generate signature
        params['api_sig'] = self._generate_signature(params)
        
        for attempt in range(self.retry_attempts):
            try:
                if use_post:
                    response = requests.post(self.BASE_URL, data=params, timeout=30)
                else:
                    response = requests.get(self.BASE_URL, params=params, timeout=30)
                
                response.raise_for_status()
                data = response.json()
                
                # Check for Last.fm API errors
                if 'error' in data:
                    error_code = data.get('error', 0)
                    error_message = data.get('message', 'Unknown error')
                    self.logger.error(f"Last.fm API error {error_code}: {error_message}")
                    
                    # Don't retry certain errors
                    if error_code in [4, 9, 10, 13]:  # Auth errors, invalid method, service offline, invalid signature
                        return None
                    
                    if attempt < self.retry_attempts - 1:
                        self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue
                    
                    return None
                
                return data
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error("Max retry attempts reached")
        
        return None
    
    def authenticate(self) -> bool:
        """Authenticate with Last.fm and get session key"""
        try:
            # Generate auth token
            auth_params = {
                'username': self.username,
                'password': self.password
            }
            
            response = self._make_request('auth.getMobileSession', auth_params, use_post=True)
            
            if response and 'session' in response:
                self.session_key = response['session']['key']
                self.logger.info("Successfully authenticated with Last.fm")
                return True
            else:
                self.logger.error("Failed to authenticate with Last.fm")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def scrobble_track(self, track: Dict[str, str]) -> bool:
        """Scrobble a single track to Last.fm"""
        if not self.session_key:
            self.logger.error("Not authenticated with Last.fm")
            return False
        
        # Prepare scrobble parameters
        timestamp = str(int(time.time()))
        scrobble_params = {
            'artist': track.get('artist', ''),
            'track': track.get('track', ''),
            'timestamp': timestamp
        }
        
        # Add optional parameters
        if track.get('album'):
            scrobble_params['album'] = track['album']
        if track.get('duration'):
            scrobble_params['duration'] = str(track['duration'])
        if track.get('album_artist'):
            scrobble_params['albumArtist'] = track['album_artist']
        if track.get('track_number'):
            scrobble_params['trackNumber'] = str(track['track_number'])
        
        # Make scrobble request
        response = self._make_request('track.scrobble', scrobble_params, use_post=True)
        
        if response and 'scrobbles' in response:
            # Check if scrobble was accepted
            scrobbles = response['scrobbles']
            if '@attr' in scrobbles and scrobbles['@attr']['accepted'] == '1':
                return True
            else:
                # Check for individual scrobble errors
                scrobble = scrobbles.get('scrobble', {})
                if 'ignoredMessage' in scrobble:
                    self.logger.warning(f"Scrobble ignored: {scrobble['ignoredMessage']['#text']}")
                return False
        
        return False
    
    def update_now_playing(self, track: Dict[str, str]) -> bool:
        """Update now playing status on Last.fm"""
        if not self.session_key:
            self.logger.error("Not authenticated with Last.fm")
            return False
        
        # Prepare now playing parameters
        np_params = {
            'artist': track.get('artist', ''),
            'track': track.get('track', '')
        }
        
        # Add optional parameters
        if track.get('album'):
            np_params['album'] = track['album']
        if track.get('duration'):
            np_params['duration'] = str(track['duration'])
        if track.get('album_artist'):
            np_params['albumArtist'] = track['album_artist']
        if track.get('track_number'):
            np_params['trackNumber'] = str(track['track_number'])
        
        # Make now playing request
        response = self._make_request('track.updateNowPlaying', np_params, use_post=True)
        
        if response and 'nowplaying' in response:
            self.logger.debug(f"Updated now playing: {track['artist']} - {track['track']}")
            return True
        
        return False
    
    def get_user_info(self) -> Optional[Dict]:
        """Get authenticated user information"""
        if not self.session_key:
            return None
        
        response = self._make_request('user.getInfo', {'user': self.username})
        return response.get('user') if response else None
