# AutoClip Gaming - Architecture Documentation

## System Overview

AutoClip Gaming is a distributed system that automates the process of discovering, processing, and publishing viral gaming clips across multiple social media platforms. The system is designed to run primarily on GitHub Actions with optional local execution.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      GitHub Actions Scheduler                          │
│                   (Triggers every 6 hours)                          │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Discovery  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Database   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌───▼────┐     ┌───▼────┐
    │Process  │      │Process  │     │Process  │
    │Video 1  │      │Video 2  │     │Video 3 │
    └────┬────┘      └───┬────┘     └───┬────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                   ┌──────▼──────┐
                   │  Publish    │
                   └──────┬──────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼─────┐    ┌───▼────┐    ┌───▼──────┐
   │  YouTube  │    │ TikTok  │    │Instagram │
   │  Shorts  │    │         │    │  Reels   │
   └──────────┘    └────────┘    └──────────┘
```

## Component Architecture

### 1. Discovery Layer

**Purpose:** Find trending gaming videos from YouTube

**Components:**
- `DiscoveryService` - Main orchestrator
- YouTube Data API client
- SQLite database for tracking

**Data Flow:**
```
YouTube API
    ↓ (Search & Filter)
DiscoveryService
    ↓ (Validate & Deduplicate)
Database (videos table)
    ↓ (Output)
discovered_videos.json
```

**Key Features:**
- Multi-niche search (Roblox, Horror, Fortnite)
- View count filtering (min: 10,000)
- Recency filtering (max: 7 days)
- Deduplication (skip already processed)

### 2. Processing Layer

**Purpose:** Transform videos into publishable clips

**Pipeline Stages:**

```
Video ID
    ↓
[Download] → Download video from YouTube (yt-dlp)
    ↓
[Transcribe] → Extract and transcribe audio (Whisper)
    ↓
[Analyze] → Detect viral moments (Gemini AI)
    ↓
[Generate] → Create clips for each platform (FFmpeg)
    ↓
[Validate] → QA checks (QualityAssurance)
    ↓
[Metadata] → SEO optimization (SEOGenerator)
    ↓
Database (clips table)
```

**Components:**

1. **Downloader (`downloader.py`)**
   - Uses yt-dlp for video downloads
   - Format selection (720p max for speed)
   - Automatic cleanup

2. **Transcriber (`transcriber.py`)**
   - Extracts audio using FFmpeg
   - Transcribes using Whisper (base model)
   - Returns timestamped text segments

3. **Analyzer (`analyzer.py`)**
   - Uses Gemini AI for viral moment detection
   - Scores moments by virality potential
   - Selects best moments (top 3)

4. **Editor (`editor.py`)**
   - Extracts clips at timestamps
   - Resizes to 9:16 format
   - Platform-specific optimization
   - Optional caption burning

5. **SEO Generator (`seo_generator.py`)**
   - Generates clickbait titles
   - Creates descriptions
   - Selects relevant hashtags

6. **Quality Assurance (`quality_assurance.py`)**
   - Duration checks
   - Content validation
   - Profanity filtering
   - Copyright detection (basic)

### 3. Publishing Layer

**Purpose:** Upload clips to social platforms

**Architecture:**
```
Database (unpublished clips)
    ↓
Publisher (Orchestrator)
    ↓
    ├─→ YouTube Publisher (API + OAuth)
    ├─→ TikTok Publisher (Mock/Real)
    └─→ Instagram Publisher (Mock/Real)
         ↓
      Analytics Tracker
```

**Components:**

1. **Publisher (`publisher.py`)**
   - Orchestrates multi-platform publishing
   - Implements rate limiting
   - Error handling and retries

2. **Platform Publishers (`publishers/`)**
   - `youtube.py` - Full API integration
   - `tiktok.py` - Mock (API restricted)
   - `instagram.py` - Mock (API restricted)

3. **Analytics (`analytics.py`)**
   - Tracks published clips
   - Fetches performance metrics
   - Generates reports

### 4. Data Layer

**Purpose:** Persist state and track progress

**Schema:**

```sql
-- Videos table
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    youtube_id TEXT UNIQUE,
    title TEXT,
    channel TEXT,
    view_count INTEGER,
    published_at TEXT,
    niche TEXT,
    processed BOOLEAN,
    discovered_at TEXT,
    url TEXT
);

-- Clips table
CREATE TABLE clips (
    id INTEGER PRIMARY KEY,
    youtube_id TEXT,
    clip_path TEXT,
    platform TEXT,
    start_time REAL,
    end_time REAL,
    moment_type TEXT,
    quote TEXT,
    virality_score REAL,
    title TEXT,
    description TEXT,
    hashtags TEXT,
    qa_passed BOOLEAN,
    published BOOLEAN,
    created_at TEXT
);

