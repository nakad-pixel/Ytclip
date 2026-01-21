# AutoClip Gaming 🎮📹

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-green.svg)](https://github.com/features/actions)

> Autonomous Multi-Platform Viral Clip Generator for Gaming Content

AutoClip Gaming discovers trending gaming videos, analyzes them for viral moments using AI, extracts high-quality short clips, generates SEO-optimized metadata, and automatically publishes to YouTube Shorts, TikTok, and Instagram Reels.

## ✨ Features

- 🔍 **Smart Discovery**: Automatically finds trending gaming videos from YouTube
- 🧠 **AI-Powered Analysis**: Uses Gemini AI to detect viral moments
- ✂️ **Intelligent Clipping**: Extracts and formats clips for each platform
- 📝 **SEO Optimization**: Auto-generates titles, descriptions, and hashtags
- 🎨 **Gaming-Style Captions**: Dynamic, engaging text overlays
- ✅ **Quality Assurance**: Automatic compliance and quality checks
- 🚀 **Multi-Platform Publishing**: Uploads to YouTube Shorts, TikTok, and Instagram
- 📊 **Analytics Tracking**: Monitors performance across all platforms
- ⚙️ **Fully Automated**: Runs on GitHub Actions for free

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AutoClip Gaming Pipeline                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌───▼────┐        ┌───▼─────┐
   │Discovery│         │Process │        │Publish │
   └────┬────┘         └───┬────┘        └───┬─────┘
        │                  │                  │
   ┌────▼──────────────────▼──────────────────▼────┐
   │              Core Modules                     │
   ├──────────────────────────────────────────────────┤
   │ • YouTube API Integration                     │
   │ • yt-dlp Video Downloads                    │
   │ • Whisper Transcription                     │
   │ • Gemini AI Analysis                        │
   │ • FFmpeg Video Processing                   │
   │ • SEO Metadata Generation                    │
   │ • Quality Assurance Checks                   │
   └──────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg
- YouTube Data API key
- Gemini API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/autoclip-gaming.git
cd autoclip-gaming

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Run Locally

```bash
# Discover trending videos
python src/discovery.py

# Process a specific video
python src/processor.py --video-id <youtube_id> --niche <game>

# Publish generated clips
python src/publisher.py
```

### Deploy to GitHub Actions

1. Push code to GitHub
2. Add repository secrets (API keys)
3. Enable GitHub Actions
4. Pipeline runs automatically every 6 hours

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       └── main.yml           # GitHub Actions pipeline
├── src/
│   ├── discovery.py            # YouTube video discovery
│   ├── downloader.py          # Video downloading
│   ├── transcriber.py        # Audio transcription (Whisper)
│   ├── analyzer.py           # Viral moment detection (Gemini)
│   ├── editor.py             # Video editing (FFmpeg)
│   ├── caption_generator.py   # Caption generation
│   ├── seo_generator.py      # SEO metadata
│   ├── quality_assurance.py  # QA checks
│   ├── analytics.py          # Performance tracking
│   ├── database.py          # SQLite operations
│   ├── processor.py         # Main pipeline orchestrator
│   ├── config_validator.py   # Configuration validation
│   ├── utils.py             # Utility functions
│   └── publishers/
│       ├── youtube.py        # YouTube Shorts publisher
│       ├── tiktok.py        # TikTok publisher
│       └── instagram.py     # Instagram Reels publisher
├── config/
│   ├── config.yaml          # Main configuration
│   ├── prompts.yaml         # AI prompts
│   └── compliance_rules.yaml # QA rules
├── tests/
│   ├── test_discovery.py
│   ├── test_analyzer.py
│   ├── test_editor.py
│   ├── test_publishers.py
│   └── test_integration.py
├── docs/
│   ├── SETUP.md             # Setup guide
│   ├── API_KEYS.md          # API key configuration
│   ├── TROUBLESHOOTING.md  # Issue resolution
│   └── ARCHITECTURE.md     # System design
├── requirements.txt
├── .env.example
└── README.md
```

## 🔑 API Keys Required

### Required

- **YouTube Data API**: For discovering trending videos
- **Google Gemini AI**: For viral moment detection and SEO generation

### Optional (for publishing)

- **YouTube OAuth**: For publishing to YouTube Shorts
- **TikTok API**: For publishing to TikTok (mocked if not provided)
- **Instagram API**: For publishing to Instagram Reels (mocked if not provided)

See [API_KEYS.md](docs/API_KEYS.md) for detailed setup instructions.

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- **Discovery**: Change game niches, view thresholds
- **Processing**: Adjust parallel processing, timeouts
- **Video Editing**: Modify resolutions, caption styles
- **SEO**: Customize title style, hashtag counts
- **Quality Assurance**: Set strictness levels
- **Publishing**: Enable/disable platforms, set limits

## 📊 Pipeline Flow

1. **Discovery** (Every 6 hours)
   - Searches YouTube for trending gaming videos
   - Filters by view count and recency
   - Saves to database

2. **Processing** (Parallel, up to 2 videos)
   - Downloads video using yt-dlp
   - Transcribes audio with Whisper
   - Analyzes for viral moments with Gemini
   - Generates clips for each platform
   - Runs quality checks
   - Saves to database

3. **Publishing** (After processing)
   - Retrieves unpublished clips
   - Publishes to YouTube, TikTok, Instagram
   - Tracks publication status

4. **Analytics** (Every 12 hours)
   - Fetches metrics from platforms
   - Updates database
   - Generates performance reports

## 🎯 Supported Platforms

| Platform      | Format | Max Duration | Status  |
|---------------|---------|--------------|---------|
| YouTube Shorts | 9:16    | 60s          | ✅ Full  |
| TikTok        | 9:16    | 180s         | ⚠️ Mock* |
| Instagram     | 9:16    | 90s          | ⚠️ Mock* |

*Mock implementation included for testing; full integration requires API approval.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_analyzer.py

# Run with verbose output
pytest -v
```

## 📈 Performance

- **Discovery Rate**: ~50 videos per 6 hours
- **Processing Time**: ~5-10 minutes per video
- **Clip Generation**: 3-9 clips per video (1-3 per platform)
- **Cost**: Free tier supports ~100 videos/day

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Video Processing**: FFmpeg, yt-dlp
- **AI/ML**: Google Gemini AI, Whisper
- **Database**: SQLite
- **Automation**: GitHub Actions
- **APIs**: YouTube Data API v3

## 📚 Documentation

- [Setup Guide](docs/SETUP.md) - Complete installation and configuration
- [API Keys](docs/API_KEYS.md) - Detailed API key setup instructions
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Architecture](docs/ARCHITECTURE.md) - System design and data flow

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

- This tool is for educational and personal use
- Respect copyright and content ownership
- Follow platform terms of service
- Always give credit to original creators

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Whisper](https://github.com/openai/whisper) - Speech recognition
- [Google Gemini](https://ai.google.dev/) - AI analysis
- [FFmpeg](https://ffmpeg.org/) - Video processing

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/yourusername/autoclip-gaming/issues)
- 💬 [Discussions](https://github.com/yourusername/autoclip-gaming/discussions)

---

**Built with ❤️ for the gaming community**

**Happy Clipping! 🎮📹**
