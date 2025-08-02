# Telegram Circle Video Bot

## Overview

This is a Telegram bot that converts regular videos and images into circular videos (kruzhok format) for Telegram messaging. The bot is designed for Uzbek-speaking users and provides a simple interface to transform media files into the circular video format commonly used in Telegram. Users can upload videos or images, and the bot processes them to create circular videos that can be shared as Telegram's native circle video format.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Technology**: Python with pyTeleBot library
- **Design Pattern**: Event-driven webhook/polling architecture
- **Rationale**: PyTeleBot provides a simple and reliable way to interact with Telegram's Bot API, handling message routing and file operations efficiently

### Media Processing Pipeline
- **Input Handling**: Accepts both video and image files from users
- **Processing Approach**: Likely uses FFmpeg or similar media processing tools via subprocess calls
- **Output Format**: Generates circular video format compatible with Telegram's kruzhok feature
- **Temporary File Management**: Uses Python's tempfile module for secure temporary file handling during processing

### User Interface Design
- **Language**: Uzbek language interface with localized messages
- **Interaction Flow**: Three-step process (upload → select effect → receive result)
- **Effect Selection**: 5 different video effects available (normal, zoom, blur, color change, rotation)
- **Command Structure**: Simple commands (/start, /hide, /lang) for user control
- **User State Management**: Tracks user's current state (choosing_effect) and stored media files
- **User Feedback**: Real-time status updates during processing with emoji-enhanced messages

### Error Handling
- **File Validation**: Checks for supported media formats before processing
- **User Feedback**: Clear error messages in Uzbek for unsupported formats or processing failures
- **Logging**: Comprehensive logging system for debugging and monitoring

### Configuration Management
- **Environment Variables**: Bot token stored as environment variable for security
- **Message Localization**: Centralized message dictionary for easy translation management

## External Dependencies

### Telegram Bot API
- **Purpose**: Core messaging and file handling functionality
- **Library**: pyTeleBot (telebot)
- **Integration**: Handles message reception, file downloads, and response delivery

### Media Processing Tools
- **Likely Tool**: FFmpeg (executed via subprocess)
- **Purpose**: Video and image manipulation for circular format conversion
- **Integration**: Command-line execution for media transformation

### System Dependencies
- **Python Standard Library**: tempfile, subprocess, pathlib, logging, os, time
- **File System**: Temporary directory usage for media processing workflow

### Runtime Environment
- **Platform**: Cross-platform Python application
- **Deployment**: Designed for containerized or server deployment with environment variable configuration