# AutoClip Gaming - Setup Guide

## Overview

AutoClip Gaming is an autonomous system that discovers trending gaming videos, analyzes them for viral moments using AI, extracts high-quality short clips, generates SEO-optimized metadata, and publishes to YouTube Shorts, TikTok, and Instagram Reels.

## Prerequisites

- Python 3.10 or higher
- FFmpeg installed on your system
- Git (for cloning the repository)
- A GitHub account (for GitHub Actions)

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd autoclip-gaming
```

### 2. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3 python3-pip
```

**macOS:**
```bash
brew install ffmpeg python3
```

**Windows:**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Add FFmpeg to your PATH
3. Install Python 3.10+ from python.org

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for publishing)
YOUTUBE_CLIENT_SECRETS=/path/to/client_secrets.json
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token_here
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
```

## API Key Setup

### YouTube Data API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Go to Credentials → Create Credentials → API Key
5. Copy the API key to `.env`

**For Publishing to YouTube:**
1. Go to Google Cloud Console
2. Go to Credentials → Create Credentials → OAuth client ID
3. Select "Desktop application"
4. Download the JSON file
5. Save it and add the path to `YOUTUBE_CLIENT_SECRETS` in `.env`

### Gemini API (Google AI)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key to `.env`

### TikTok API (Optional)

1. Go to [TikTok Developer Portal](https://developers.tiktok.com/)
2. Create a developer account
3. Create an app and get access token
4. Copy to `.env`

**Note:** TikTok API is currently restricted. The system will use mock uploads if the token is not provided.

### Instagram API (Optional)

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create an app and select Instagram
3. Add Instagram Graph API
4. Get access token
5. Copy to `.env`

**Note:** Instagram API requires a business account and app review. The system will use mock uploads if the token is not provided.

## Running Locally

### Discover Videos

```bash
python src/discovery.py
```

This will:
- Search YouTube for trending gaming videos
- Save discovered videos to `data/videos.db`
- Output video IDs to `data/discovered_videos.json`

### Process a Video

```bash
python src/processor.py --video-id <youtube_video_id> --niche <game_niche>
```

Example:
```bash
python src/processor.py --video-id dQw4w9WgXcQ --niche "Fortnite"
```

This will:
- Download the video
- Transcribe audio
- Detect viral moments
- Generate clips for all platforms
- Run quality checks
- Save results to database

### Publish Clips

```bash
python src/publisher.py
```

This will:
- Find unpublished clips from database
- Publish to configured platforms
- Track publication status

## GitHub Actions Deployment

### 1. Fork or Create Repository

Push your code to GitHub.

### 2. Configure Repository Secrets

Go to your repository Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

- `YOUTUBE_API_KEY`: Your YouTube Data API key
- `GEMINI_API_KEY`: Your Gemini API key
- `YOUTUBE_CLIENT_SECRETS`: (Optional) YouTube OAuth client secrets (base64 encoded)
- `TIKTOK_ACCESS_TOKEN`: (Optional) TikTok access token
- `INSTAGRAM_ACCESS_TOKEN`: (Optional) Instagram access token

**Base64 Encoding for YouTube Client Secrets:**

On Linux/Mac:
```bash
base64 -i path/to/client_secrets.json
```

On Windows (PowerShell):
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("path\to\client_secrets.json"))
```

### 3. Enable GitHub Actions

1. Go to Actions tab
2. Click "I understand my workflows, go ahead and enable them"
3. The workflow will run automatically every 6 hours
4. You can also trigger it manually from the Actions tab

### 4. Monitor Workflow Runs

- Go to the Actions tab
- Click on a workflow run to see logs
- Check for any errors in the output

## Configuration

Edit `config/config.yaml` to customize:

- **Discovery niches**: Change the games to search for
- **Video quality**: Adjust resolution and bitrate
- **Virality scoring**: Adjust weights for detecting moments
- **QA settings**: Change strictness levels
- **Publishing platforms**: Enable/disable specific platforms

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
pip install -r requirements.txt --upgrade
```

**FFmpeg Not Found:**
Make sure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

**API Quota Exceeded:**
- YouTube API has daily limits
- Reduce `max_results_per_niche` in config
- Increase discovery interval

**Memory Issues:**
- Reduce `max_parallel` in config
- Use smaller Whisper model (`tiny` instead of `base`)

**Whisper Download Fails:**
```bash
pip install openai-whisper
```

### Getting Help

Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions to common problems.

## Next Steps

- Review [Architecture Documentation](ARCHITECTURE.md) to understand the system
- Customize [AI Prompts](prompts.yaml) for better moment detection
- Adjust [Compliance Rules](compliance_rules.yaml) for quality control
- Set up analytics tracking to monitor performance

## Support

For issues or questions:
1. Check existing GitHub Issues
2. Review Troubleshooting Guide
3. Create a new issue with details

---

**Happy Clipping! 🎮📹**
