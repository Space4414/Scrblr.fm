# Universal Last.fm Scrobbler Platform

## Overview

A comprehensive web-based platform for automatic Last.fm scrobbling with multiple interfaces and universal music platform integration. Users can scrobble from Spotify, Deezer, custom playlists, and even through Discord bot commands. Features include customizable intervals, community playlist sharing, and complete user management with PostgreSQL database backend.

## User Preferences

Preferred communication style: Simple, everyday language.
Feature requests: Stop/start scrobbling controls, custom intervals, universal platform support, public community features for internet fame.

## System Architecture

### Core Platform Components

**Universal Scrobbler (universal_scrobbler.py)**
- Central scrobbling engine with Last.fm API integration
- Multi-threaded auto-scrobbling sessions management
- Spotify and Deezer platform integration with search capabilities
- User statistics tracking and duplicate prevention
- Background session workers for continuous operation

**Web Application (main.py, app.py, routes.py)**
- Flask-based web interface with Replit authentication
- RESTful API endpoints for playlist management
- Real-time session status and user dashboard
- Community features for public playlist sharing

**Database Models (models.py)**
- PostgreSQL database with comprehensive user management
- Playlist storage with multiple source types (Spotify, Deezer, custom)
- Scrobble history tracking with analytics
- Community playlist system with likes and usage stats

**Authentication System (replit_auth.py)**
- Replit OAuth integration for seamless user login
- Session management with browser fingerprinting
- Secure credential storage for Last.fm accounts

**Legacy Interfaces**
- Discord bot integration for server-based scrobbling
- Standalone 24/7 scrobbler for continuous operation
- GitHub Pages demo version for public showcase

### Platform Features

**Universal Music Platform Integration**
- Spotify playlist import with full track metadata
- Deezer playlist support for European users
- Universal search across multiple platforms
- Custom playlist creation with manual track entry

**Scrobbling Controls**
- Start/stop functionality with user-controlled intervals (1-60 minutes)
- Shuffle mode and sequential playback options
- Real-time session monitoring and statistics
- Individual track scrobbling for immediate updates

**Community Features**
- Public playlist sharing and discovery
- Featured playlists curated by community engagement
- Like system and usage statistics
- Category-based playlist browsing

**User Management**
- Comprehensive user profiles with Last.fm integration
- Personal statistics and listening analytics
- Privacy controls and data management options
- Multi-platform credential management

### Data Architecture

**PostgreSQL Database Schema**
- Users table with OAuth and Last.fm credentials
- Playlists with JSON track storage and metadata
- Scrobble history with source tracking and analytics
- Community engagement metrics and featured content
- Session management for active scrobbling tracking

**Security & Privacy**
- Encrypted credential storage for external APIs
- User data isolation and privacy controls
- Secure session management with browser fingerprinting
- Optional public profile and statistics sharing

## External Dependencies

### Core Python Packages
- **Flask**: Web framework for the main application interface
- **Flask-SQLAlchemy**: Database ORM for PostgreSQL integration
- **Flask-Login**: User session management and authentication
- **Flask-Dance**: OAuth integration for Replit authentication
- **requests**: HTTP library for Last.fm and external API communication
- **spotipy**: Official Spotify Web API Python library
- **deezer-python**: Deezer API integration for playlist imports
- **psycopg2-binary**: PostgreSQL database adapter

### Platform API Integrations
- **Last.fm Web Services API 2.0**: Core scrobbling functionality
- **Spotify Web API**: Playlist import and music search
- **Deezer API**: Alternative music platform integration
- **Replit OAuth**: User authentication and account management

### Database Requirements
- **PostgreSQL**: Primary database for user data and playlists
- Automatic table creation and schema management
- Connection pooling and performance optimization
- Data persistence with relationship integrity

### Optional Enhancements
- **Discord.py**: Bot interface for server-based scrobbling
- **GitHub Pages**: Static demo version deployment
- **Android APK**: Mobile application development options