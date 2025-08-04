import hashlib
import requests
import time

API_KEY = '45905c9b4239a9ec7b245f8a3711e87b'
SHARED_SECRET = 'afcbf283834eaea726d3176d1ab946d0'
TOKEN = 'FbdqsatHpFkblIMAugO-OzWKmFP6iiyG'

def generate_api_sig(params):
    string = ''.join([f"{k}{params[k]}" for k in sorted(params)])
    string += SHARED_SECRET
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def get_session_key():
    params = {
        'method': 'auth.getSession',
        'api_key': API_KEY,
        'token': TOKEN,
    }
    params['api_sig'] = generate_api_sig(params)
    params['format'] = 'json'
    
    response = requests.get('http://ws.audioscrobbler.com/2.0/', params=params)
    data = response.json()
    
    if 'session' in data:
        print("✅ Session key obtained:", data['session']['key'])
        return data['session']['key']
    else:
        print("❌ Error getting session key:", data)
        return None

def scrobble_track(session_key, artist, track, timestamp):
    params = {
        'method': 'track.scrobble',
        'api_key': API_KEY,
        'artist': artist,
        'track': track,
        'timestamp': str(timestamp),
        'sk': session_key,
        'format': 'json'
    }
    params['api_sig'] = generate_api_sig(params)
    
    response = requests.post('http://ws.audioscrobbler.com/2.0/', data=params)
    print("🎧 Scrobble response:", response.json())

if __name__ == "__main__":
    session_key = get_session_key()
    if session_key:
        # Example track list to scrobble
        tracks = [
            {'artist': 'Coldplay', 'track': 'Yellow', 'timestamp': int(time.time()) - 600},
            {'artist': 'Imagine Dragons', 'track': 'Believer', 'timestamp': int(time.time()) - 300}
        ]
        for t in tracks:
            scrobble_track(session_key, t['artist'], t['track'], t['timestamp'])
            time.sleep(1)  # Avoid hammering API