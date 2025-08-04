# Universal Last.fm Scrobbler Discord Bot Setup Guide

This guide will help you set up the advanced Universal Last.fm Scrobbler Discord Bot with Spotify/Deezer integration, multi-user support, and community features.

## Prerequisites

1. **Discord Developer Account**: You need a Discord account to create a bot
2. **Discord Server**: You need a server where you have administrator permissions
3. **Last.fm Account**: Users need valid Last.fm credentials for scrobbling
4. **Optional**: Spotify API credentials for playlist importing
5. **Optional**: Deezer support works automatically for public playlists

## Step 1: Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give your bot a name (e.g., "Universal Scrobbler")
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Copy the bot token (you'll need this later)

## Step 2: Configure Bot Permissions

In the Bot section:
1. Enable "Message Content Intent" under Privileged Gateway Intents
2. Go to the "OAuth2" > "URL Generator" section
3. Select the following scopes:
   - `bot`
   - `applications.commands`
4. Select the following bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
   - Use External Emojis
   - Attach Files

## Step 3: Invite Bot to Your Server

1. Copy the generated URL from the OAuth2 section
2. Open the URL in your browser
3. Select your Discord server
4. Click "Authorize"

## Step 4: Set Up Environment Variables

### Required Variables
```bash
DISCORD_TOKEN=your_discord_bot_token_here
```

### Optional Variables (for enhanced features)
```bash
# Default user (backwards compatibility)
LASTFM_USERNAME=default_lastfm_username
LASTFM_PASSWORD=default_lastfm_password

# Spotify integration (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

To set environment variables in Replit:
1. Click on the "Secrets" tab in the left sidebar
2. Add each variable with its corresponding value

### Getting Spotify API Credentials (Optional)
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy the Client ID and Client Secret
4. Add them as environment variables

## Step 5: Run the Bot

1. Execute the Discord bot script:
   ```bash
   python discord_scrobbler_bot.py
   ```

2. You should see a message indicating the bot is online with feature information

## Universal Scrobbler Commands

### 🔐 Authentication
- `!login "username" "password"` - Authenticate with your Last.fm account

### 🎵 Basic Scrobbling
- `!scrobble "Artist" "Track" "Album"` - Scrobble a single track
- `!recent 10` - Show your recent scrobbles
- `!status` - Show your stats and current status

### 📋 Playlist Management
- `!create "My Playlist" "Artist1 - Track1" "Artist2 - Track2"` - Create custom playlist
- `!playlists` - List your playlists
- `!swift` - Load Taylor Swift's Tortured Poets Department album

### 🔗 Platform Integration
- `!spotify "playlist_url" "My Playlist"` - Import Spotify playlist
- `!deezer "playlist_url" "My Playlist"` - Import Deezer playlist
- `!search spotify "taylor swift"` - Search Spotify for tracks
- `!search deezer "daft punk"` - Search Deezer for tracks

### 🤖 Auto-Scrobbling
- `!auto "My Playlist" 5 true` - Start auto-scrobbling (5min intervals, shuffle on)
- `!stop` - Stop auto-scrobbling

### 🌟 Community Features
- `!share "My Playlist"` - Share playlist with community
- `!community` - Browse community playlists
- `!copy 1 "My Copy"` - Copy community playlist by number
- `!like 1` - Like a community playlist

### ℹ️ Help
- `!commands` - Show all commands with detailed explanations

## Usage Examples

### Multi-User Setup
Each user authenticates individually:
```
!login "your_username" "your_password"
!status  # Check your personal stats
```

### Import Spotify Playlist
```
!login "your_username" "your_password"
!spotify "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" "Top Hits"
!auto "Top Hits" 3 true  # Start scrobbling every 3 minutes with shuffle
```

### Import Deezer Playlist
```
!deezer "https://www.deezer.com/playlist/1234567890" "French Hits"
!auto "French Hits" 5 false  # Start scrobbling every 5 minutes in order
```

### Create Custom Playlist
```
!create "My Mix" "Taylor Swift - Anti-Hero" "The Weeknd - Blinding Lights" "Dua Lipa - Levitating"
!auto "My Mix" 2 true
```

### Community Interaction
```
!share "My Mix"  # Share your playlist
!community      # Browse what others shared
!copy 1 "Awesome Mix"  # Copy the first community playlist
!like 1         # Like a community playlist
```

### Platform Search
```
!search spotify "taylor swift folklore"
!search deezer "radiohead ok computer"
```

## Advanced Features

### Multi-User Support
- Each Discord user maintains their own Last.fm session
- Personal playlists, statistics, and preferences
- Individual auto-scrobbling sessions

### Platform Integration
- **Spotify**: Requires API credentials for full functionality
- **Deezer**: Works automatically for public playlists
- **Universal Search**: Find music across platforms

### Community System
- Share playlists with other server members
- Like and copy community playlists
- Featured playlists based on popularity

### Auto-Scrobbling Engine
- Customizable intervals (1-60 minutes)
- Shuffle or sequential playback
- Multiple concurrent sessions per server
- Background processing with automatic management

## Troubleshooting

### Bot Not Responding
- Check that the bot token is correct
- Ensure the bot has proper permissions in your Discord server
- Verify that "Message Content Intent" is enabled

### User Authentication Issues
- Each user must authenticate with `!login` command
- Verify Last.fm credentials are correct
- Check console output for authentication errors

### Platform Integration Issues
- **Spotify**: Ensure API credentials are set correctly
- **Deezer**: Only public playlists can be imported
- Check playlist URLs are valid and accessible

### Auto-Scrobbling Not Working
- Verify user is authenticated with `!login`
- Check that playlist exists with `!playlists`
- Ensure playlist has tracks
- Check console output for scrobbling errors

### Community Features Not Working
- Community playlists are saved locally in `community_playlists.json`
- File permissions may prevent saving/loading
- Check console output for file system errors

## Security Notes

- Keep your Discord bot token secret
- Users authenticate individually with their own Last.fm credentials
- Spotify credentials are only used for playlist importing, not stored per user
- Use environment variables for all sensitive information

## Performance Considerations

- Bot supports multiple concurrent auto-scrobbling sessions
- Background task runs every minute to check all active sessions
- Community playlist data is persisted to JSON file
- Memory usage scales with number of active users and playlists

## Development Features

### Logging
- Comprehensive logging for debugging
- Auto-scrobbling activity is logged
- Error handling with user-friendly messages

### Data Persistence
- User sessions maintained in memory during bot runtime
- Community playlists saved to `community_playlists.json`
- Statistics calculated in real-time

### Error Handling
- Graceful handling of API failures
- User-friendly error messages
- Automatic retry logic for network issues

## Support

If you encounter issues:
1. Check the console output for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure the bot has the necessary Discord permissions
4. Test with simple commands first before using advanced features
5. Check individual user authentication with `!login`

## Limitations

- Deezer integration limited to public playlists without API credentials
- Spotify requires API credentials for full functionality
- User sessions are not persistent across bot restarts
- Rate limits apply from Last.fm, Spotify, and Deezer APIs

---

**Note**: This bot supports multiple users and includes advanced features. Please respect all platform terms of service and API rate limits. The bot is designed for community use while maintaining individual user privacy and preferences.