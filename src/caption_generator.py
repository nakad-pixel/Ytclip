#!/usr/bin/env python3
"""
Caption Generator: Create gaming-style captions for clips
Generates dynamic, engaging text overlays that match gaming content style.
"""

import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CaptionGenerator:
    """Generate gaming-style captions for video clips."""

    # Gaming-style prefix/suffix words for emphasis
    EMPHASIS_WORDS = {
        'exciting': ['INSANE!', 'OMG!', 'WTF?!', 'LET\'S GO!', 'NO WAY!', 'HOLY!'],
        'funny': ['LOL', 'LMAO', 'BRUH', 'GET REKT', 'SKILL ISSUE', 'WHY?!'],
        'shocking': ['WTF?!', 'NO WAY!', 'ARE YOU KIDDING?!', 'IMPOSSIBLE!', 'WHY?!'],
        'emotional': ['...', '😢', '😭', 'NOOO!', 'MY HEART', 'PAIN']
    }

    # Color schemes for different moment types
    COLORS = {
        'exciting': 'yellow',
        'funny': 'cyan',
        'shocking': 'red',
        'emotional': 'white'
    }

    def __init__(self, style: str = 'gaming'):
        """
        Initialize caption generator.

        Args:
            style: Caption style ('gaming', 'minimal', 'bold')
        """
        self.style = style

    def generate_caption(self, moment: Dict[str, Any], quote: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a caption for a viral moment.

        Args:
            moment: Moment data from analyzer
            quote: Optional quote override

        Returns:
            Caption data with text, timing, and style
        """
        moment_type = moment.get('type', 'exciting')
        base_quote = quote or moment.get('quote', '')

        # Add emphasis prefix based on type
        emphasis = self._get_emphasis_word(moment_type)

        # Build caption text
        if self.style == 'gaming':
            # Gaming style: UPPERCASE with emojis
            caption_text = f"{emphasis} {base_quote.upper()}"
        elif self.style == 'minimal':
            # Minimal style: Just the quote
            caption_text = base_quote
        else:  # bold
            # Bold style: Emphasis + quote
            caption_text = f"{emphasis} {base_quote}"

        # Determine color
        color = self.COLORS.get(moment_type, 'yellow')

        return {
            'text': caption_text,
            'start': moment['start'],
            'end': moment['end'],
            'color': color,
            'style': self.style,
            'type': moment_type
        }

    def _get_emphasis_word(self, moment_type: str) -> str:
        """Get a random emphasis word for the moment type."""
        import random
        words = self.EMPHASIS_WORDS.get(moment_type, self.EMPHASIS_WORDS['exciting'])
        return random.choice(words)

    def generate_captions_for_moments(self, moments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate captions for multiple moments."""
        captions = []
        for moment in moments:
            caption = self.generate_caption(moment)
            captions.append(caption)
        return captions

    def create_word_by_word_captions(self, moment: Dict[str, Any],
                                     quote: Optional[str = None]) -> List[Dict[str, Any]]:
        """
        Create word-by-word animated captions (karaoke style).
        Each word appears at a specific time.
        """
        moment_type = moment.get('type', 'exciting')
        base_quote = quote or moment.get('quote', '')

        if not base_quote:
            return []

        # Split quote into words
        words = base_quote.split()
        if not words:
            return []

        # Calculate timing for each word
        duration = moment['end'] - moment['start']
        word_duration = duration / len(words)

        captions = []
        color = self.COLORS.get(moment_type, 'yellow')

        for i, word in enumerate(words):
            word_start = moment['start'] + (i * word_duration)
            word_end = word_start + word_duration

            captions.append({
                'text': word.upper() if self.style == 'gaming' else word,
                'start': word_start,
                'end': word_end,
                'color': color,
                'style': self.style
            })

        return captions

    def create_punchline_caption(self, moment: Dict[str, Any],
                                 punchline: str) -> Dict[str, Any]:
        """
        Create a special punchline caption that appears at the end of the clip.
        """
        # Punchline appears in last 2 seconds or 20% of the clip
        duration = moment['end'] - moment['start']
        punchline_duration = min(2.0, duration * 0.2)
        punchline_start = moment['end'] - punchline_duration

        return {
            'text': punchline.upper(),
            'start': punchline_start,
            'end': moment['end'],
            'color': 'red',
            'style': 'bold',
            'is_punchline': True
        }

    def add_reaction_captions(self, moment: Dict[str, Any],
                             reactions: List[str]) -> List[Dict[str, Any]]:
        """
        Add reaction captions at specific points during the clip.
        Reactions are placed at 25%, 50%, and 75% of the clip.
        """
        duration = moment['end'] - moment['start']
        if not reactions:
            return []

        # Place reactions at intervals
        positions = [0.25, 0.5, 0.75]
        captions = []

        for i, position in enumerate(positions):
            if i < len(reactions):
                timestamp = moment['start'] + (duration * position)
                captions.append({
                    'text': reactions[i].upper(),
                    'start': timestamp,
                    'end': timestamp + 1.0,  # Show for 1 second
                    'color': 'yellow',
                    'style': 'gaming',
                    'is_reaction': True
                })

        return captions

def main():
    """Test caption generator."""
    moment = {
        'start': 30.5,
        'end': 45.0,
        'type': 'exciting',
        'quote': 'I can\'t believe that just happened!'
    }

    generator = CaptionGenerator(style='gaming')

    # Test basic caption
    caption = generator.generate_caption(moment)
    print(f"Caption: {caption['text']}")
    print(f"Color: {caption['color']}")

    # Test word-by-word captions
    word_captions = generator.create_word_by_word_captions(moment)
    print(f"\nWord-by-word captions ({len(word_captions)} words):")
    for cap in word_captions:
        print(f"  [{cap['start']:.1f}s - {cap['end']:.1f}s] {cap['text']}")

if __name__ == '__main__':
    main()
