# API Keys Configuration Guide

This guide explains how to obtain and configure API keys for all services used by AutoClip Gaming.

## Table of Contents

1. [YouTube Data API](#youtube-data-api)
2. [Google Gemini AI](#google-gemini-ai)
3. [YouTube OAuth (for publishing)](#youtube-oauth-for-publishing)
4. [TikTok API](#tiktok-api)
5. [Instagram API](#instagram-api)

---

## YouTube Data API

### Purpose

Used for:
- Discovering trending videos
- Getting video statistics
- Fetching channel information

### Obtaining API Key

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Create Project"
   - Enter project name (e.g., "AutoClip Gaming")
   - Click "Create"

2. **Enable YouTube Data API**
   - In left sidebar, go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click on it
   - Click "Enable"

3. **Create API Key**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the API key

4. **Restrict API Key** (Recommended)
   - Click the "Edit" icon (pencil) next to your API key
   - Under "Application restrictions", select "IP addresses"
   - Add:
     - Your local IP (if running locally)
     - GitHub Actions IP ranges (if deploying)
   - Under "API restrictions", select "Restrict key"
   - Select "YouTube Data API v3"
   - Click "Save"

### Usage

Add to `.env`:
```env
YOUTUBE_API_KEY=AIzaSy...
```

### Quotas

- Daily quota: 10,000 units
- Search request: 100 units
- Video details: 1 unit
- With current settings, can process ~100 videos per day

**Monitoring:**
- Go to Google Cloud Console → APIs & Services → Dashboard
- Check YouTube Data API v3 usage

---

## Google Gemini AI

### Purpose

Used for:
- Detecting viral moments in transcriptions
- Generating optimized titles
- Creating engaging descriptions

### Obtaining API Key

1. **Access Google AI Studio**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Accept terms of service
   - Copy the API key

3. **Project Selection** (Optional)
   - You can select an existing Google Cloud project
   - Or create a new one

### Usage

Add to `.env`:
```env
GEMINI_API_KEY=AIzaSy...
```

### Quotas

- Free tier: 15 requests per minute
- Paid tier: Much higher limits
- Current usage: ~2-3 requests per video

**Monitoring:**
- Go to [Google AI Studio](https://makersuite.google.com/app/usage)
- View usage statistics

### Best Practices

- Implement retry logic for rate limits
- Cache responses when possible
- Use appropriate model (gemini-pro for most cases)

---

## YouTube OAuth (for publishing)

### Purpose

Used for:
- Publishing clips to YouTube Shorts
- Managing your YouTube channel

### Prerequisites

- Google Account with a YouTube channel
- Google Cloud Project with API access

### Creating OAuth Credentials

1. **Configure OAuth Consent Screen**
   - Go to Google Cloud Console → APIs & Services → OAuth consent screen
   - Select "External" (for personal use)
   - Fill in required fields:
     - App name: "AutoClip Gaming"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue" (skip optional sections)
   - Click "Back to Dashboard"

2. **Create OAuth Client ID**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop application"
   - Name: "AutoClip Gaming"
   - Click "Create"

3. **Download Client Secrets**
   - Click the download icon (arrow down)
   - Save the JSON file as `client_secrets.json`
   - **Do not commit this file to Git!**

### Usage

Add to `.env`:
```env
YOUTUBE_CLIENT_SECRETS=/path/to/client_secrets.json
```

For GitHub Actions, encode as base64:

```bash
base64 -i client_secrets.json
```

Add to GitHub Secrets:
```
YOUTUBE_CLIENT_SECRETS=<base64_encoded_string>
```

### Scopes

The system requests:
- `https://www.googleapis.com/auth/youtube.upload`
- Uploads videos to your channel

### Security Notes

- Never share your client_secrets.json
- Add to `.gitignore`
- Rotate credentials if compromised

---

## TikTok API

### Purpose

Used for:
- Publishing clips to TikTok
- Managing TikTok account

### Status: ⚠️ Restricted Access

TikTok's API is currently restricted and requires approval for automated uploads. The system includes a mock implementation for testing.

### Obtaining Access (If Approved)

1. **Developer Account**
   - Go to [TikTok Developer Portal](https://developers.tiktok.com/)
   - Sign up for a developer account
   - Complete verification

2. **Create Application**
   - Go to "My Apps" → "Create App"
   - Select "Business" app type
   - Fill in application details

3. **Get Access Token**
   - Go to app dashboard
   - Generate access token
   - Copy the token

### Usage

Add to `.env`:
```env
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token
```

### Without Access Token

The system will:
- Generate clips but skip actual upload
- Log "mock upload" messages
- Allow testing of other components

### Alternative

Consider using TikTok's [Official API](https://developers.tiktok.com/doc/login-kit/) when access becomes available.

---

## Instagram API

### Purpose

Used for:
- Publishing clips to Instagram Reels
- Managing Instagram business account

### Prerequisites

- Instagram Business account
- Facebook Business account
- Meta Developer account
- App review approval (currently required)

### Obtaining Access

1. **Create Meta Developer Account**
   - Go to [Meta for Developers](https://developers.facebook.com/)
   - Sign up and create a developer account

2. **Create Application**
   - Go to "My Apps" → "Create App"
   - Select "Business" type
   - Fill in details

3. **Add Instagram Product**
   - In app dashboard, click "Add Product"
   - Select "Instagram Graph API"
   - Configure permissions

4. **Get Access Token**
   - Generate user access token
   - Include required permissions:
     - `instagram_basic`
     - `instagram_content_publish`
     - `pages_read_engagement`

5. **App Review** (Required)
   - Submit your app for review
   - Provide screenshots and explanation
   - Wait for approval (can take weeks)

### Usage

Add to `.env`:
```env
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
```

Also add:
```env
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
```

### Without Access Token

The system will:
- Generate clips but skip actual upload
- Log "mock upload" messages
- Allow testing of other components

### Alternative

Use a social media management tool like:
- [Buffer](https://buffer.com/)
- [Later](https://later.com/)
- [Hootsuite](https://hootsuite.com/)

---

## Security Best Practices

### 1. Never Commit API Keys

Add to `.gitignore`:
```
.env
client_secrets.json
*.json
!config/*.json
```

### 2. Use Environment Variables

Always load keys from environment:
```python
api_key = os.getenv('API_KEY')
```

### 3. Rotate Credentials Regularly

- Change API keys every 90 days
- Monitor for unauthorized usage
- Revoke unused credentials

### 4. Use Secrets Management

For production:
- GitHub Secrets (CI/CD)
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

### 5. Implement Rate Limiting

```python
from utils import RateLimiter

limiter = RateLimiter(calls_per_second=10)
limiter.wait_if_needed()
# Make API call
```

### 6. Log Usage

Track API usage:
```python
logger.info(f"YouTube API quota used: {quota_used}/{quota_limit}")
```

---

## Cost Estimation

### Free Tier

- YouTube Data API: 10,000 units/day
- Gemini AI: 15 requests/minute (free tier)
- Total: ~100 videos/day processing

### Paid Tiers

If you exceed free limits:
- YouTube: ~$5-20/month for increased quota
- Gemini: ~$0.001/1k tokens
- TikTok/Instagram: Free (once approved)

---

## Testing API Keys

### YouTube

```bash
curl "https://www.googleapis.com/youtube/v3/search?key=YOUR_KEY&q=test"
```

### Gemini

```python
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello")
print(response.text)
```

---

## Troubleshooting API Issues

### Invalid API Key

- Check for typos
- Ensure key is properly copied
- Verify key hasn't been revoked

### Quota Exceeded

- Check usage in respective dashboards
- Reduce request frequency
- Consider upgrading to paid tier

### Authentication Failed

- Verify OAuth configuration
- Check consent screen settings
- Ensure required scopes are included

---

## Support

For API-specific issues:
1. Check official documentation
2. Review API status pages
3. Check service-specific forums
4. Create GitHub issue with error details
