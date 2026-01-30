# Two-Phase Optimized Video Processing Pipeline

## Overview

The AutoClip Gaming system uses a smart two-phase approach to maximize efficiency and avoid YouTube bot detection:

1. **Phase 1 (Analysis):** Discover and analyze ALL discovered videos using transcripts + Gemini AI (no downloads)
2. **Phase 2 (Creation):** Download and process ONLY the top-scoring videos based on virality scores

## Benefits

✅ **Bot Detection Prevention:** Fewer downloads = less suspicious activity  
✅ **Bandwidth Efficiency:** Only download top-scoring videos  
✅ **Time Efficiency:** Analysis (transcripts) is fast; creation is slow but minimal  
✅ **Quality:** Only publish highest virality content  
✅ **Scalability:** Can discover 100+ videos but only process 2-4 per day  
✅ **Failure Isolation:** Phase 1 failures don't block Phase 2 (they're separate jobs)  

## Architecture

### Phase 1: Analysis (Every 6 Hours)

```
Discovery → Fetch Transcripts (YouTube API) → AI Analysis → Score Videos → Database
```

**What Happens:**
1. Discovery module finds new videos from YouTube
2. For each discovered video:
   - Fetch transcript using YouTube Transcript API (no download!)
   - Analyze transcript with Gemini AI for viral moments
   - Calculate virality score (0-100)
   - Store score and status='analyzed' in database
3. Log summary of analyzed videos

**No Downloads:** This phase uses YouTube's free transcript API instead of downloading videos.

### Phase 2: Creation (Every 12 Hours)

```
Select Top Videos → Download → Extract Clips → Generate Metadata → QA Check → Publish
```

**What Happens:**
1. Query database for top N videos with status='analyzed' and score >= threshold
2. For each selected video:
   - Download video from YouTube
   - Extract viral moment clips
   - Generate platform-specific clips (YouTube Shorts, TikTok, Instagram)
   - Run quality assurance checks
   - Publish to platforms
   - Cleanup downloads
   - Mark status='published'

**Selective Processing:** Only downloads and processes 2-4 top videos per day.

## Configuration

Edit `config/config.yaml`:

```yaml
processing:
  # Phase 1: Analysis phase (no downloads)
  max_videos_to_analyze: 100      # Analyze up to 100 discovered videos
  virality_threshold: 70           # Minimum score to proceed to Phase 2
  
  # Phase 2: Download & publish phase
  max_videos_to_process: 2         # Only download/process top 2 videos per cycle
  processing_interval_hours: 12    # Phase 2 runs every 12 hours
```

## Database Schema

Videos table includes new phase tracking fields:

```sql
CREATE TABLE videos (
    ...
    status TEXT DEFAULT 'discovered',  -- 'discovered', 'analyzed', 'processing', 'published', 'failed'
    virality_score REAL DEFAULT 0.0,  -- 0-100 score from AI analysis
    analyzed_at TEXT,                  -- When analysis completed
    processed_at TEXT                  -- When clips were created and published
);
```

## Usage

### Run Phase 1 (Analysis)

```bash
python src/processor.py --phase analysis
```

### Run Phase 2 (Creation)

```bash
python src/processor.py --phase creation
```

### Run Single Video (Legacy Mode)

```bash
python src/processor.py --video-id VIDEO_ID
```

## GitHub Actions Schedule

The workflow automatically runs both phases:

- **Phase 1 (Analysis):** Every 6 hours
  - `0 */6 * * *` (00:00, 06:00, 12:00, 18:00 UTC)
  
- **Phase 2 (Creation):** Every 12 hours
  - `0 0,12 * * *` (00:00, 12:00 UTC)

### Manual Trigger

You can manually trigger specific phases from GitHub Actions UI:

1. Go to Actions tab
2. Select "AutoClip Gaming Pipeline - Two Phase"
3. Click "Run workflow"
4. Select phase: `analysis`, `creation`, or `both`

## Example Scenario

### Day 1

**00:00 UTC - Discovery + Phase 1 Analysis:**
- Discovers 20 new videos
- Analyzes all 20 (transcripts + Gemini)
- Scores: [45, 62, 58, 78, 91, 55, 68, 73, 82, 69, ...]
- 8 videos score >= 70
- Status updated to 'analyzed'
- **No downloads, no bot risk**

**06:00 UTC - Phase 1 Analysis:**
- Discovers 15 more videos
- Analyzes all 15
- Adds to analyzed pool

**12:00 UTC - Phase 2 Creation:**
- Queries top 2 videos: Video A (91), Video B (82)
- Downloads Video A → extracts 6 clips → publishes to 3 platforms
- Downloads Video B → extracts 6 clips → publishes to 3 platforms
- Marks both as 'published'
- Cleans up downloads
- **Minimal downloads, maximum quality**

