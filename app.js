// Last.fm Auto Scrobbler - GitHub Pages Version
const API_KEY = '45905c9b4239a9ec7b245f8a3711e87b';
const SHARED_SECRET = 'afcbf283834eaea726d3176d1ab946d0';
const API_URL = 'https://ws.audioscrobbler.com/2.0/';

let sessionKey = null;
let scrobbleHistory = [];
let isAutoScrobbling = false;
let autoScrobbleInterval = null;
let currentPlaylist = [];
let scrobbleCount = 0;

// MD5 hash function for signature generation
function md5(string) {
    function rotateLeft(value, amount) {
        var lbits = (value << amount) | (value >>> (32 - amount));
        return lbits;
    }
    
    function addUnsigned(x, y) {
        var x4 = (x & 0x40000000);
        var y4 = (y & 0x40000000);
        var x8 = (x & 0x80000000);
        var y8 = (y & 0x80000000);
        var result = (x & 0x3FFFFFFF) + (y & 0x3FFFFFFF);
        if (x4 & y4) {
            return (result ^ 0x80000000 ^ x8 ^ y8);
        }
        if (x4 | y4) {
            if (result & 0x40000000) {
                return (result ^ 0xC0000000 ^ x8 ^ y8);
            } else {
                return (result ^ 0x40000000 ^ x8 ^ y8);
            }
        } else {
            return (result ^ x8 ^ y8);
        }
    }
    
    function convertToWordArray(string) {
        var wordArray = Array();
        var messageLength = string.length;
        var numberOfWords = (((messageLength + 8) - ((messageLength + 8) % 64)) / 64) + 1;
        var numberOfBits = numberOfWords * 64;
        var arrayOfWords = Array(numberOfWords - 1);
        var bytePosition = 0;
        var byteCount = 0;
        while (byteCount < messageLength) {
            wordCount = (byteCount - (byteCount % 4)) / 4;
            bytePosition = (byteCount % 4) * 8;
            arrayOfWords[wordCount] = (arrayOfWords[wordCount] | (string.charCodeAt(byteCount) << bytePosition));
            byteCount++;
        }
        wordCount = (byteCount - (byteCount % 4)) / 4;
        bytePosition = (byteCount % 4) * 8;
        arrayOfWords[wordCount] = arrayOfWords[wordCount] | (0x80 << bytePosition);
        arrayOfWords[numberOfWords - 2] = messageLength << 3;
        arrayOfWords[numberOfWords - 1] = messageLength >>> 29;
        return arrayOfWords;
    }
    
    function wordToHex(value) {
        var wordToHexValue = "", wordToHexValueTemp = "", byte, count;
        for (count = 0; count <= 3; count++) {
            byte = (value >>> (count * 8)) & 255;
            wordToHexValueTemp = "0" + byte.toString(16);
            wordToHexValue = wordToHexValue + wordToHexValueTemp.substr(wordToHexValueTemp.length - 2, 2);
        }
        return wordToHexValue;
    }
    
    function F(x, y, z) { return (x & y) | ((~x) & z); }
    function G(x, y, z) { return (x & z) | (y & (~z)); }
    function H(x, y, z) { return (x ^ y ^ z); }
    function I(x, y, z) { return (y ^ (x | (~z))); }
    
    function FF(a, b, c, d, x, s, ac) {
        a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
        return addUnsigned(rotateLeft(a, s), b);
    }
    
    function GG(a, b, c, d, x, s, ac) {
        a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
        return addUnsigned(rotateLeft(a, s), b);
    }
    
    function HH(a, b, c, d, x, s, ac) {
        a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
        return addUnsigned(rotateLeft(a, s), b);
    }
    
    function II(a, b, c, d, x, s, ac) {
        a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
        return addUnsigned(rotateLeft(a, s), b);
    }
    
    var x = Array();
    var k, AA, BB, CC, DD, a, b, c, d;
    var S11 = 7, S12 = 12, S13 = 17, S14 = 22;
    var S21 = 5, S22 = 9, S23 = 14, S24 = 20;
    var S31 = 4, S32 = 11, S33 = 16, S34 = 23;
    var S41 = 6, S42 = 10, S43 = 15, S44 = 21;
    
    string = string.replace(/\r\n/g, "\n");
    x = convertToWordArray(string);
    a = 0x67452301; b = 0xEFCDAB89; c = 0x98BADCFE; d = 0x10325476;
    
    for (k = 0; k < x.length; k += 16) {
        AA = a; BB = b; CC = c; DD = d;
        a = FF(a, b, c, d, x[k + 0], S11, 0xD76AA478);
        d = FF(d, a, b, c, x[k + 1], S12, 0xE8C7B756);
        c = FF(c, d, a, b, x[k + 2], S13, 0x242070DB);
        b = FF(b, c, d, a, x[k + 3], S14, 0xC1BDCEEE);
        a = FF(a, b, c, d, x[k + 4], S11, 0xF57C0FAF);
        d = FF(d, a, b, c, x[k + 5], S12, 0x4787C62A);
        c = FF(c, d, a, b, x[k + 6], S13, 0xA8304613);
        b = FF(b, c, d, a, x[k + 7], S14, 0xFD469501);
        a = FF(a, b, c, d, x[k + 8], S11, 0x698098D8);
        d = FF(d, a, b, c, x[k + 9], S12, 0x8B44F7AF);
        c = FF(c, d, a, b, x[k + 10], S13, 0xFFFF5BB1);
        b = FF(b, c, d, a, x[k + 11], S14, 0x895CD7BE);
        a = FF(a, b, c, d, x[k + 12], S11, 0x6B901122);
        d = FF(d, a, b, c, x[k + 13], S12, 0xFD987193);
        c = FF(c, d, a, b, x[k + 14], S13, 0xA679438E);
        b = FF(b, c, d, a, x[k + 15], S14, 0x49B40821);
        a = GG(a, b, c, d, x[k + 1], S21, 0xF61E2562);
        d = GG(d, a, b, c, x[k + 6], S22, 0xC040B340);
        c = GG(c, d, a, b, x[k + 11], S23, 0x265E5A51);
        b = GG(b, c, d, a, x[k + 0], S24, 0xE9B6C7AA);
        a = GG(a, b, c, d, x[k + 5], S21, 0xD62F105D);
        d = GG(d, a, b, c, x[k + 10], S22, 0x2441453);
        c = GG(c, d, a, b, x[k + 15], S23, 0xD8A1E681);
        b = GG(b, c, d, a, x[k + 4], S24, 0xE7D3FBC8);
        a = GG(a, b, c, d, x[k + 9], S21, 0x21E1CDE6);
        d = GG(d, a, b, c, x[k + 14], S22, 0xC33707D6);
        c = GG(c, d, a, b, x[k + 3], S23, 0xF4D50D87);
        b = GG(b, c, d, a, x[k + 8], S24, 0x455A14ED);
        a = GG(a, b, c, d, x[k + 13], S21, 0xA9E3E905);
        d = GG(d, a, b, c, x[k + 2], S22, 0xFCEFA3F8);
        c = GG(c, d, a, b, x[k + 7], S23, 0x676F02D9);
        b = GG(b, c, d, a, x[k + 12], S24, 0x8D2A4C8A);
        a = HH(a, b, c, d, x[k + 5], S31, 0xFFFA3942);
        d = HH(d, a, b, c, x[k + 8], S32, 0x8771F681);
        c = HH(c, d, a, b, x[k + 11], S33, 0x6D9D6122);
        b = HH(b, c, d, a, x[k + 14], S34, 0xFDE5380C);
        a = HH(a, b, c, d, x[k + 1], S31, 0xA4BEEA44);
        d = HH(d, a, b, c, x[k + 4], S32, 0x4BDECFA9);
        c = HH(c, d, a, b, x[k + 7], S33, 0xF6BB4B60);
        b = HH(b, c, d, a, x[k + 10], S34, 0xBEBFBC70);
        a = HH(a, b, c, d, x[k + 13], S31, 0x289B7EC6);
        d = HH(d, a, b, c, x[k + 0], S32, 0xEAA127FA);
        c = HH(c, d, a, b, x[k + 3], S33, 0xD4EF3085);
        b = HH(b, c, d, a, x[k + 6], S34, 0x4881D05);
        a = HH(a, b, c, d, x[k + 9], S31, 0xD9D4D039);
        d = HH(d, a, b, c, x[k + 12], S32, 0xE6DB99E5);
        c = HH(c, d, a, b, x[k + 15], S33, 0x1FA27CF8);
        b = HH(b, c, d, a, x[k + 2], S34, 0xC4AC5665);
        a = II(a, b, c, d, x[k + 0], S41, 0xF4292244);
        d = II(d, a, b, c, x[k + 7], S42, 0x432AFF97);
        c = II(c, d, a, b, x[k + 14], S43, 0xAB9423A7);
        b = II(b, c, d, a, x[k + 5], S44, 0xFC93A039);
        a = II(a, b, c, d, x[k + 12], S41, 0x655B59C3);
        d = II(d, a, b, c, x[k + 3], S42, 0x8F0CCC92);
        c = II(c, d, a, b, x[k + 10], S43, 0xFFEFF47D);
        b = II(b, c, d, a, x[k + 1], S44, 0x85845DD1);
        a = II(a, b, c, d, x[k + 8], S41, 0x6FA87E4F);
        d = II(d, a, b, c, x[k + 15], S42, 0xFE2CE6E0);
        c = II(c, d, a, b, x[k + 6], S43, 0xA3014314);
        b = II(b, c, d, a, x[k + 13], S44, 0x4E0811A1);
        a = II(a, b, c, d, x[k + 4], S41, 0xF7537E82);
        d = II(d, a, b, c, x[k + 11], S42, 0xBD3AF235);
        c = II(c, d, a, b, x[k + 2], S43, 0x2AD7D2BB);
        b = II(b, c, d, a, x[k + 9], S44, 0xEB86D391);
        a = addUnsigned(a, AA);
        b = addUnsigned(b, BB);
        c = addUnsigned(c, CC);
        d = addUnsigned(d, DD);
    }
    
    var temp = wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d);
    return temp.toLowerCase();
}

