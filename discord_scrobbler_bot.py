#!/usr/bin/env python3
"""
Universal Last.fm Scrobbler Discord Bot
Advanced Discord bot with Spotify/Deezer integration, playlist management, and community features
"""

import discord
from discord.ext import commands, tasks
import hashlib
import requests
import time
import random
import json
import os
import asyncio
from datetime import datetime, timedelta
import logging
import threading
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
try:
    import deezer
except ImportError:
    deezer = None

# Configure logging
logging.basicConfig(level=logging.INFO)

# Last.fm API credentials
API_KEY = '45905c9b4239a9ec7b245f8a3711e87b'
SHARED_SECRET = 'afcbf283834eaea726d3176d1ab946d0'

# Discord bot token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Default credentials (users can override with commands)
DEFAULT_USERNAME = os.getenv('LASTFM_USERNAME')
DEFAULT_PASSWORD = os.getenv('LASTFM_PASSWORD')

# Spotify credentials (optional)
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class UniversalDiscordScrobbler:
    def __init__(self):
        # User management
        self.user_sessions = {}  # user_id -> session data
        self.active_sessions = {}  # user_id -> auto-scrobbling data
        
        # Spotify integration
        self.spotify = None
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            except Exception as e:
                logging.error(f"Spotify initialization failed: {e}")
        
        # Deezer integration
        self.deezer_client = None
        if deezer:
            try:
                self.deezer_client = deezer.Client()
            except Exception as e:
                logging.error(f"Deezer initialization failed: {e}")
        
        # Community playlists
        self.community_playlists = {}
        self.load_community_playlists()
        
    def load_community_playlists(self):
        """Load community playlists from file"""
        try:
            if os.path.exists('community_playlists.json'):
                with open('community_playlists.json', 'r') as f:
                    self.community_playlists = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load community playlists: {e}")
    
    def save_community_playlists(self):
        """Save community playlists to file"""
        try:
            with open('community_playlists.json', 'w') as f:
                json.dump(self.community_playlists, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save community playlists: {e}")
        
    def generate_api_sig(self, params):
        string = ''.join([f"{k}{params[k]}" for k in sorted(params)])
        string += SHARED_SECRET
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    async def authenticate_user(self, user_id, username, password):
        """Authenticate a user with Last.fm"""
        params = {
            'method': 'auth.getMobileSession',
            'api_key': API_KEY,
            'username': username,
            'password': password,
        }
        params['api_sig'] = self.generate_api_sig(params)
        params['format'] = 'json'
        
        try:
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params, timeout=30)
            data = response.json()
            
            if 'session' in data:
                self.user_sessions[user_id] = {
                    'username': username,
                    'session_key': data['session']['key'],
                    'playlists': {},
                    'scrobble_history': [],
                    'preferences': {
                        'default_interval': 3,
                        'shuffle_mode': True
                    }
                }
                return True, "Successfully authenticated with Last.fm!"
            else:
                error_msg = data.get('error', 'Unknown error')
                return False, f"Authentication failed: {error_msg}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    async def scrobble_track(self, user_id, artist, track, album=None):
        """Scrobble a track for a specific user"""
        if user_id not in self.user_sessions:
            return False, "Please authenticate first with !login"
            
        session = self.user_sessions[user_id]
        timestamp = int(time.time())
        
        params = {
            'method': 'track.scrobble',
            'api_key': API_KEY,
            'artist': artist,
            'track': track,
            'timestamp': str(timestamp),
            'sk': session['session_key']
        }
        
        if album:
            params['album'] = album
            
        params['api_sig'] = self.generate_api_sig(params)
        params['format'] = 'json'
        
        try:
            response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params, timeout=30)
            data = response.json()
            
            if 'scrobbles' in data:
                session['scrobble_history'].append({
                    'artist': artist,
                    'track': track,
                    'album': album,
                    'timestamp': timestamp
                })
                return True, "Track scrobbled successfully!"
            else:
                error_msg = data.get('error', 'Unknown error')
                return False, f"Scrobble failed: {error_msg}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    async def get_spotify_playlist(self, playlist_id):
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
                        'duration': item['track']['duration_ms'],
                        'spotify_id': item['track']['id']
                    }
                    tracks.append(track_data)
            
            return tracks, None
            
        except Exception as e:
            logging.error(f"Spotify playlist error: {e}")
            return None, str(e)
    
    async def get_deezer_playlist(self, playlist_id):
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
    
    async def search_spotify(self, query, type='track', limit=10):
        """Search Spotify for tracks, albums, or playlists"""
        if not self.spotify:
            return None, "Spotify not configured"
            
        try:
            results = self.spotify.search(query, type=type, limit=limit)
            return results, None
        except Exception as e:
            return None, str(e)
    
    async def search_deezer(self, query, type='track', limit=10):
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
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        if user_id not in self.user_sessions:
            return None
            
        session = self.user_sessions[user_id]
        history = session['scrobble_history']
        
        if not history:
            return {
                'total_scrobbles': 0,
                'unique_artists': 0,
                'unique_tracks': 0,
                'top_artist': None,
                'top_track': None
            }
        
        # Calculate stats
        artists = [s['artist'] for s in history]
        tracks = [f"{s['artist']} - {s['track']}" for s in history]
        
        artist_counts = {}
        track_counts = {}
        
        for artist in artists:
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
        
        for track in tracks:
            track_counts[track] = track_counts.get(track, 0) + 1
        
        top_artist = max(artist_counts.items(), key=lambda x: x[1])[0] if artist_counts else None
        top_track = max(track_counts.items(), key=lambda x: x[1])[0] if track_counts else None
        
        return {
            'total_scrobbles': len(history),
            'unique_artists': len(set(artists)),
            'unique_tracks': len(set(tracks)),
            'top_artist': top_artist,
            'top_track': top_track
        }
    
    async def start_auto_scrobbling(self, user_id, playlist_name, interval_minutes=3, shuffle=True):
        """Start auto-scrobbling session for user"""
        if user_id not in self.user_sessions:
            return False, "Please authenticate first with !login"
        
        if playlist_name not in self.user_sessions[user_id]['playlists']:
            return False, f"Playlist '{playlist_name}' not found"
        
        if user_id in self.active_sessions:
            return False, "Auto-scrobbling already active. Use !stop first."
        
        playlist = self.user_sessions[user_id]['playlists'][playlist_name]
        
        self.active_sessions[user_id] = {
            'playlist': playlist.copy(),
            'interval': interval_minutes,
            'shuffle': shuffle,
            'current_index': 0,
            'total_scrobbles': 0,
            'started_at': datetime.now()
        }
        
        return True, f"Started auto-scrobbling '{playlist_name}' every {interval_minutes} minutes"
    
    async def stop_auto_scrobbling(self, user_id):
        """Stop auto-scrobbling session for user"""
        if user_id in self.active_sessions:
            session = self.active_sessions.pop(user_id)
            return True, f"Stopped auto-scrobbling. Total: {session['total_scrobbles']} tracks"
        else:
            return False, "No active auto-scrobbling session"