**18:00 UTC - Phase 1 Analysis:**
- Analyzes another batch of discovered videos

### Day 2

**00:00 UTC - Discovery + Phase 1 + Phase 2:**
- Continues rolling discovery and analysis
- Phase 2 processes next top 2 videos from analyzed pool

## API Requirements

### Phase 1 (Analysis)
- **YouTube Data API v3** - Video discovery
- **YouTube Transcript API** - Free, no auth needed
- **Gemini API** - AI analysis

### Phase 2 (Creation)
- **All Phase 1 APIs** (for re-analysis if needed)
- **YouTube OAuth** (optional) - Publishing to YouTube Shorts
- **TikTok API** (optional) - Publishing to TikTok
- **Instagram API** (optional) - Publishing to Instagram

## Monitoring

### Check Analysis Results

```bash
cat data/phase_analysis_results.json
```

Example output:
```json
{
  "phase": "analysis",
  "videos_analyzed": 20,
  "videos_above_threshold": 8,
  "failures": 0,
  "scores": [
    {"video_id": "abc123", "score": 91.5, "title": "INSANE ROBLOX MOMENT..."},
    {"video_id": "def456", "score": 82.3, "title": "You WON'T BELIEVE..."}
  ]
}
```

### Check Creation Results

```bash
cat data/phase_creation_results.json
```

Example output:
```json
{
  "phase": "creation",
  "videos_processed": 2,
  "clips_generated": 12,
  "failures": 0,
  "published_videos": [
    {"video_id": "abc123", "clips_count": 6, "virality_score": 91.5},
    {"video_id": "def456", "clips_count": 6, "virality_score": 82.3}
  ]
}
```

## Database Queries

### View all analyzed videos

```sql
SELECT youtube_id, title, virality_score, analyzed_at 
FROM videos 
WHERE status = 'analyzed' 
ORDER BY virality_score DESC;
```

### View videos ready for processing

```sql
SELECT youtube_id, title, virality_score 
FROM videos 
WHERE status = 'analyzed' AND virality_score >= 70 
ORDER BY virality_score DESC 
LIMIT 5;
```

### View published videos

```sql
SELECT youtube_id, title, virality_score, processed_at 
FROM videos 
WHERE status = 'published' 
ORDER BY processed_at DESC;
```

## Troubleshooting

### No videos being analyzed

**Check:**
1. Discovery is running and finding videos
2. YouTube Transcript API is accessible
3. Gemini API key is valid
4. Check logs: `data/phase_analysis_results.json`

### No videos being processed in Phase 2

**Check:**
1. Are there analyzed videos above threshold?
   ```bash
   python -c "from src.database import Database; db = Database(); print(db.get_top_analyzed_videos())"
   ```
2. Check virality_threshold in config (default: 70)
3. Check logs: `data/phase_creation_results.json`

### Transcript fetch failures

**Possible causes:**
- Video has no captions/transcript available
- Video is age-restricted
- Video is private or deleted
- YouTube Transcript API rate limit (rare)

**Solution:** Video will be marked as 'failed' and skipped

### Analysis phase taking too long

**Optimize:**
1. Reduce `max_videos_to_analyze` in config
2. Use faster Gemini model if available
3. Check Gemini API rate limits

## Performance Metrics

### Phase 1 (Analysis)
- **Speed:** ~5-10 seconds per video
- **Throughput:** 100 videos in ~10-15 minutes
- **Cost:** Free (YouTube Transcript API)
- **Bandwidth:** ~0 MB (no downloads)

### Phase 2 (Creation)
- **Speed:** ~5-10 minutes per video
- **Throughput:** 2 videos in ~20 minutes
- **Cost:** Bandwidth only (yt-dlp downloads)
- **Bandwidth:** ~100-500 MB per video

### Daily Capacity
- **Analysis:** Up to 400 videos/day (4 cycles × 100 videos)
- **Creation:** 4-8 videos/day (2 cycles × 2-4 videos)
- **Clips Published:** 24-72 clips/day (4-8 videos × 6 clips)

## Best Practices

1. **Run discovery frequently** (every 6 hours) to build analyzed pool
2. **Keep virality threshold high** (70-80) for quality control
3. **Process conservatively** (2-4 videos per cycle) to avoid bot detection
4. **Monitor scores** - adjust threshold if too few/many videos qualify
5. **Clean up old analyzed videos** periodically (>30 days old)
6. **Backup database** before major changes

## Migration from Old Pipeline

If migrating from single-phase pipeline:

1. Backup existing database
2. Deploy new code with schema updates
3. Existing videos will default to status='discovered'
4. Run Phase 1 to analyze existing discovered videos
5. Phase 2 will start processing top-scored videos

No data loss - backward compatible with old database structure.