-- Analytics table
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY,
    clip_id INTEGER,
    platform TEXT,
    platform_video_id TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    fetched_at TEXT
);
```

## Data Flow

### Complete Pipeline Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   1. DISCOVERY PHASE                      │
├──────────────────────────────────────────────────────────────┤
│ • Search YouTube for trending videos (50 per niche)        │
│ • Filter by views (>10k) and recency (<7 days)          │
│ • Check database for duplicates                           │
│ • Save new videos to database                            │
│ • Output: discovered_videos.json                           │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                   2. PROCESSING PHASE                     │
├──────────────────────────────────────────────────────────────┤
│ 2.1 Download                                           │
│   • Fetch video from YouTube (yt-dlp)                    │
│   • Save to data/downloads/                              │
│                                                        │
│ 2.2 Transcribe                                        │
│   • Extract audio (FFmpeg)                               │
│   • Transcribe with Whisper (base model)                   │
│   • Return timestamped segments                           │
│                                                        │
│ 2.3 Analyze                                           │
│   • Send transcription to Gemini AI                        │
│   • Detect viral moments (1-3 per video)                  │
│   • Score moments by virality potential                    │
│   • Select top 3 moments                                │
│                                                        │
│ 2.4 Generate Clips                                     │
│   • For each moment:                                     │
│     - Extract clip segment                                │
│     - Resize to 9:16 for each platform                   │
│     - Apply platform-specific settings                       │
│                                                        │
│ 2.5 Quality Assurance                                  │
│   • Check duration limits                                 │
│   • Validate content quality                              │
│   • Filter profanity                                     │
│   • Flag copyright issues                                 │
│   • Score: 0-100                                       │
│                                                        │
│ 2.6 SEO Metadata                                       │
│   • Generate title (clickbait style)                      │
│   • Create description                                   │
│   • Select hashtags (15 max)                             │
│                                                        │
│ 2.7 Save to Database                                   │
│   • Store clip metadata                                  │
│   • Mark video as processed                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                   3. PUBLISHING PHASE                      │
├──────────────────────────────────────────────────────────────┤
│ • Retrieve unpublished clips from database                   │
│ • For each clip:                                        │
│   - Upload to YouTube Shorts (if enabled)                 │
│   - Upload to TikTok (if enabled - mocked)               │
│   - Upload to Instagram Reels (if enabled - mocked)        │
│   - Rate limit uploads (stagger by 120min)               │
│   - Update database with publication status                │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                   4. ANALYTICS PHASE                       │
├──────────────────────────────────────────────────────────────┤
│ • Fetch metrics from platforms (every 12 hours)           │
│ • Update database with views, likes, comments              │
│ • Calculate engagement rates                              │
│ • Generate performance reports                            │
│ • Identify top-performing clips                          │
└──────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|----------|
| Language | Python 3.10+ | Main implementation |
| Automation | GitHub Actions | CI/CD pipeline |
| Database | SQLite | Data persistence |
| Config | YAML | Configuration management |

### External APIs

| Service | Usage | Cost |
|----------|-------|-------|
| YouTube Data API v3 | Video discovery, stats | Free tier: 10k units/day |
| Google Gemini AI | Viral detection, SEO | Free tier: 15 req/min |
| YouTube OAuth | Publishing to Shorts | Free |
| TikTok API | Publishing (mocked) | Restricted |
| Instagram Graph API | Publishing (mocked) | Requires approval |

### Libraries

| Library | Purpose | Key Functions |
|----------|---------|----------------|
| google-api-python-client | YouTube API | Search, video details |
| google-generativeai | Gemini AI | Viral moment detection |
| yt-dlp | Video download | Download videos |
| whisper | Transcription | Speech-to-text |
| ffmpeg-python | Video processing | FFmpeg wrapper |
| pyyaml | Config parsing | Load YAML files |
| pytest | Testing | Unit & integration tests |

## Scalability Considerations

### Current Limitations

1. **API Quotas**
   - YouTube: 10,000 units/day (~100 videos)
   - Gemini: 15 requests/minute

2. **Processing Time**
   - ~5-10 minutes per video
   - Limited by GitHub Actions (6 hours)

3. **Storage**
   - Artifacts: 500MB limit
   - Database: SQLite (single file)

### Scaling Strategies

1. **Increase Quotas**
   - Upgrade to paid YouTube API tier
   - Use paid Gemini tier

2. **Parallel Processing**
   - Increase `max_parallel` in config
   - Use multiple GitHub Actions runners

3. **Distributed Processing**
   - Move to dedicated server
   - Use job queue (Redis + Celery)

4. **Database Migration**
   - Switch to PostgreSQL for scale
   - Add connection pooling

5. **Caching**
   - Cache YouTube API responses
   - Store transcriptions
   - Memoize Gemini responses

## Security Architecture

### API Key Management

```
┌─────────────────────────────────────────────────┐
│         GitHub Secrets (Encrypted)             │
├─────────────────────────────────────────────────┤
│ • YOUTUBE_API_KEY                           │
│ • GEMINI_API_KEY                            │
│ • YOUTUBE_CLIENT_SECRETS (base64)           │
│ • TIKTOK_ACCESS_TOKEN                       │
│ • INSTAGRAM_ACCESS_TOKEN                     │
└─────────────────────────────────────────────────┘
                    │
                    ↓ (GitHub Actions)
