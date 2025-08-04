from flask import render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import current_user, login_required
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import User, Playlist, ScrobbleSession, ScrobbleHistory, UserStats, CommunityPlaylist
from universal_scrobbler import scrobbler
import json
import logging

# Register Replit Auth
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard for authenticated users"""
    user_stats = scrobbler.get_user_stats(current_user.id)
    recent_scrobbles = scrobbler.get_recent_scrobbles(current_user.id, limit=10)
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.updated_at.desc()).limit(10).all()
    
    # Get active session
    active_session = ScrobbleSession.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    return render_template('dashboard.html', 
                         user_stats=user_stats,
                         recent_scrobbles=recent_scrobbles,
                         user_playlists=user_playlists,
                         active_session=active_session)

@app.route('/profile')
@require_login
def profile():
    """User profile and settings"""
    return render_template('profile.html', user=current_user)

@app.route('/setup-lastfm', methods=['POST'])
@require_login
def setup_lastfm():
    """Set up Last.fm credentials for user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'})
    
    # Authenticate with Last.fm
    session_key = scrobbler.authenticate_lastfm(username, password)
    
    if session_key:
        current_user.lastfm_username = username
        current_user.lastfm_session_key = session_key
        db.session.commit()
        return jsonify({'success': True, 'message': 'Last.fm account connected successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid Last.fm credentials'})

@app.route('/scrobble', methods=['POST'])
@require_login
def manual_scrobble():
    """Manual single track scrobble"""
    data = request.get_json()
    artist = data.get('artist')
    track = data.get('track')
    album = data.get('album', '')
    
    if not artist or not track:
        return jsonify({'success': False, 'message': 'Artist and track are required'})
    
    success, message = scrobbler.scrobble_track(current_user.id, artist, track, album)
    return jsonify({'success': success, 'message': message})

@app.route('/playlists')
@require_login
def playlists():
    """User playlists page"""
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.updated_at.desc()).all()
    community_playlists = db.session.query(Playlist, CommunityPlaylist)\
                                    .join(CommunityPlaylist)\
                                    .filter(CommunityPlaylist.featured_by_admin == True)\
                                    .limit(20).all()
    
    return render_template('playlists.html', 
                         user_playlists=user_playlists,
                         community_playlists=community_playlists)

@app.route('/create-playlist', methods=['POST'])
@require_login
def create_playlist():
    """Create new playlist"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    tracks = data.get('tracks', [])
    source_type = data.get('source_type', 'custom')
    is_public = data.get('is_public', False)
    
    if not name:
        return jsonify({'success': False, 'message': 'Playlist name is required'})
    
    playlist = Playlist(
        user_id=current_user.id,
        name=name,
        description=description,
        source_type=source_type,
        is_public=is_public
    )
    playlist.set_tracks(tracks)
    
    db.session.add(playlist)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Playlist created successfully',
        'playlist_id': playlist.id
    })

@app.route('/import-spotify-playlist', methods=['POST'])
@require_login
def import_spotify_playlist():
    """Import playlist from Spotify"""
    data = request.get_json()
    playlist_url = data.get('playlist_url')
    playlist_name = data.get('name')
    
    if not playlist_url:
        return jsonify({'success': False, 'message': 'Spotify playlist URL required'})
    
    # Extract playlist ID from URL
    try:
        if 'playlist/' in playlist_url:
            playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        else:
            playlist_id = playlist_url
        
        tracks, error = scrobbler.get_spotify_playlist(playlist_id)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        # Create playlist
        playlist = Playlist(
            user_id=current_user.id,
            name=playlist_name or f"Imported Spotify Playlist",
            source_type='spotify',
            source_id=playlist_id
        )
        playlist.set_tracks(tracks)
        
        db.session.add(playlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Imported {len(tracks)} tracks from Spotify',
            'playlist_id': playlist.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/import-deezer-playlist', methods=['POST'])
@require_login
def import_deezer_playlist():
    """Import playlist from Deezer"""
    data = request.get_json()
    playlist_url = data.get('playlist_url')
    playlist_name = data.get('name')
    
    if not playlist_url:
        return jsonify({'success': False, 'message': 'Deezer playlist URL required'})
    
    try:
        # Extract playlist ID from URL
        if 'playlist/' in playlist_url:
            playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        else:
            playlist_id = playlist_url
        
        tracks, error = scrobbler.get_deezer_playlist(playlist_id)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        # Create playlist
        playlist = Playlist(
            user_id=current_user.id,
            name=playlist_name or f"Imported Deezer Playlist",
            source_type='deezer',
            source_id=playlist_id
        )
        playlist.set_tracks(tracks)
        
        db.session.add(playlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Imported {len(tracks)} tracks from Deezer',
            'playlist_id': playlist.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/start-auto-scrobbling', methods=['POST'])
@require_login
def start_auto_scrobbling():
    """Start automatic scrobbling session"""
    data = request.get_json()
    playlist_id = data.get('playlist_id')
    interval_minutes = data.get('interval_minutes', 3)
    shuffle = data.get('shuffle', True)
    
    if not playlist_id:
        return jsonify({'success': False, 'message': 'Playlist ID required'})
    
    # Check if playlist exists and belongs to user
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
    if not playlist:
        return jsonify({'success': False, 'message': 'Playlist not found'})
    
    success, message = scrobbler.start_auto_scrobbling(
        current_user.id, 
        playlist_id, 
        interval_minutes, 
        shuffle
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/stop-auto-scrobbling', methods=['POST'])
@require_login
def stop_auto_scrobbling():
    """Stop automatic scrobbling session"""
    success, message = scrobbler.stop_auto_scrobbling(current_user.id)
    return jsonify({'success': success, 'message': message})

@app.route('/search-music')
@require_login
def search_music():
    """Search for music across platforms"""
    query = request.args.get('q', '')
    platform = request.args.get('platform', 'spotify')
    search_type = request.args.get('type', 'track')
    
    if not query:
        return jsonify({'results': []})
    
    try:
        if platform == 'spotify':
            results, error = scrobbler.search_spotify(query, search_type)
        elif platform == 'deezer':
            results, error = scrobbler.search_deezer(query, search_type)
        else:
            return jsonify({'error': 'Unsupported platform'})
        
        if error:
            return jsonify({'error': error})
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/community')
def community():
    """Community playlists page"""
    featured_playlists = db.session.query(Playlist, CommunityPlaylist)\
                                   .join(CommunityPlaylist)\
                                   .filter(CommunityPlaylist.featured_by_admin == True)\
                                   .order_by(CommunityPlaylist.likes_count.desc())\
                                   .limit(50).all()
    
    return render_template('community.html', featured_playlists=featured_playlists)

@app.route('/api/stats')
@require_login
def api_stats():
    """Get user statistics"""
    stats = scrobbler.get_user_stats(current_user.id)
    return jsonify(stats)

@app.route('/api/session-status')
@require_login
def api_session_status():
    """Get current scrobbling session status"""
    active_session = ScrobbleSession.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    if active_session:
        playlist = Playlist.query.get(active_session.playlist_id)
        return jsonify({
            'active': True,
            'playlist_name': playlist.name if playlist else 'Unknown',
            'interval_minutes': active_session.interval_minutes,
            'total_scrobbles': active_session.total_scrobbles,
            'started_at': active_session.started_at.isoformat() if active_session.started_at else None,
            'last_scrobble_at': active_session.last_scrobble_at.isoformat() if active_session.last_scrobble_at else None
        })
    else:
        return jsonify({'active': False})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal error: {error}")
    return render_template('500.html'), 500