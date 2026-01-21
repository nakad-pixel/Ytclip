# Troubleshooting Guide

This guide helps you resolve common issues with AutoClip Gaming.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [API Key Problems](#api-key-problems)
3. [Video Processing Issues](#video-processing-issues)
4. [AI/ML Issues](#aiml-issues)
5. [Publishing Issues](#publishing-issues)
6. [GitHub Actions Issues](#github-actions-issues)
7. [Performance Issues](#performance-issues)

---

## Installation Issues

### Python Version Error

**Error:**
```
SyntaxError: Python 3.10 or higher required
```

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.10+
# Ubuntu/Debian
sudo apt-get install python3.10

# macOS (using Homebrew)
brew install python@3.10

# Windows
# Download from python.org
```

### FFmpeg Not Found

**Error:**
```
ffmpeg: command not found
```

**Solution:**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Search "Environment Variables"
   - Edit PATH
   - Add `C:\ffmpeg\bin`

**Verify:**
```bash
ffmpeg -version
```

### Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt --upgrade

# Or install specific module
pip install <module_name>

# If using virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Whisper Installation Fails

**Error:**
```
ERROR: Could not build wheels for openai-whisper
```

**Solution:**

**Option 1: Install system dependencies**
```bash
# Ubuntu/Debian
sudo apt-get install -y python3-dev rustc cargo

# macOS
xcode-select --install
```

**Option 2: Use pre-built wheels**
```bash
pip install openai-whisper --prefer-binary
```

**Option 3: Use smaller model only**
```python
# In transcriber.py
Transcriber(model_size='tiny')  # Instead of 'base'
```

---

## API Key Problems

### YouTube API Key Invalid

**Error:**
```
403 Forbidden: API key not valid
```

**Solution:**

1. Verify key is correct in `.env`
2. Check key restrictions:
   - Go to Google Cloud Console → APIs & Services → Credentials
   - Edit your API key
   - Under "API restrictions", ensure YouTube Data API v3 is selected
3. Check quotas:
   - Go to APIs & Services → Dashboard
   - Verify you haven't exceeded daily quota

### Gemini API Error

**Error:**
```
403: Your application has authenticated using end user credential
```

**Solution:**

Gemini uses API keys, not OAuth. Ensure you're using:
```python
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
```

Not:
```python
# Wrong - don't use OAuth
genai.configure(credentials=...)
```

### Quota Exceeded

**Error:**
```
429: Resource has been exhausted
```

**Solution:**

**YouTube:**
- Reduce `max_results_per_niche` in `config.yaml`
- Increase discovery interval (edit GitHub Actions workflow)
- Check usage: Google Cloud Console → APIs & Services → Quotas

**Gemini:**
- Free tier: 15 requests/minute
- Implement retry logic:
```python
import time
from google.api_core import exceptions

for attempt in range(3):
    try:
        response = model.generate_content(prompt)
        break
    except exceptions.ResourceExhausted:
        time.sleep(60)  # Wait 1 minute
```

---

## Video Processing Issues

### Download Timeout

**Error:**
```
Download timeout for video_id
```

**Solution:**

Increase timeout in `downloader.py`:
```python
subprocess.run(cmd, check=True, timeout=600)  # 10 minutes instead of 5
```

Or use alternative mirror:
```python
cmd = [
    'yt-dlp',
    '--proxy', 'socks5://127.0.0.1:1080',  # If using proxy
    '-f', 'best[height<=720]',
    # ...
]
```

### FFmpeg Processing Fails

**Error:**
```
Invalid data found when processing input
```

**Solution:**

1. Check video format:
```bash
ffprobe input.mp4
```

2. Try different codec:
```python
# In editor.py
'-c:v', 'libx264',  # Try 'libx265' or 'mpeg4'
```

3. Use re-encoding:
```python
# Instead of '-c', 'copy', use:
'-c:v', 'libx264',
'-preset', 'fast',
```

### Audio Extraction Fails

**Error:**
```
No audio stream found
```

**Solution:**

Some videos have no audio. Add check in `transcriber.py`:
```python
# Before extracting audio
probe_cmd = ['ffprobe', '-i', video_path, '-show_streams', '-select_streams', 'a']
result = subprocess.run(probe_cmd, capture_output=True)

if 'Audio: none' in result.stderr.decode():
    logger.warning("No audio stream found")
    return None
```

---

## AI/ML Issues

### Whisper Slow Performance

**Issue:** Transcription takes 30+ minutes

**Solution:**

1. Use smaller model:
```python
transcriber = Transcriber(model_size='tiny')  # Or 'base'
```

2. Use GPU (if available):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. Reduce audio quality:
```python
# In transcriber.py
cmd = [
    'ffmpeg',
    '-i', video_path,
    '-ar', '8000',  # Instead of 16000
    '-ac', '1',
    # ...
]
```

### Gemini Returns Empty Response

**Error:**
```
Response: ''
```

**Solution:**

1. Check API key validity
2. Add debug logging:
```python
logger.debug(f"Prompt: {prompt}")
logger.debug(f"Response: {response.text}")
```

3. Try simpler prompt:
```python
prompt = "Find exciting moments in: {text}"
```

4. Check response structure:
```python
logger.debug(f"Full response: {response.to_dict()}")
```

### JSON Parse Error

**Error:**
```
JSONDecodeError: Expecting value
```

**Solution:**

Gemini sometimes returns extra text. Clean it:
```python
response_text = response.text.strip()

# Remove markdown
if response_text.startswith('```'):
    response_text = response_text.strip('```')
    if response_text.startswith('json'):
        response_text = response_text[4:].strip()

# Remove whitespace
response_text = ' '.join(response_text.split())
```

---

## Publishing Issues

### YouTube Authentication Failed

**Error:**
```
AuthenticationError: Could not authenticate
```

**Solution:**

1. Verify client_secrets.json format:
```json
{
  "installed": {
    "client_id": "...",
    "client_secret": "...",
    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
  }
}
```

2. Regenerate OAuth credentials:
   - Go to Google Cloud Console
   - Delete existing OAuth client
   - Create new one

3. Check consent screen:
   - OAuth consent screen must be configured
   - Status must be "In Production" or "Testing"

### TikTok Upload Fails

**Error:**
```
TikTok API is restricted
```

**Solution:**

TikTok API is currently restricted. Options:

1. **Wait for API approval** (if you have access)
2. **Use manual upload** - clips are generated, you upload manually
3. **Use third-party tool** - Buffer, Later, etc.

The mock implementation will:
- Generate clips successfully
- Log "mock upload" messages
- Not actually upload to TikTok

### Instagram Upload Fails

**Error:**
```
Instagram Graph API requires review
```

**Solution:**

Instagram requires app review for publishing. Options:

1. **Submit app for review**:
   - Provide screenshots
   - Explain use case
   - Wait 1-3 weeks

2. **Use Meta Business Suite**:
   - Upload clips manually
   - Schedule posts

3. **Use third-party scheduler**:
   - Hootsuite
   - Sprout Social

---

## GitHub Actions Issues

### Workflow Fails Immediately

**Error:**
```
Error: YOUTUBE_API_KEY not set
```

**Solution:**

Add secrets to repository:
1. Go to repository Settings → Secrets
2. Click "New repository secret"
3. Add:
   - `YOUTUBE_API_KEY`
   - `GEMINI_API_KEY`
   - (Optional) `YOUTUBE_CLIENT_SECRETS`

### Artifact Upload Fails

**Error:**
```
Error: Unable to upload artifact
```

**Solution:**

Artifacts have size limits (500MB for free). Reduce file sizes:

1. Use lower resolution:
```yaml
# In config.yaml
video_processing:
  target_codec: "h264"
```

2. Delete large files before artifact:
```python
# In processor.py
def cleanup_large_files():
    for f in os.listdir('data'):
        if f.endswith('.mp4') and os.path.getsize(f) > 100_000_000:
            os.remove(f)
```

### Workflow Timeout

**Error:**
```
The operation was canceled
```

**Solution:**

GitHub Actions has 6-hour timeout. Optimize:

1. Reduce processing:
```yaml
# In .github/workflows/main.yml
strategy:
  matrix:
    video: ${{ fromJson(needs.discover.outputs.videos) }}
  max-parallel: 1  # Instead of 2
```

2. Use caching:
```yaml
- name: Cache Whisper models
  uses: actions/cache@v3
  with:
    path: ~/.cache/whisper
    key: whisper-${{ runner.os }}
```

---

## Performance Issues

### System Runs Out of Memory

**Error:**
```
MemoryError: Unable to allocate
```

**Solution:**

1. Reduce parallel processing:
```yaml
# In config.yaml
video_processing:
  max_parallel: 1  # Instead of 2
```

2. Use smaller Whisper model:
```python
Transcriber(model_size='tiny')
```

3. Clear cache regularly:
```python
import gc
gc.collect()
```

### Processing Too Slow

**Issue:** Takes 30+ minutes per video

**Solution:**

1. Skip transcription (if not needed):
```python
# In processor.py
transcription = None
if config.get('enable_transcription', True):
    transcription = transcriber.process_video(video_path)
```

2. Use cached transcriptions:
```python
# Check if already transcribed
cache_key = f"{video_id}_transcription.json"
if os.path.exists(cache_key):
    with open(cache_key, 'r') as f:
        transcription = json.load(f)
```

3. Optimize FFmpeg:
```python
# Use hardware acceleration if available
'-hwaccel', 'cuda',  # or 'videotoolbox' on Mac
```

---

## Getting Additional Help

### Collect Debug Information

Before asking for help, collect:

1. **System Info:**
```bash
python --version
ffmpeg -version
uname -a  # or systeminfo on Windows
```

2. **Logs:**
```bash
# Check recent logs
tail -f autoclip.log
```

3. **Configuration:**
```bash
# Show config (redact sensitive data)
python -c "import yaml; print(yaml.safe_load(open('config/config.yaml')))"
```

### Where to Get Help

1. **GitHub Issues** - Report bugs
2. **GitHub Discussions** - Ask questions
3. **Documentation** - Read guides
4. **Stack Overflow** - Search for similar issues

### Report Format

When reporting an issue, include:

```markdown
## Issue Description
[Brief description]

## Steps to Reproduce
1. Step one
2. Step two

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Error Logs
```
[Paste logs here]
```

## System Information
- OS: [Ubuntu 22.04 / macOS / Windows 11]
- Python: [3.10.5]
- FFmpeg: [5.1.2]
```
```

---

## Prevention Tips

### Regular Maintenance

```bash
# Clean old downloads
find data/downloads -name "*.mp4" -mtime +7 -delete

# Compress old logs
gzip *.log

# Check disk space
df -h
```

### Monitoring

Set up alerts for:
- API quota usage
- Disk space
- Workflow failures

### Backups

```bash
# Backup database
cp data/videos.db backups/videos_$(date +%Y%m%d).db

# Backup config
tar -czf backups/config_$(date +%Y%m%d).tar.gz config/
```

---

**Still stuck?** [Create an issue](https://github.com/yourusername/autoclip-gaming/issues) with details!
