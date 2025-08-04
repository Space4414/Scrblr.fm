# GitHub Pages Setup Guide

## Creating Your GitHub Repository

### Step 1: Create New Repository
1. Go to https://github.com/new
2. Repository name: `lastfm-scrobbler` (or any name you prefer)
3. Description: `Interactive Last.fm Auto Scrobbler`
4. Make it **Public** (required for GitHub Pages)
5. Check "Add a README file"
6. Click "Create repository"

### Step 2: Upload Files
1. Click "uploading an existing file" or use Git
2. Upload these files from the `github_web` folder:
   - `index.html`
   - `style.css` 
   - `app.js`
3. Commit the changes

### Step 3: Enable GitHub Pages
1. Go to your repository Settings
2. Scroll to "Pages" section
3. Under "Source", select "Deploy from a branch"
4. Choose "main" branch and "/ (root)" folder
5. Click "Save"

### Step 4: Access Your Web App
- Your app will be available at: `https://yourusername.github.io/lastfm-scrobbler`
- It may take a few minutes to deploy

## Features of the GitHub Pages Version

### ✅ What Works
- **Beautiful responsive interface** with Taylor Swift themes
- **Single track scrobbling** with form inputs
- **Preset album loaders** (Tortured Poets, Midnights, Folklore, Evermore, Red, Classic Rock)
- **Playlist management** with custom track lists
- **Auto-scrobbling simulation** (visual feedback)
- **Scrobble history tracking** (local storage)
- **Mobile-friendly design** with animations

### ⚠️ GitHub Pages Limitations
Due to CORS (Cross-Origin Resource Sharing) restrictions:
- **Direct Last.fm API calls** may be blocked by browsers
- **Actual scrobbling** requires a server (like your Replit version)
- The app will work in **"demo mode"** showing simulated scrobbles

### 🔧 Workarounds for Full Functionality
1. **Use the Replit version** for actual scrobbling
2. **Install browser extension** to bypass CORS (advanced users)
3. **Run locally** with a local server

## Repository Structure
```
lastfm-scrobbler/
├── index.html          # Main web page
├── style.css           # Beautiful Taylor Swift-themed styles
├── app.js              # JavaScript functionality
└── README.md           # Repository description
```

## Customization Options

### Adding More Albums
Edit `app.js` and add new functions like:
```javascript
function loadYourAlbum() {
    const playlist = `Artist - Track - Album
    Another Artist - Another Track - Album`;
    document.getElementById('playlist').value = playlist;
    showStatus('Loaded Your Album', 'success');
}
```

### Changing Colors/Theme
Edit `style.css` to modify:
- Background gradients
- Button colors
- Card designs
- Animations

### Adding Features
- More preset playlists
- Different scrobbling intervals
- Export/import functionality
- Dark/light mode toggle

## Usage Instructions for Users

1. **Visit your GitHub Pages URL**
2. **Enter Last.fm credentials** (stored locally in browser)
3. **Choose an option:**
   - Scrobble single tracks manually
   - Load preset albums (Taylor Swift, Classic Rock, etc.)
   - Create custom playlists
   - Start auto-scrobbling simulation

## Demo Mode Features

Since actual scrobbling may be limited by CORS:
- **Visual feedback** shows what would be scrobbled
- **Local history** tracks simulated scrobbles
- **Full UI experience** for testing and demonstration
- **Perfect for showcasing** the interface design

The GitHub Pages version serves as a beautiful demo and interface, while your Replit version handles the actual Last.fm API integration!