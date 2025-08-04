#!/usr/bin/env python3
"""
Flask Web Server for Last.fm Scrobbler
Serves the interactive web interface
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import hashlib
import requests
import time
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Last.fm API credentials
API_KEY = '45905c9b4239a9ec7b245f8a3711e87b'
SHARED_SECRET = 'afcbf283834eaea726d3176d1ab946d0'
API_URL = 'http://ws.audioscrobbler.com/2.0/'

def generate_api_sig(params):
    """Generate API signature"""
    string = ''.join([f"{k}{params[k]}" for k in sorted(params)])
    string += SHARED_SECRET
    return hashlib.md5(string.encode('utf-8')).hexdigest()

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('.', 'index.html')

@app.route('/script.js')
def script():
    """Serve the JavaScript file"""
    return send_from_directory('.', 'script.js')

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Authenticate with Last.fm"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    params = {
        'method': 'auth.getMobileSession',
        'api_key': API_KEY,
        'username': username,
        'password': password,
    }
    params['api_sig'] = generate_api_sig(params)
    params['format'] = 'json'
    
    try:
        response = requests.post(API_URL, data=params, timeout=30)
        data = response.json()
        
        if 'session' in data:
            return jsonify({
                'success': True,
                'session_key': data['session']['key'],
                'username': username
            })
        else:
            return jsonify({
                'success': False,
                'error': data.get('message', 'Authentication failed')
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrobble', methods=['POST'])
def scrobble():
    """Scrobble a track"""
    data = request.json
    session_key = data.get('session_key')
    artist = data.get('artist')
    track = data.get('track')
    album = data.get('album', '')
    
    if not all([session_key, artist, track]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    timestamp = int(time.time())
    
    params = {
        'method': 'track.scrobble',
        'api_key': API_KEY,
        'artist': artist,
        'track': track,
        'timestamp': str(timestamp),
        'sk': session_key
    }
    
    if album:
        params['album'] = album
    
    params['api_sig'] = generate_api_sig(params)
    params['format'] = 'json'
    
    try:
        response = requests.post(API_URL, data=params, timeout=30)
        result = response.json()
        
        if 'scrobbles' in result:
            return jsonify({
                'success': True,
                'artist': artist,
                'track': track,
                'album': album,
                'timestamp': timestamp
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('message', 'Scrobble failed')
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'lastfm-scrobbler'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)