// Generate API signature
function generateApiSig(params) {
    const sorted = Object.keys(params).sort();
    let string = '';
    for (const key of sorted) {
        string += key + params[key];
    }
    string += SHARED_SECRET;
    return md5(string);
}

// Show status message
function showStatus(message, type = 'info') {
    const statusSection = document.getElementById('statusSection');
    const statusText = document.getElementById('statusText');
    
    statusSection.style.display = 'block';
    statusText.innerHTML = message;
    
    statusSection.className = 'status-box';
    if (type === 'error') {
        statusSection.style.borderColor = '#f44336';
        statusSection.style.background = 'rgba(244, 67, 54, 0.1)';
    } else if (type === 'success') {
        statusSection.style.borderColor = '#4caf50';
        statusSection.style.background = 'rgba(76, 175, 80, 0.1)';
    }
}

// Authenticate with Last.fm
async function authenticate() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showStatus('Please enter your Last.fm username and password', 'error');
        return;
    }
    
    showStatus('Authenticating with Last.fm...', 'info');
    
    const params = {
        method: 'auth.getMobileSession',
        api_key: API_KEY,
        username: username,
        password: password
    };
    
    params.api_sig = generateApiSig(params);
    params.format = 'json';
    
    try {
        const formData = new FormData();
        Object.keys(params).forEach(key => formData.append(key, params[key]));
        
        const response = await fetch(`https://cors-anywhere.herokuapp.com/${API_URL}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.session) {
            sessionKey = data.session.key;
            showStatus(`Successfully authenticated as ${username}`, 'success');
            
            const authStatus = document.getElementById('authStatus');
            authStatus.className = 'alert alert-success';
            authStatus.style.display = 'block';
            authStatus.innerHTML = `<i class="fas fa-check-circle"></i> Connected as <strong>${username}</strong>`;
        } else {
            // Try direct API call for GitHub Pages
            const directResponse = await fetch(API_URL, {
                method: 'POST',
                body: formData,
                mode: 'no-cors'
            });
            
            // Since we can't read the response in no-cors mode, we'll assume success
            // and let the user know they need to test by scrobbling
            showStatus('Authentication attempted. Try scrobbling a track to test.', 'info');
        }
    } catch (error) {
        showStatus(`Network error: Due to CORS restrictions, direct authentication may not work on GitHub Pages. You can still try scrobbling with your credentials.`, 'info');
        
        // For GitHub Pages, we'll store the credentials locally
        sessionKey = 'github_pages_mode';
        localStorage.setItem('lastfm_username', username);
        localStorage.setItem('lastfm_password', password);
        
        const authStatus = document.getElementById('authStatus');
        authStatus.className = 'alert alert-info';
        authStatus.style.display = 'block';
        authStatus.innerHTML = `<i class="fas fa-info-circle"></i> GitHub Pages Mode - credentials stored locally for ${username}`;
    }
}

// Scrobble a single track
async function scrobbleSingle() {
    const artist = document.getElementById('singleArtist').value;
    const track = document.getElementById('singleTrack').value;
    const album = document.getElementById('singleAlbum').value;
    
    if (!artist || !track) {
        showStatus('Please enter artist and track name', 'error');
        return;
    }
    
    const success = await scrobbleTrack(artist, track, album);
    
    if (success) {
        document.getElementById('singleArtist').value = '';
        document.getElementById('singleTrack').value = '';
        document.getElementById('singleAlbum').value = '';
    }
}

// Scrobble a track
async function scrobbleTrack(artist, track, album = '') {
    if (!sessionKey && !localStorage.getItem('lastfm_username')) {
        showStatus('Please authenticate first', 'error');
        return false;
    }
    
    const timestamp = Math.floor(Date.now() / 1000);
    
    const params = {
        method: 'track.scrobble',
        api_key: API_KEY,
        artist: artist,
        track: track,
        timestamp: timestamp.toString(),
        sk: sessionKey === 'github_pages_mode' ? 'temp_session' : sessionKey
    };
    
    if (album) {
        params.album = album;
    }
    
    // For GitHub Pages mode, add auth params
    if (sessionKey === 'github_pages_mode') {
        params.username = localStorage.getItem('lastfm_username');
        params.password = localStorage.getItem('lastfm_password');
        delete params.sk;
    }
    
    params.api_sig = generateApiSig(params);
    params.format = 'json';
    
    try {
        const formData = new FormData();
        Object.keys(params).forEach(key => formData.append(key, params[key]));
        
        // For GitHub Pages, we'll simulate the scrobble since CORS prevents actual API calls
        if (sessionKey === 'github_pages_mode') {
            // Simulate successful scrobble
            scrobbleCount++;
            document.getElementById('scrobbleCount').innerHTML = `Total scrobbles: ${scrobbleCount}`;
            
            // Add to history
            scrobbleHistory.unshift({
                artist: artist,
                track: track,
                album: album,
                timestamp: timestamp
            });
            
            // Keep only last 20
            if (scrobbleHistory.length > 20) {
                scrobbleHistory = scrobbleHistory.slice(0, 20);
            }
            
            updateHistory();
            
            const albumText = album ? ` • ${album}` : '';
            showStatus(`Simulated scrobble: ${artist} - ${track}${albumText} (GitHub Pages mode - actual scrobbling requires server)`, 'success');
            
            return true;
        }
        
        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.scrobbles) {
            scrobbleCount++;
            document.getElementById('scrobbleCount').innerHTML = `Total scrobbles: ${scrobbleCount}`;
            
            // Add to history
            scrobbleHistory.unshift({
                artist: artist,
                track: track,
                album: album,
                timestamp: timestamp
            });
            
            // Keep only last 20
            if (scrobbleHistory.length > 20) {
                scrobbleHistory = scrobbleHistory.slice(0, 20);
            }
            
            updateHistory();
            
            const albumText = album ? ` • ${album}` : '';
            showStatus(`Scrobbled: ${artist} - ${track}${albumText}`, 'success');
            
            return true;
        } else {
            showStatus(`Scrobble failed: ${data.message || 'Unknown error'}`, 'error');
            return false;
        }
    } catch (error) {
        showStatus(`Network error: ${error.message}`, 'error');
        return false;
    }
}

// Update history display
function updateHistory() {
    const historyDiv = document.getElementById('scrobbleHistory');
    
    if (scrobbleHistory.length === 0) {
        historyDiv.innerHTML = '<p class="text-muted">No scrobbles yet</p>';
        return;
    }
    
    let html = '';
    scrobbleHistory.forEach((item, index) => {
        const albumText = item.album ? ` • ${item.album}` : '';
        const timeAgo = getTimeAgo(item.timestamp);
        html += `
            <div class="history-item">
                <strong>${item.artist}</strong> - <em>${item.track}</em>${albumText}
                <br><small class="text-muted">${timeAgo}</small>
            </div>
        `;
    });
    
    historyDiv.innerHTML = html;
}

// Get time ago string
function getTimeAgo(timestamp) {
    const now = Math.floor(Date.now() / 1000);
    const diff = now - timestamp;
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return `${Math.floor(diff / 86400)} days ago`;
}

// Load preset playlists
function loadTorturedPoets() {
    const playlist = `Taylor Swift - Fortnight - The Tortured Poets Department
Taylor Swift - The Tortured Poets Department - The Tortured Poets Department
Taylor Swift - My Boy Only Breaks His Favorite Toys - The Tortured Poets Department
Taylor Swift - So Long, London - The Tortured Poets Department
Taylor Swift - But Daddy I Love Him - The Tortured Poets Department
Taylor Swift - Fresh Out the Slammer - The Tortured Poets Department
Taylor Swift - Florida!!! - The Tortured Poets Department
Taylor Swift - Guilty as Sin? - The Tortured Poets Department
Taylor Swift - Who's Afraid of Little Old Me? - The Tortured Poets Department
Taylor Swift - I Can Fix Him (No Really I Can) - The Tortured Poets Department
Taylor Swift - loml - The Tortured Poets Department
Taylor Swift - I Can Do It With a Broken Heart - The Tortured Poets Department
Taylor Swift - The Smallest Man Who Ever Lived - The Tortured Poets Department
Taylor Swift - The Alchemy - The Tortured Poets Department
Taylor Swift - Clara Bow - The Tortured Poets Department
Taylor Swift - The Black Dog - The Tortured Poets Department
Taylor Swift - imgonnagetyouback - The Tortured Poets Department
Taylor Swift - The Albatross - The Tortured Poets Department
Taylor Swift - Chloe or Sam or Sophia or Marcus - The Tortured Poets Department
Taylor Swift - How Did It End? - The Tortured Poets Department
Taylor Swift - So High School - The Tortured Poets Department
Taylor Swift - I Hate It Here - The Tortured Poets Department
Taylor Swift - thanK you aIMee - The Tortured Poets Department
Taylor Swift - I Look in People's Windows - The Tortured Poets Department
Taylor Swift - The Prophecy - The Tortured Poets Department
Taylor Swift - Cassandra - The Tortured Poets Department
Taylor Swift - Peter - The Tortured Poets Department
Taylor Swift - The Bolter - The Tortured Poets Department
Taylor Swift - Robin - The Tortured Poets Department
Taylor Swift - The Manuscript - The Tortured Poets Department`;
    
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded The Tortured Poets Department (30 tracks)', 'success');
}

function loadMidnights() {
    const playlist = `Taylor Swift - Lavender Haze - Midnights
Taylor Swift - Maroon - Midnights
Taylor Swift - Anti-Hero - Midnights
Taylor Swift - Snow On The Beach - Midnights
Taylor Swift - You're On Your Own, Kid - Midnights
Taylor Swift - Midnight Rain - Midnights
Taylor Swift - Question...? - Midnights
Taylor Swift - Vigilante Shit - Midnights
Taylor Swift - Bejeweled - Midnights
Taylor Swift - Labyrinth - Midnights
Taylor Swift - Karma - Midnights
Taylor Swift - Sweet Nothing - Midnights
Taylor Swift - Mastermind - Midnights`;
    
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded Midnights (13 tracks)', 'success');
}

function loadFolklore() {
    const playlist = `Taylor Swift - the 1 - folklore
Taylor Swift - cardigan - folklore
Taylor Swift - the last great american dynasty - folklore
Taylor Swift - exile - folklore
Taylor Swift - my tears ricochet - folklore
Taylor Swift - mirrorball - folklore
Taylor Swift - seven - folklore
Taylor Swift - august - folklore
Taylor Swift - this is me trying - folklore
Taylor Swift - illicit affairs - folklore
Taylor Swift - invisible string - folklore
Taylor Swift - mad woman - folklore
Taylor Swift - epiphany - folklore
Taylor Swift - betty - folklore
Taylor Swift - peace - folklore
Taylor Swift - hoax - folklore`;
    
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded folklore (16 tracks)', 'success');
}

function loadEvermore() {
    const playlist = `Taylor Swift - willow - evermore
Taylor Swift - champagne problems - evermore
Taylor Swift - gold rush - evermore
Taylor Swift - 'tis the damn season - evermore
Taylor Swift - tolerate it - evermore
Taylor Swift - no body, no crime - evermore
Taylor Swift - happiness - evermore
Taylor Swift - dorothea - evermore
Taylor Swift - coney island - evermore
Taylor Swift - ivy - evermore
Taylor Swift - cowboy like me - evermore
Taylor Swift - long story short - evermore
Taylor Swift - marjorie - evermore
Taylor Swift - closure - evermore
Taylor Swift - evermore - evermore`;
    
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded evermore (15 tracks)', 'success');
}

function loadRed() {
    const playlist = `Taylor Swift - State of Grace (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Red (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Treacherous (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - I Knew You Were Trouble (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - All Too Well (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - 22 (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - I Almost Do (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - We Are Never Ever Getting Back Together (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Stay Stay Stay (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - The Last Time (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Holy Ground (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Sad Beautiful Tragic (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - The Lucky One (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Everything Has Changed (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Starlight (Taylor's Version) - Red (Taylor's Version)
Taylor Swift - Begin Again (Taylor's Version) - Red (Taylor's Version)`;
    
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded Red Taylor\'s Version (16 tracks)', 'success');
}

function loadClassicRock() {
    const playlist = `The Beatles - Hey Jude - The Beatles 1967-1970
Queen - Bohemian Rhapsody - A Night at the Opera
Pink Floyd - Comfortably Numb - The Wall
Led Zeppelin - Stairway to Heaven - Led Zeppelin IV
The Rolling Stones - Paint It Black - Aftermath
David Bowie - Space Oddity - David Bowie
The Who - Baba O'Riley - Who's Next
Fleetwood Mac - Go Your Own Way - Rumours
Eagles - Hotel California - Hotel California
AC/DC - Back in Black - Back in Black`;
    
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded Classic Rock Hits (10 tracks)', 'success');
}

// Parse playlist
function parsePlaylist() {
    const playlistText = document.getElementById('playlist').value;
    const lines = playlistText.split('\n').filter(line => line.trim());
    
    currentPlaylist = [];
    
    lines.forEach(line => {
        const parts = line.split(' - ');
        if (parts.length >= 2) {
            const track = {
                artist: parts[0].trim(),
                track: parts[1].trim(),
                album: parts.length > 2 ? parts[2].trim() : ''
            };
            currentPlaylist.push(track);
        }
    });
    
    return currentPlaylist.length > 0;
}

// Start auto scrobbling
function startAutoScrobbling() {
    if (!sessionKey && !localStorage.getItem('lastfm_username')) {
        showStatus('Please authenticate first', 'error');
        return;
    }
    
    if (!parsePlaylist()) {
        showStatus('Please enter a valid playlist', 'error');
        return;
    }
    
    if (isAutoScrobbling) {
        showStatus('Auto scrobbling is already running', 'error');
        return;
    }
    
    const interval = parseInt(document.getElementById('interval').value) || 3;
    
    isAutoScrobbling = true;
    showStatus(`Auto scrobbling started (${currentPlaylist.length} tracks, every ${interval} minutes)`, 'success');
    
    // Scrobble first track immediately
    autoScrobbleNext();
    
    // Set up interval
    autoScrobbleInterval = setInterval(autoScrobbleNext, interval * 60 * 1000);
}

// Stop auto scrobbling
function stopAutoScrobbling() {
    if (!isAutoScrobbling) {
        showStatus('Auto scrobbling is not running', 'error');
        return;
    }
    
    isAutoScrobbling = false;
    clearInterval(autoScrobbleInterval);
    
    showStatus('Auto scrobbling stopped', 'success');
    document.getElementById('currentTrack').innerHTML = '';
}

// Auto scrobble next track
async function autoScrobbleNext() {
    if (!isAutoScrobbling || currentPlaylist.length === 0) {
        return;
    }
    
    // Pick random track
    const track = currentPlaylist[Math.floor(Math.random() * currentPlaylist.length)];
    
    document.getElementById('currentTrack').innerHTML = `Now playing: ${track.artist} - ${track.track}`;
    
    await scrobbleTrack(track.artist, track.track, track.album);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateHistory();
    
    // Check for stored credentials
    if (localStorage.getItem('lastfm_username')) {
        document.getElementById('username').value = localStorage.getItem('lastfm_username');
        showStatus('Previous credentials found. Click Connect to authenticate.', 'info');
    }
});