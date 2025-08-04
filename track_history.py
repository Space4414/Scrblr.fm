"""
Track History Module
Manages scrobbling history to avoid duplicates and provide analytics
"""

import json
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path

class TrackHistory:
    """Manages track scrobbling history and duplicate prevention"""
    
    def __init__(self, history_file: str = 'track_history.json'):
        self.history_file = Path(history_file)
        self.logger = logging.getLogger(__name__)
        self.history = []
        self.duplicate_threshold = 3600  # 1 hour in seconds
        
        # Load existing history
        self._load_history()
    
    def _load_history(self):
        """Load track history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('tracks', [])
                    self.logger.info(f"Loaded {len(self.history)} tracks from history")
            else:
                self.logger.info("No existing history file found, starting fresh")
                self.history = []
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            self.history = []
    
    def _save_history(self):
        """Save track history to file"""
        try:
            # Keep only recent history (last 7 days)
            cutoff_time = time.time() - (7 * 24 * 3600)
            recent_history = [
                track for track in self.history 
                if track.get('timestamp', 0) > cutoff_time
            ]
            
            data = {
                'tracks': recent_history,
                'last_updated': time.time()
            }
            
            # Create directory if it doesn't exist
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.history = recent_history
            self.logger.debug(f"Saved {len(recent_history)} tracks to history")
            
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")
    
    def add_track(self, track: Dict[str, str]) -> bool:
        """Add a successfully scrobbled track to history"""
        try:
            history_entry = {
                'artist': track.get('artist', ''),
                'track': track.get('track', ''),
                'album': track.get('album', ''),
                'timestamp': time.time(),
                'source': track.get('source', 'unknown')
            }
            
            self.history.append(history_entry)
            self._save_history()
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding track to history: {e}")
            return False
    
    def was_recently_scrobbled(self, track: Dict[str, str]) -> bool:
        """Check if a track was recently scrobbled to avoid duplicates"""
        current_time = time.time()
        artist = track.get('artist', '').lower().strip()
        track_name = track.get('track', '').lower().strip()
        
        # Check recent history for duplicates
        for history_track in reversed(self.history):  # Start from most recent
            # Skip if too old
            if current_time - history_track.get('timestamp', 0) > self.duplicate_threshold:
                break
            
            # Compare artist and track name (case insensitive)
            hist_artist = history_track.get('artist', '').lower().strip()
            hist_track = history_track.get('track', '').lower().strip()
            
            if hist_artist == artist and hist_track == track_name:
                return True
        
        return False
    
    def get_recent_tracks(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recently scrobbled tracks"""
        return list(reversed(self.history[-limit:]))
    
    def get_track_count(self, hours: int = 24) -> int:
        """Get count of tracks scrobbled in the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        return sum(1 for track in self.history if track.get('timestamp', 0) > cutoff_time)
    
    def get_artist_stats(self, days: int = 7) -> Dict[str, int]:
        """Get artist play counts for the last N days"""
        cutoff_time = time.time() - (days * 24 * 3600)
        artist_counts = {}
        
        for track in self.history:
            if track.get('timestamp', 0) > cutoff_time:
                artist = track.get('artist', 'Unknown Artist')
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
        
        # Sort by play count
        return dict(sorted(artist_counts.items(), key=lambda x: x[1], reverse=True))
    
    def get_source_stats(self, days: int = 7) -> Dict[str, int]:
        """Get scrobbling source statistics for the last N days"""
        cutoff_time = time.time() - (days * 24 * 3600)
        source_counts = {}
        
        for track in self.history:
            if track.get('timestamp', 0) > cutoff_time:
                source = track.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
        
        return source_counts
    
    def clear_history(self):
        """Clear all track history"""
        try:
            self.history = []
            self._save_history()
            self.logger.info("Track history cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing history: {e}")
            return False
    
    def export_history(self, output_file: str) -> bool:
        """Export history to a different file"""
        try:
            export_data = {
                'export_date': time.time(),
                'total_tracks': len(self.history),
                'tracks': self.history
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"History exported to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting history: {e}")
            return False
    
    def get_history_summary(self) -> Dict:
        """Get a summary of the track history"""
        if not self.history:
            return {'total_tracks': 0, 'date_range': None, 'sources': {}}
        
        timestamps = [track.get('timestamp', 0) for track in self.history if track.get('timestamp')]
        
        return {
            'total_tracks': len(self.history),
            'date_range': {
                'first_scrobble': min(timestamps) if timestamps else None,
                'last_scrobble': max(timestamps) if timestamps else None
            },
            'sources': self.get_source_stats(days=30),
            'recent_activity': {
                'last_24h': self.get_track_count(24),
                'last_7d': self.get_track_count(24 * 7)
            }
        }