scrobbler = UniversalDiscordScrobbler()

@bot.event
async def on_ready():
    print(f'🎵 Universal Last.fm Scrobbler Bot ({bot.user}) is online!')
    print('🔗 Features: Spotify/Deezer integration, Multi-user support, Community playlists')
    
    # Start the auto-scrobbling task
    if not auto_scrobble_task.is_running():
        auto_scrobble_task.start()
    
    # Default authentication for backwards compatibility
    if DEFAULT_USERNAME and DEFAULT_PASSWORD:
        success, message = await scrobbler.authenticate_user('default', DEFAULT_USERNAME, DEFAULT_PASSWORD)
        if success:
            print(f'✅ Default user authenticated: {DEFAULT_USERNAME}')
        else:
            print(f'❌ Default authentication failed: {message}')

@bot.command(name='login')
async def login_user(ctx, username: str, password: str):
    """Authenticate with Last.fm: !login "username" "password" """
    
    user_id = str(ctx.author.id)
    success, message = await scrobbler.authenticate_user(user_id, username, password)
    
    if success:
        await ctx.send(f"✅ {message} Welcome, {username}!")
    else:
        await ctx.send(f"❌ {message}")

@bot.command(name='scrobble')
async def scrobble_single(ctx, artist: str, track: str, album: str = None):
    """Scrobble a single track: !scrobble "Artist Name" "Track Name" "Album Name" """
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    success, message = await scrobbler.scrobble_track(user_id, artist, track, album)
    
    if success:
        album_text = f" from '{album}'" if album else ""
        await ctx.send(f"✅ Scrobbled: **{artist}** - *{track}*{album_text}")
    else:
        await ctx.send(f"❌ {message}")

