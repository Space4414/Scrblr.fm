"""
Music Sources Module
Manages different sources of music tracks for scrobbling
"""

import os
import json
import random
import logging
from typing import Dict, List, Optional
from pathlib import Path

class MusicSourceManager:
    """Manages multiple music sources and provides tracks for scrobbling"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.current_playlist = []
        self.current_index = 0
        self.shuffle_enabled = config.getboolean('music_sources', 'shuffle_tracks', fallback=True)
        
        # Initialize music sources
        self._load_music_sources()
    
    def _load_music_sources(self):
        """Load tracks from all enabled music sources"""
        tracks = []
        
        # Load local music files if enabled
        if self.config.getboolean('music_sources', 'enable_local_files', fallback=True):
            local_tracks = self._load_local_music()
            tracks.extend(local_tracks)
            self.logger.info(f"Loaded {len(local_tracks)} local tracks")
        
        # Load streaming simulation tracks if enabled
        if self.config.getboolean('music_sources', 'enable_streaming_simulation', fallback=True):
            streaming_tracks = self._load_streaming_simulation()
            tracks.extend(streaming_tracks)
            self.logger.info(f"Loaded {len(streaming_tracks)} streaming simulation tracks")
        
        # Set up playlist
        if tracks:
            self.current_playlist = tracks
            if self.shuffle_enabled:
                random.shuffle(self.current_playlist)
            self.logger.info(f"Total tracks in playlist: {len(self.current_playlist)}")
        else:
            self.logger.warning("No tracks loaded from any source")
    
    def _load_local_music(self) -> List[Dict[str, str]]:
        """Load music from local directory"""
        tracks = []
        music_dir = self.config.get('music_sources', 'local_music_dir', fallback='./music')
        
        if not os.path.exists(music_dir):
            self.logger.info(f"Local music directory not found: {music_dir}")
            return tracks
        
        # Supported audio formats
        audio_extensions = {'.mp3', '.flac', '.m4a', '.wav', '.ogg', '.wma'}
        
        try:
            music_path = Path(music_dir)
            for file_path in music_path.rglob('*'):
                if file_path.suffix.lower() in audio_extensions:
                    track = self._extract_metadata_from_filename(file_path)
                    if track:
                        tracks.append(track)
        
        except Exception as e:
            self.logger.error(f"Error loading local music: {e}")
        
        return tracks
    
    def _extract_metadata_from_filename(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Extract track metadata from filename and directory structure"""
        try:
            # Get filename without extension
            filename = file_path.stem
            
            # Try different filename patterns
            track_info = None
            
            # Pattern: "Artist - Track Name"
            if ' - ' in filename:
                parts = filename.split(' - ', 1)
                if len(parts) == 2:
                    track_info = {
                        'artist': parts[0].strip(),
                        'track': parts[1].strip(),
                        'source': 'local_file'
                    }
            
            # Pattern: "Track Number. Artist - Track Name"
            elif '. ' in filename and ' - ' in filename:
                parts = filename.split('. ', 1)[1].split(' - ', 1)
                if len(parts) == 2:
                    track_info = {
                        'artist': parts[0].strip(),
                        'track': parts[1].strip(),
                        'source': 'local_file'
                    }
            
            # Fallback: use parent directory as artist
            else:
                track_info = {
                    'artist': file_path.parent.name,
                    'track': filename,
                    'source': 'local_file'
                }
            
            # Try to extract album from directory structure
            if track_info and len(file_path.parts) >= 2:
                # Check if parent directory could be an album
                parent_dir = file_path.parent.name
                grandparent_dir = file_path.parent.parent.name if len(file_path.parts) >= 3 else None
                
                # If artist is in grandparent and parent looks like album
                if grandparent_dir and grandparent_dir.lower() != 'music':
                    track_info['album'] = parent_dir
                    track_info['artist'] = grandparent_dir
            
            return track_info
            
        except Exception as e:
            self.logger.warning(f"Could not extract metadata from {file_path}: {e}")
            return None
    
    def _load_streaming_simulation(self) -> List[Dict[str, str]]:
        """Load predefined tracks that simulate streaming service"""
        # This simulates a music streaming service with a curated playlist
        # In a real implementation, this could connect to Spotify, Apple Music, etc.
        
        streaming_tracks = [
            {
                'artist': 'The Beatles',
                'track': 'Hey Jude',
                'album': 'The Beatles 1967-1970',
                'duration': '431',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'Queen',
                'track': 'Bohemian Rhapsody',
                'album': 'A Night at the Opera',
                'duration': '355',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'Pink Floyd',
                'track': 'Comfortably Numb',
                'album': 'The Wall',
                'duration': '382',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'Led Zeppelin',
                'track': 'Stairway to Heaven',
                'album': 'Led Zeppelin IV',
                'duration': '482',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'The Rolling Stones',
                'track': 'Paint It Black',
                'album': 'Aftermath',
                'duration': '202',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'David Bowie',
                'track': 'Space Oddity',
                'album': 'David Bowie',
                'duration': '317',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'The Who',
                'track': 'Baba O\'Riley',
                'album': 'Who\'s Next',
                'duration': '300',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'Fleetwood Mac',
                'track': 'Go Your Own Way',
                'album': 'Rumours',
                'duration': '217',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'Eagles',
                'track': 'Hotel California',
                'album': 'Hotel California',
                'duration': '391',
                'source': 'streaming_simulation'
            },
            {
                'artist': 'AC/DC',
                'track': 'Back in Black',
                'album': 'Back in Black',
                'duration': '255',
                'source': 'streaming_simulation'
            }
        ]
        
        return streaming_tracks
    
    def get_next_track(self) -> Optional[Dict[str, str]]:
        """Get the next track from the current playlist"""
        if not self.current_playlist:
            self.logger.warning("No tracks available in playlist")
            return None
        
        # Get current track
        track = self.current_playlist[self.current_index]
        
        # Advance to next track
        self.current_index = (self.current_index + 1) % len(self.current_playlist)
        
        # If we've completed a full cycle and shuffle is enabled, reshuffle
        if self.current_index == 0 and self.shuffle_enabled:
            random.shuffle(self.current_playlist)
            self.logger.debug("Reshuffled playlist")
        
        return track.copy()  # Return a copy to avoid modification
    
    def get_current_track(self) -> Optional[Dict[str, str]]:
        """Get the current track without advancing"""
        if not self.current_playlist:
            return None
        
        return self.current_playlist[self.current_index].copy()
    
    def refresh_sources(self):
        """Refresh all music sources"""
        self.logger.info("Refreshing music sources...")
        self._load_music_sources()
    
    def get_playlist_stats(self) -> Dict[str, int]:
        """Get statistics about the current playlist"""
        if not self.current_playlist:
            return {'total_tracks': 0, 'local_tracks': 0, 'streaming_tracks': 0}
        
        local_count = sum(1 for track in self.current_playlist if track.get('source') == 'local_file')
        streaming_count = sum(1 for track in self.current_playlist if track.get('source') == 'streaming_simulation')
        
        return {
            'total_tracks': len(self.current_playlist),
            'local_tracks': local_count,
            'streaming_tracks': streaming_count,
            'current_position': self.current_index
        }
