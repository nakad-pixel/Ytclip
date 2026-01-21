#!/usr/bin/env python3
"""
SEO Generator: Create optimized titles, descriptions, and hashtags
Generates metadata to maximize discoverability on social platforms.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import random

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trending gaming hashtags
GAMING_HASHTAGS = [
    '#gaming', '#gamer', '#gamingclips', '#viral', '#trending',
    '#shorts', '#fyp', '#foryou', '#foryoupage', '#gamingcommunity',
    '#gamingtiktok', '#gamermoments', '#clips', '#gameclips', '#epic',
    '#insane', '#funny', '#wtf', '#omg', '#letsplay', '#gameplay'
]

NICHES_TO_HASHTAGS = {
    'Roblox': ['#roblox', '#robloxfyp', '#bloxfruits', '#robloxedit', '#adoptme'],
    'Horror games': ['#horror', '#horrorgame', '#scary', '#jumscare', '#horrorclips'],
    'Fortnite': ['#fortnite', '#fortniteclips', '#epicgames', '#battleroyale', '#fortnitetiktok']
}

class SEOGenerator:
    """Generate SEO-optimized metadata for social media posts."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize SEO generator with optional Gemini API."""
        if GEMINI_AVAILABLE:
            api_key = api_key or os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.use_ai = True
                logger.info("Initialized Gemini for SEO generation")
            else:
                self.use_ai = False
        else:
            self.use_ai = False

    def generate_title(self, moment: Dict[str, Any], niche: str = 'gaming',
                       platform: str = 'youtube_shorts') -> str:
        """
        Generate clickbait-style title for the clip.

        Args:
            moment: Moment data with quote and type
            niche: Game niche/category
            platform: Target platform

        Returns:
            Optimized title text
        """
        quote = moment.get('quote', '').strip()
        moment_type = moment.get('type', 'exciting')

        # Platform-specific length limits
        length_limits = {
            'youtube_shorts': 100,
            'tiktok': 150,
            'instagram_reels': 125
        }

        max_length = length_limits.get(platform, 100)

        # Use AI if available
        if self.use_ai:
            title = self._generate_ai_title(quote, moment_type, niche, max_length)
            if title:
                return title

        # Fallback to template-based generation
        title_templates = {
            'exciting': [
                f"OMG! {self._truncate_quote(quote, 30)} 😱🔥",
                f"YOU WON'T BELIEVE THIS! {self._truncate_quote(quote, 25)}",
                f"INSANE MOMENT! {self._truncate_quote(quote, 30)} 🔥",
                f"WTF?! {self._truncate_quote(quote, 30)} 💀"
            ],
            'funny': [
                f"LMFAO! {self._truncate_quote(quote, 30)} 😂",
                f"THIS IS HILARIOUS! {self._truncate_quote(quote, 25)}",
                f"CAN'T STOP LAUGHING! {self._truncate_quote(quote, 30)} 🤣",
                f"BRUH! {self._truncate_quote(quote, 30)} 😭"
            ],
            'shocking': [
                f"NO WAY! {self._truncate_quote(quote, 30)} 😱",
                f"ARE YOU SERIOUS?! {self._truncate_quote(quote, 25)}",
                f"I'M SHOOK! {self._truncate_quote(quote, 30)} 💀",
                f"THIS CHANGED EVERYTHING! {self._truncate_quote(quote, 25)}"
            ],
            'emotional': [
                f"This hit different... {self._truncate_quote(quote, 30)} 😢",
                f"WHY DID I WATCH THIS 😭",
                f"My heart... {self._truncate_quote(quote, 25)} 💔",
                f"NOT ME CRYING 😭🤧"
            ]
        }

        templates = title_templates.get(moment_type, title_templates['exciting'])
        title = random.choice(templates)

        # Add niche context
        if niche and niche != 'gaming':
            title = f"[{niche}] {title}"

        # Ensure length limit
        if len(title) > max_length:
            title = title[:max_length-3] + '...'

        return title

    def _generate_ai_title(self, quote: str, moment_type: str,
                            niche: str, max_length: int) -> Optional[str]:
        """Use Gemini AI to generate optimized title."""
        try:
            prompt = f"""Generate a viral, clickbait-style title for a gaming clip.

Requirements:
- Moment type: {moment_type}
- Quote: "{quote}"
- Game: {niche}
- Platform: YouTube Shorts/TikTok/Instagram Reels
- Max length: {max_length} characters
- Use emojis but don't overdo it (2-3 max)
- Make it exciting and shareable
- MUST include the quote or a variation of it

Return ONLY the title, no explanation."""

            response = self.model.generate_content(prompt)
            title = response.text.strip()

            # Remove markdown if present
            if title.startswith('```'):
                title = title.strip('```').strip()

            # Clean up quotes
            title = title.strip('"').strip("'")

            if len(title) <= max_length and len(title) > 10:
                return title

            return None

        except Exception as e:
            logger.warning(f"AI title generation failed: {e}")
            return None

    def _truncate_quote(self, quote: str, max_chars: int) -> str:
        """Truncate quote while keeping it readable."""
        if len(quote) <= max_chars:
            return quote
        return quote[:max_chars-3] + '...'

    def generate_description(self, moment: Dict[str, Any], niche: str = 'gaming',
                             platform: str = 'youtube_shorts') -> str:
        """Generate optimized description for the clip."""
        quote = moment.get('quote', '').strip()
        moment_type = moment.get('type', 'exciting')

        # Platform-specific templates
        if platform == 'youtube_shorts':
            desc = f"{quote}\n\n⬇️ SUBSCRIBE for more {niche} content!\n\n🔥 Turn on notifications 🔥\n\n🎮 Like, Comment & Share!\n\n"
        elif platform == 'tiktok':
            desc = f"{quote} #{niche.replace(' ', '')}\n\nFollow for more 🔥"
        else:  # instagram_reels
            desc = f"{quote}\n.\n.\n.\n#{niche.replace(' ', '')} #gaming #viral"

        return desc

    def generate_hashtags(self, niche: str, moment_type: str = 'exciting',
                          count: int = 15) -> List[str]:
        """
        Generate relevant hashtags.

        Args:
            niche: Game category
            moment_type: Type of moment (exciting, funny, etc.)
            count: Number of hashtags to generate

        Returns:
            List of hashtag strings
        """
        hashtags = set()

        # Add general gaming hashtags
        hashtags.update(GAMING_HASHTAGS[:8])

        # Add niche-specific hashtags
        if niche in NICHES_TO_HASHTAGS:
            hashtags.update(NICHES_TO_HASHTAGS[niche])

        # Add moment-specific hashtags
        moment_hashtags = {
            'exciting': ['#epic', '#insane', '#crazy', '#unreal', '#skill'],
            'funny': ['#funny', '#hilarious', '#lol', '#comedy', '#lmao'],
            'shocking': ['#wtf', '#shocking', '#unbelievable', '#insane', '#viral'],
            'emotional': ['#emotional', '#sad', '#wholesome', '#feels', '#wholesomegaming']
        }
        hashtags.update(moment_hashtags.get(moment_type, []))

        # Convert to list and shuffle
        hashtag_list = list(hashtags)
        random.shuffle(hashtag_list)

        # Return requested count
        return hashtag_list[:count]

    def generate_metadata(self, moment: Dict[str, Any], niche: str = 'gaming',
                          platform: str = 'youtube_shorts') -> Dict[str, Any]:
        """
        Generate complete metadata package for a clip.

        Returns:
            Dictionary with title, description, hashtags
        """
        title = self.generate_title(moment, niche, platform)
        description = self.generate_description(moment, niche, platform)
        hashtags = self.generate_hashtags(niche, moment.get('type', 'exciting'))

        return {
            'title': title,
            'description': description,
            'hashtags': hashtags,
            'platform': platform,
            'niche': niche
        }

def main():
    """Test SEO generator."""
    moment = {
        'start': 30.5,
        'end': 45.0,
        'type': 'exciting',
        'quote': 'I can\'t believe I just pulled that off!'
    }

    generator = SEOGenerator()

    # Generate for different platforms
    for platform in ['youtube_shorts', 'tiktok', 'instagram_reels']:
        metadata = generator.generate_metadata(moment, 'Fortnite', platform)
        print(f"\n{platform.upper()}:")
        print(f"Title: {metadata['title']}")
        print(f"Description: {metadata['description']}")
        print(f"Hashtags: {' '.join(metadata['hashtags'][:10])}")

if __name__ == '__main__':
    main()