┌─────────────────────────────────────────────────┐
│          Environment Variables                  │
├─────────────────────────────────────────────────┤
│ Loaded into process at runtime               │
│ Never written to logs or files              │
└─────────────────────────────────────────────────┘
```

### Best Practices

1. **Never commit secrets** - `.gitignore` prevents this
2. **Base64 encode OAuth files** - For GitHub Secrets
3. **Rotate keys regularly** - Every 90 days
4. **Use least privilege** - Minimal API scopes
5. **Audit access** - Monitor usage logs

## Error Handling Strategy

### Hierarchy

```
1. Retry logic (3 attempts, exponential backoff)
   ↓
2. Fallback to alternative method (if available)
   ↓
3. Graceful degradation (skip feature, continue)
   ↓
4. Log error and fail task
```

### Specific Strategies

- **API failures**: Retry with backoff
- **Video download**: Skip, try next video
- **Transcription failure**: Continue without it
- **Publishing failure**: Save to database, retry later
- **Workflow failure**: Send notification, don't block

## Monitoring & Observability

### Logging Levels

- **DEBUG**: Detailed flow information
- **INFO**: Key events and progress
- **WARNING**: Non-critical issues
- **ERROR**: Failures that need attention
- **CRITICAL**: System failures

### Metrics Tracked

1. **Discovery Metrics**
   - Videos found per niche
   - Videos filtered by views
   - Videos already processed

2. **Processing Metrics**
   - Download success rate
   - Transcription time
   - Moments detected per video
   - Clips generated per video

3. **Publishing Metrics**
   - Upload success rate
   - Upload time per platform
   - Failed uploads (with reasons)

4. **Analytics Metrics**
   - Views, likes, comments
   - Engagement rate
   - Top performing clips

### Health Checks

```python
def health_check():
    checks = {
        'api_keys': verify_api_keys(),
        'database': check_database_connection(),
        'disk_space': check_disk_space(),
        'ffmpeg': check_ffmpeg_installed(),
        'whisper': check_whisper_model_loaded()
    }
    return all(checks.values()), checks
```

## Deployment Architecture

### GitHub Actions Workflow

```
┌─────────────────────────────────────────────┐
│          GitHub Repository                  │
└──────────┬──────────────────────────────┘
           │
           ↓ (push / schedule)
┌─────────────────────────────────────────────┐
│      GitHub Actions Runner                │
│  • Ubuntu 22.04                        │
│  • Python 3.10                         │
│  • FFmpeg pre-installed                │
└──────────┬──────────────────────────────┘
           │
    ┌──────┼──────┐
    │      │      │
    ↓      ↓      ↓
┌─────┐ ┌─────┐ ┌─────┐
│Disc.│ │Proc.│ │Pub. │
└─────┘ └─────┘ └─────┘
```

### Job Dependencies

```
discover (runs every 6h)
    ↓ (outputs: videos)
process (matrix: videos, max-parallel: 2)
    ↓ (outputs: clips)
publish (all clips)
    ↓
cleanup (always, delete artifacts)
```

## Future Enhancements

### Planned Features

1. **AI Improvements**
   - Custom fine-tuned models
   - Better moment detection
   - Automatic hashtag generation

2. **Platform Integration**
   - Real TikTok API (when approved)
   - Real Instagram API (when approved)
   - Add more platforms (Snap, Shorts, etc.)

3. **Analytics**
   - Real-time dashboard
   - A/B testing
   - Predictive performance

4. **User Interface**
   - Web dashboard
   - Manual clip editing
   - Scheduled publishing

5. **Monetization**
   - Affiliate link insertion
   - Sponsorship integration
   - Revenue tracking

---

**Document Version:** 1.0.0
**Last Updated:** 2024-01-21
