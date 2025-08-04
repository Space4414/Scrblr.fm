# Last.fm Automatic Scrobbling Bot

A Python automation bot for continuous Last.fm music scrobbling with configurable timing and error handling.

## Features

- **Continuous Scrobbling**: Automatically scrobbles tracks to Last.fm at configurable intervals
- **Multiple Music Sources**: Supports local music files and streaming simulation
- **Duplicate Prevention**: Maintains track history to avoid duplicate scrobbles
- **Error Handling**: Robust retry logic for API failures and network issues
- **Configurable**: Easy configuration through INI file
- **Logging**: Comprehensive logging for monitoring and debugging
- **Authentication**: Secure Last.fm API authentication

## Requirements

- Python 3.6 or higher
- Last.fm API account and credentials
- Internet connection for API access

## Installation

1. Clone or download this project
2. Install required Python packages:
   ```bash
   pip install requests schedule
   ```

## Configuration

1. **Get Last.fm API Credentials**:
   - Go to https://www.last.fm/api/account/create
   - Create an API account to get your API key and secret
   - Note your Last.fm username and password

2. **Configure the Bot**:
   - Run the bot once to create a default `config.ini` file:
     ```bash
     python main.py
     ```
   - Edit `config.ini` with your credentials:
     ```ini
     [lastfm]
     api_key = your_actual_api_key
     api_secret = your_actual_api_secret
     username = your_lastfm_username
     password = your_lastfm_password
     ```

3. **Environment Variables** (optional):
   You can also set credentials via environment variables:
   ```bash
   export LASTFM_API_KEY="your_api_key"
   export LASTFM_API_SECRET="your_api_secret"
   export LASTFM_USERNAME="your_username"
   export LASTFM_PASSWORD="your_password"
   