@bot.command(name='create')
async def create_playlist(ctx, name: str, *tracks):
    """Create a custom playlist: !create "My Playlist" "Artist1 - Track1" "Artist2 - Track2" """
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    playlist = []
    for track_string in tracks:
        if ' - ' in track_string:
            parts = track_string.split(' - ')
            playlist.append({
                'artist': parts[0].strip(),
                'track': parts[1].strip(),
                'album': parts[2].strip() if len(parts) > 2 else ''
            })
    
    if playlist:
        scrobbler.user_sessions[user_id]['playlists'][name] = playlist
        await ctx.send(f"✅ Created playlist '{name}' with {len(playlist)} tracks!")
        
        # Show the playlist
        playlist_text = "\n".join([f"{i+1}. {t['artist']} - {t['track']}" for i, t in enumerate(playlist[:10])])
        if len(playlist) > 10:
            playlist_text += f"\n... and {len(playlist) - 10} more tracks"
        
        embed = discord.Embed(title=f"Playlist: {name}", description=playlist_text, color=0x1DB954)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ No valid tracks found. Use format: !create \"Playlist Name\" \"Artist - Track\" \"Artist2 - Track2\"")

@bot.command(name='spotify')
async def import_spotify_playlist(ctx, playlist_url: str, name: str = None):
    """Import Spotify playlist: !spotify "https://open.spotify.com/playlist/..." "My Playlist" """
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    # Extract playlist ID from URL
    try:
        if 'playlist/' in playlist_url:
            playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        else:
            playlist_id = playlist_url
        
        await ctx.send("🔍 Importing Spotify playlist...")
        tracks, error = await scrobbler.get_spotify_playlist(playlist_id)
        
        if error:
            await ctx.send(f"❌ {error}")
            return
        
        playlist_name = name or f"Spotify Playlist {playlist_id[:8]}"
        scrobbler.user_sessions[user_id]['playlists'][playlist_name] = tracks
        
        embed = discord.Embed(
            title="✅ Spotify Import Complete",
            description=f"Imported {len(tracks)} tracks to '{playlist_name}'",
            color=0x1DB954
        )
        
        # Show first few tracks
        if tracks:
            track_list = "\n".join([f"{i+1}. {t['artist']} - {t['track']}" for i, t in enumerate(tracks[:5])])
            if len(tracks) > 5:
                track_list += f"\n... and {len(tracks) - 5} more tracks"
            embed.add_field(name="Sample Tracks", value=track_list, inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Failed to import Spotify playlist: {str(e)}")

@bot.command(name='deezer')
async def import_deezer_playlist(ctx, playlist_url: str, name: str = None):
    """Import Deezer playlist: !deezer "https://www.deezer.com/playlist/..." "My Playlist" """
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    # Extract playlist ID from URL
    try:
        if 'playlist/' in playlist_url:
            playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        else:
            playlist_id = playlist_url
        
        await ctx.send("🔍 Importing Deezer playlist...")
        tracks, error = await scrobbler.get_deezer_playlist(playlist_id)
        
        if error:
            await ctx.send(f"❌ {error}")
            return
        
        playlist_name = name or f"Deezer Playlist {playlist_id[:8]}"
        scrobbler.user_sessions[user_id]['playlists'][playlist_name] = tracks
        
        embed = discord.Embed(
            title="✅ Deezer Import Complete",
            description=f"Imported {len(tracks)} tracks to '{playlist_name}'",
            color=0xFF6600
        )
        
        # Show first few tracks
        if tracks:
            track_list = "\n".join([f"{i+1}. {t['artist']} - {t['track']}" for i, t in enumerate(tracks[:5])])
            if len(tracks) > 5:
                track_list += f"\n... and {len(tracks) - 5} more tracks"
            embed.add_field(name="Sample Tracks", value=track_list, inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Failed to import Deezer playlist: {str(e)}")

@bot.command(name='auto')
async def start_auto_scrobbling(ctx, playlist_name: str, interval: int = 3, shuffle: bool = True):
    """Start auto-scrobbling: !auto "My Playlist" 5 true"""
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if interval < 1 or interval > 60:
        interval = 3
    
    success, message = await scrobbler.start_auto_scrobbling(user_id, playlist_name, interval, shuffle)
    
    if success:
        embed = discord.Embed(
            title="🎵 Auto-Scrobbling Started",
            description=message,
            color=0x1DB954
        )
        embed.add_field(name="Playlist", value=playlist_name, inline=True)
        embed.add_field(name="Interval", value=f"{interval} minutes", inline=True)
        embed.add_field(name="Shuffle", value="✅ On" if shuffle else "❌ Off", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ {message}")

@bot.command(name='stop')
async def stop_auto_scrobbling(ctx):
    """Stop auto-scrobbling"""
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    success, message = await scrobbler.stop_auto_scrobbling(user_id)
    
    if success:
        await ctx.send(f"⏹️ {message}")
    else:
        await ctx.send(f"ℹ️ {message}")

@bot.command(name='playlists')
async def list_playlists(ctx):
    """Show your playlists"""
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    playlists = scrobbler.user_sessions[user_id]['playlists']
    
    if not playlists:
        await ctx.send("📝 No playlists found. Create one with !create or import with !spotify/!deezer")
        return
    
    embed = discord.Embed(title="🎵 Your Playlists", color=0x1DB954)
    
    for name, tracks in playlists.items():
        embed.add_field(
            name=name,
            value=f"{len(tracks)} tracks",
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def show_status(ctx):
    """Show current scrobbling status"""
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    stats = scrobbler.get_user_stats(user_id)
    session = scrobbler.user_sessions[user_id]
    is_active = user_id in scrobbler.active_sessions
    
    embed = discord.Embed(title="📊 Your Scrobbler Status", color=0x1DB954)
    embed.add_field(name="Total Scrobbles", value=str(stats['total_scrobbles']), inline=True)
    embed.add_field(name="Unique Artists", value=str(stats['unique_artists']), inline=True)
    embed.add_field(name="Playlists", value=str(len(session['playlists'])), inline=True)
    embed.add_field(name="Auto-Scrobbling", value="🎵 Active" if is_active else "⏸️ Stopped", inline=True)
    
    if stats['top_artist']:
        embed.add_field(name="Top Artist", value=stats['top_artist'], inline=True)
    
    if stats['top_track']:
        embed.add_field(name="Top Track", value=stats['top_track'], inline=False)
    
    # Active session info
    if is_active:
        active = scrobbler.active_sessions[user_id]
        embed.add_field(
            name="Current Session", 
            value=f"Interval: {active['interval']}min • Scrobbles: {active['total_scrobbles']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='recent')
async def show_recent(ctx, count: int = 5):
    """Show recent scrobbles: !recent 10"""
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    history = scrobbler.user_sessions[user_id]['scrobble_history']
    
    if not history:
        await ctx.send("📝 No scrobbles yet!")
        return
    
    recent = history[-count:]
    
    embed = discord.Embed(title=f"🎵 Last {len(recent)} Scrobbles", color=0x1DB954)
    
    for i, track in enumerate(reversed(recent), 1):
        album_text = f" • {track['album']}" if track.get('album') else ""
        embed.add_field(
            name=f"{i}. {track['artist']} - {track['track']}{album_text}",
            value=f"<t:{track['timestamp']}:R>",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='search')
async def search_music(ctx, platform: str, *, query: str):
    """Search for music: !search spotify "taylor swift" or !search deezer "daft punk" """
    
    platform = platform.lower()
    
    if platform == 'spotify':
        results, error = await scrobbler.search_spotify(query, 'track', 5)
        if error:
            await ctx.send(f"❌ Spotify search failed: {error}")
            return
        
        if not results or not results['tracks']['items']:
            await ctx.send("🔍 No Spotify results found")
            return
        
        embed = discord.Embed(title=f"🎵 Spotify Search: {query}", color=0x1DB954)
        
        for i, track in enumerate(results['tracks']['items'][:5], 1):
            embed.add_field(
                name=f"{i}. {track['artists'][0]['name']} - {track['name']}",
                value=f"Album: {track['album']['name']}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    elif platform == 'deezer':
        results, error = await scrobbler.search_deezer(query, 'track', 5)
        if error:
            await ctx.send(f"❌ Deezer search failed: {error}")
            return
        
        if not results:
            await ctx.send("🔍 No Deezer results found")
            return
        
        embed = discord.Embed(title=f"🎵 Deezer Search: {query}", color=0xFF6600)
        
        for i, track in enumerate(results[:5], 1):
            embed.add_field(
                name=f"{i}. {track.artist.name} - {track.title}",
                value=f"Album: {track.album.title}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    else:
        await ctx.send("❌ Platform must be 'spotify' or 'deezer'")

@bot.command(name='share')
async def share_playlist(ctx, playlist_name: str):
    """Share a playlist with the community: !share "My Playlist" """
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    if playlist_name not in scrobbler.user_sessions[user_id]['playlists']:
        await ctx.send(f"❌ Playlist '{playlist_name}' not found")
        return
    
    playlist = scrobbler.user_sessions[user_id]['playlists'][playlist_name]
    
    # Add to community playlists
    community_id = f"{user_id}_{playlist_name}_{int(time.time())}"
    scrobbler.community_playlists[community_id] = {
        'name': playlist_name,
        'tracks': playlist,
        'author': ctx.author.display_name,
        'author_id': user_id,
        'created_at': int(time.time()),
        'likes': 0,
        'uses': 0
    }
    
    scrobbler.save_community_playlists()
    
    embed = discord.Embed(
        title="✅ Playlist Shared!",
        description=f"'{playlist_name}' is now available to the community",
        color=0x1DB954
    )
    embed.add_field(name="Tracks", value=str(len(playlist)), inline=True)
    embed.add_field(name="Author", value=ctx.author.display_name, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='community')
async def list_community_playlists(ctx):
    """Show community playlists"""
    
    if not scrobbler.community_playlists:
        await ctx.send("📝 No community playlists yet. Share yours with !share!")
        return
    
    embed = discord.Embed(title="🌟 Community Playlists", color=0x9A031E)
    
    # Sort by likes and creation time
    sorted_playlists = sorted(
        scrobbler.community_playlists.items(),
        key=lambda x: (x[1]['likes'], x[1]['created_at']),
        reverse=True
    )
    
    for i, (playlist_id, playlist) in enumerate(sorted_playlists[:10], 1):
        embed.add_field(
            name=f"{i}. {playlist['name']}",
            value=f"By {playlist['author']} • {len(playlist['tracks'])} tracks • ❤️ {playlist['likes']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='copy')
async def copy_community_playlist(ctx, playlist_number: int, new_name: str = None):
    """Copy a community playlist: !copy 1 "My Copy" """
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    if not scrobbler.community_playlists:
        await ctx.send("📝 No community playlists available")
        return
    
    # Get playlist by number
    sorted_playlists = sorted(
        scrobbler.community_playlists.items(),
        key=lambda x: (x[1]['likes'], x[1]['created_at']),
        reverse=True
    )
    
    if playlist_number < 1 or playlist_number > len(sorted_playlists):
        await ctx.send(f"❌ Invalid playlist number. Use 1-{len(sorted_playlists)}")
        return
    
    playlist_id, community_playlist = sorted_playlists[playlist_number - 1]
    
    # Copy to user's playlists
    copied_name = new_name or f"{community_playlist['name']} (Copy)"
    scrobbler.user_sessions[user_id]['playlists'][copied_name] = community_playlist['tracks'].copy()
    
    # Increment usage count
    scrobbler.community_playlists[playlist_id]['uses'] += 1
    scrobbler.save_community_playlists()
    
    embed = discord.Embed(
        title="✅ Playlist Copied!",
        description=f"Copied '{community_playlist['name']}' as '{copied_name}'",
        color=0x1DB954
    )
    embed.add_field(name="Original Author", value=community_playlist['author'], inline=True)
    embed.add_field(name="Tracks", value=str(len(community_playlist['tracks'])), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='swift')
async def load_taylor_swift(ctx):
    """Load Taylor Swift's Tortured Poets Department album"""
    
    user_id = str(ctx.author.id)
    
    # Try user's session first, then default
    if user_id not in scrobbler.user_sessions and 'default' in scrobbler.user_sessions:
        user_id = 'default'
    
    if user_id not in scrobbler.user_sessions:
        await ctx.send("❌ Please authenticate first with !login")
        return
    
    tortured_poets = [
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
    
    scrobbler.user_sessions[user_id]['playlists']['Taylor Swift - TTPD'] = tortured_poets
    
    embed = discord.Embed(
        title="🎵 Taylor Swift - The Tortured Poets Department",
        description=f"Added {len(tortured_poets)} tracks to your playlists as 'Taylor Swift - TTPD'!",
        color=0x9A031E
    )
    
    await ctx.send(embed=embed)

@tasks.loop(minutes=1)
async def auto_scrobble_task():
    """Background task for auto-scrobbling all active sessions"""
    
    current_time = time.time()
    
    # Process each active session
    for user_id, session in list(scrobbler.active_sessions.items()):
        # Check if it's time to scrobble
        last_scrobble = session.get('last_scrobble_time', 0)
        interval_seconds = session['interval'] * 60
        
        if current_time - last_scrobble >= interval_seconds:
            # Pick track based on shuffle setting
            if session['shuffle']:
                track = random.choice(session['playlist'])
            else:
                track = session['playlist'][session['current_index']]
                session['current_index'] = (session['current_index'] + 1) % len(session['playlist'])
            
            # Scrobble the track
            success, message = await scrobbler.scrobble_track(
                user_id, 
                track['artist'], 
                track['track'], 
                track.get('album')
            )
            
            if success:
                session['total_scrobbles'] += 1
                session['last_scrobble_time'] = current_time
                
                # Log success (could send to a channel if desired)
                logging.info(f"Auto-scrobbled for user {user_id}: {track['artist']} - {track['track']}")

@bot.command(name='commands')
async def help_command(ctx):
    """Show all Universal Scrobbler commands"""
    
    embed = discord.Embed(
        title="🎵 Universal Last.fm Scrobbler Bot",
        description="Advanced Discord bot with Spotify/Deezer integration and community features",
        color=0x1DB954
    )
    
    # Authentication
    embed.add_field(
        name="🔐 Authentication",
        value="`!login username password` - Authenticate with Last.fm",
        inline=False
    )
    
    # Basic Scrobbling
    embed.add_field(
        name="🎵 Basic Scrobbling",
        value="`!scrobble \"Artist\" \"Track\" \"Album\"` - Scrobble single track\n"
              "`!recent 10` - Show recent scrobbles\n"
              "`!status` - Show your stats and status",
        inline=False
    )
    
    # Playlist Management
    embed.add_field(
        name="📋 Playlist Management",
        value="`!create \"Name\" \"Artist1-Track1\" \"Artist2-Track2\"` - Create playlist\n"
              "`!playlists` - List your playlists\n"
              "`!swift` - Load Taylor Swift album",
        inline=False
    )
    
    # Platform Integration
    embed.add_field(
        name="🔗 Platform Integration",
        value="`!spotify playlist_url \"Name\"` - Import Spotify playlist\n"
              "`!deezer playlist_url \"Name\"` - Import Deezer playlist\n"
              "`!search spotify \"query\"` - Search Spotify\n"
              "`!search deezer \"query\"` - Search Deezer",
        inline=False
    )
    
    # Auto-Scrobbling
    embed.add_field(
        name="🤖 Auto-Scrobbling",
        value="`!auto \"Playlist\" 5 true` - Start auto-scrobbling (5min, shuffle on)\n"
              "`!stop` - Stop auto-scrobbling",
        inline=False
    )
    
    # Community Features
    embed.add_field(
        name="🌟 Community",
        value="`!share \"Playlist\"` - Share playlist with community\n"
              "`!community` - Browse community playlists\n"
              "`!copy 1 \"Name\"` - Copy community playlist",
        inline=False
    )
    
    embed.set_footer(text="Universal Scrobbler • Multi-platform music scrobbling made easy")
    
    await ctx.send(embed=embed)

@bot.command(name='like')
async def like_community_playlist(ctx, playlist_number: int):
    """Like a community playlist: !like 1"""
    
    if not scrobbler.community_playlists:
        await ctx.send("📝 No community playlists available")
        return
    
    # Get playlist by number
    sorted_playlists = sorted(
        scrobbler.community_playlists.items(),
        key=lambda x: (x[1]['likes'], x[1]['created_at']),
        reverse=True
    )
    
    if playlist_number < 1 or playlist_number > len(sorted_playlists):
        await ctx.send(f"❌ Invalid playlist number. Use 1-{len(sorted_playlists)}")
        return
    
    playlist_id, community_playlist = sorted_playlists[playlist_number - 1]
    
    # Increment likes
    scrobbler.community_playlists[playlist_id]['likes'] += 1
    scrobbler.save_community_playlists()
    
    await ctx.send(f"❤️ Liked '{community_playlist['name']}' by {community_playlist['author']}!")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use `!help` for command usage.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Unknown command. Use `!help` to see all available commands.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        logging.error(f"Command error: {error}")

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable not set")
        print("Please set your Discord bot token as an environment variable")
        print("\nTo get a Discord bot token:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Create a new application")
        print("3. Go to the 'Bot' section")
        print("4. Create a bot and copy the token")
        print("5. Set the environment variable: export DISCORD_TOKEN='your_token_here'")
    else:
        print("🚀 Starting Universal Last.fm Scrobbler Discord Bot...")
        bot.run(DISCORD_TOKEN)