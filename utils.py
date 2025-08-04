"""
Utility Functions Module
Common utility functions for the Last.fm scrobbling bot
"""

import logging
import os
import sys
from configparser import ConfigParser
from typing import Optional

def setup_logging(config: ConfigParser) -> logging.Logger:
    """Setup logging configuration"""
    
    # Get logging configuration
    log_level = config.get('general', 'log_level', fallback='INFO').upper()
    log_file = config.get('general', 'log_file', fallback='scrobbler.log')
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler for {log_file}: {e}")
    
    return logger

def validate_config(config: ConfigParser) -> bool:
    """Validate configuration file"""
    
    required_sections = ['lastfm', 'general', 'music_sources']
    required_lastfm_keys = ['api_key', 'api_secret', 'username', 'password']
    
    # Check required sections
    for section in required_sections:
        if not config.has_section(section):
            print(f"Missing required section: [{section}]")
            return False
    
    # Check Last.fm credentials
    for key in required_lastfm_keys:
        if not config.has_option('lastfm', key):
            print(f"Missing required Last.fm credential: {key}")
            return False
        
        value = config.get('lastfm', key)
        if not value or value.strip() == '' or 'your_' in value.lower():
            print(f"Invalid Last.fm credential: {key} = '{value}'")
            print("Please update config.ini with your actual Last.fm API credentials")
            return False
    
    # Validate numeric values
    try:
        scrobble_interval = config.getint('general', 'scrobble_interval', fallback=180)
        if scrobble_interval < 30:
            print("Scrobble interval must be at least 30 seconds")
            return False
        
        retry_attempts = config.getint('general', 'retry_attempts', fallback=3)
        if retry_attempts < 1:
            print("Retry attempts must be at least 1")
            return False
            
    except ValueError as e:
        print(f"Invalid numeric value in configuration: {e}")
        return False
    
    return True

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def clean_string(text: str) -> str:
    """Clean and normalize string for comparison"""
    if not text:
        return ""
    
    # Remove extra whitespace and convert to lowercase
    cleaned = ' '.join(text.strip().split()).lower()
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = ['the ', 'a ', 'an ']
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    
    return cleaned

def get_safe_filename(text: str, max_length: int = 100) -> str:
    """Convert text to safe filename"""
    if not text:
        return "untitled"
    
    # Remove/replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    safe_text = text
    for char in unsafe_chars:
        safe_text = safe_text.replace(char, '_')
    
    # Remove extra spaces and dots
    safe_text = ' '.join(safe_text.split())
    safe_text = safe_text.strip('. ')
    
    # Truncate if too long
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length].rsplit(' ', 1)[0]
    
    return safe_text or "untitled"

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                Last.fm Automatic Scrobbling Bot             ║
║                                                              ║
║  Continuously scrobbles music tracks to your Last.fm        ║
║  profile with configurable timing and error handling        ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_stats(track_history, music_manager):
    """Print current statistics"""
    try:
        history_summary = track_history.get_history_summary()
        playlist_stats = music_manager.get_playlist_stats()
        
        print("\n" + "="*60)
        print("CURRENT STATISTICS")
        print("="*60)
        
        print(f"Total tracks scrobbled: {history_summary['total_tracks']}")
        print(f"Tracks in last 24h: {history_summary['recent_activity']['last_24h']}")
        print(f"Tracks in last 7d: {history_summary['recent_activity']['last_7d']}")
        
        print(f"\nPlaylist: {playlist_stats['total_tracks']} tracks")
        print(f"  - Local files: {playlist_stats['local_tracks']}")
        print(f"  - Streaming simulation: {playlist_stats['streaming_tracks']}")
        print(f"  - Current position: {playlist_stats['current_position'] + 1}")
        
        if history_summary['sources']:
            print("\nScrobbling sources:")
            for source, count in history_summary['sources'].items():
                print(f"  - {source}: {count} tracks")
        
        print("="*60)
        
    except Exception as e:
        print(f"Error displaying stats: {e}")

def check_environment():
    """Check if the environment is properly set up"""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 6):
        issues.append("Python 3.6 or higher is required")
    
    # Check required modules
    required_modules = ['requests', 'schedule']
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            issues.append(f"Required module '{module}' is not installed")
    
    return issues

def get_environment_info() -> dict:
    """Get information about the current environment"""
    return {
        'python_version': sys.version,
        'platform': sys.platform,
        'working_directory': os.getcwd(),
        'script_path': os.path.abspath(__file__),
        'environment_variables': {
            'LASTFM_API_KEY': '***' if os.getenv('LASTFM_API_KEY') else 'Not set',
            'LASTFM_API_SECRET': '***' if os.getenv('LASTFM_API_SECRET') else 'Not set',
            'LASTFM_USERNAME': '***' if os.getenv('LASTFM_USERNAME') else 'Not set',
            'LASTFM_PASSWORD': '***' if os.getenv('LASTFM_PASSWORD') else 'Not set'
        }
    }
