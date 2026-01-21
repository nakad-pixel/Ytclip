#!/usr/bin/env python3
"""
Quality Assurance Module: Validate clips and ensure compliance
Checks for profanity, copyright issues, and quality standards.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic profanity filter list (expandable)
PROFANITY_LIST = [
    'fuck', 'shit', 'bitch', 'ass', 'damn', 'hell',
    'nigger', 'nigga', 'fag', 'faggot', 'retard'
]

class QualityAssurance:
    """Validate clips for quality and compliance."""

    def __init__(self, strictness: str = 'strict'):
        """
        Initialize QA checker.

        Args:
            strictness: 'strict', 'moderate', or 'lenient'
        """
        self.strictness = strictness
        self.profanity_pattern = re.compile(
            r'\b(' + '|'.join(PROFANITY_LIST) + r')\b',
            re.IGNORECASE
        )

    def check_clip(self, clip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive QA check on a clip.

        Args:
            clip_data: Dictionary with clip information including:
                - clip_path: Path to video file
                - quote: Text content
                - duration: Clip length in seconds
                - platform: Target platform

        Returns:
            QA report with pass/fail status and issues
        """
        report = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'scores': {}
        }

        # Check duration
        duration_score, duration_issues = self._check_duration(clip_data)
        report['scores']['duration'] = duration_score
        report['issues'].extend(duration_issues)

        # Check content
        content_score, content_issues = self._check_content(clip_data)
        report['scores']['content'] = content_score
        report['issues'].extend(content_issues)

        # Check profanity
        profanity_score, profanity_issues = self._check_profanity(clip_data)
        report['scores']['profanity'] = profanity_score
        report['warnings'].extend(profanity_issues)

        # Check copyright
        copyright_score, copyright_issues = self._check_copyright(clip_data)
        report['scores']['copyright'] = copyright_score
        report['issues'].extend(copyright_issues)

        # Calculate overall score
        report['overall_score'] = sum(report['scores'].values()) / len(report['scores'])

        # Determine pass/fail based on strictness
        thresholds = {
            'strict': 85,
            'moderate': 70,
            'lenient': 60
        }
        threshold = thresholds.get(self.strictness, 70)

        report['passed'] = (
            report['overall_score'] >= threshold and
            len([i for i in report['issues'] if i['severity'] == 'critical']) == 0
        )

        return report

    def _check_duration(self, clip_data: Dict[str, Any]) -> tuple[int, List[Dict]]:
        """Check if clip duration is appropriate."""
        issues = []
        score = 100

        duration = clip_data.get('duration', clip_data.get('end', 0) - clip_data.get('start', 0))

        # Platform-specific limits
        platform_limits = {
            'youtube_shorts': {'min': 5, 'max': 60},
            'tiktok': {'min': 5, 'max': 180},
            'instagram_reels': {'min': 5, 'max': 90}
        }

        platform = clip_data.get('platform', 'youtube_shorts')
        limits = platform_limits.get(platform, platform_limits['youtube_shorts'])

        if duration < limits['min']:
            issues.append({
                'type': 'duration',
                'severity': 'warning',
                'message': f"Clip too short: {duration:.1f}s (min: {limits['min']}s)"
            })
            score -= 20
        elif duration > limits['max']:
            issues.append({
                'type': 'duration',
                'severity': 'critical',
                'message': f"Clip too long: {duration:.1f}s (max: {limits['max']}s)"
            })
            score -= 50
        elif duration < 10:
            # Very short clips are less viral
            issues.append({
                'type': 'duration',
                'severity': 'info',
                'message': f"Clip is short: {duration:.1f}s (optimal: 15-30s)"
            })
            score -= 10

        return max(0, score), issues

    def _check_content(self, clip_data: Dict[str, Any]) -> tuple[int, List[Dict]]:
        """Check content quality."""
        issues = []
        score = 100

        quote = clip_data.get('quote', '')
        if not quote or len(quote) < 5:
            issues.append({
                'type': 'content',
                'severity': 'warning',
                'message': 'Quote is too short or empty'
            })
            score -= 30

        # Check for meaningful content
        meaningful_words = len([w for w in quote.split() if len(w) > 2])
        if meaningful_words < 3:
            issues.append({
                'type': 'content',
                'severity': 'warning',
                'message': 'Quote lacks meaningful content'
            })
            score -= 20

        return max(0, score), issues

    def _check_profanity(self, clip_data: Dict[str, Any]) -> tuple[int, List[Dict]]:
        """Check for profanity in text."""
        warnings = []

        quote = clip_data.get('quote', '')
        if not quote:
            return 100, warnings

        # Find profanity
        matches = self.profanity_pattern.findall(quote)

        if matches:
            if self.strictness == 'strict':
                return 0, [{
                    'type': 'profanity',
                    'severity': 'warning',
                    'message': f'Profanity detected: {", ".join(matches)}'
                }]
            else:
                warnings.append({
                    'type': 'profanity',
                    'severity': 'info',
                    'message': f'Profanity detected: {", ".join(matches)}'
                })
                return 80, warnings

        return 100, warnings

    def _check_copyright(self, clip_data: Dict[str, Any]) -> tuple[int, List[Dict]]:
        """
        Check for potential copyright issues.
        Note: This is a basic check. Real copyright detection requires more advanced tools.
        """
        issues = []
        score = 100

        # Check for common copyright indicators in quote
        quote = clip_data.get('quote', '').lower()
        copyright_indicators = [
            'copyright', 'licensed', 'owned by', 'property of',
            'all rights reserved', 'official'
        ]

        for indicator in copyright_indicators:
            if indicator in quote:
                issues.append({
                    'type': 'copyright',
                    'severity': 'warning',
                    'message': f'Possible copyright mention: "{indicator}"'
                })
                score -= 30
                break

        return max(0, score), issues

    def batch_check_clips(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run QA checks on multiple clips."""
        reports = []
        for clip in clips:
            report = self.check_clip(clip)
            report['clip_data'] = clip
            reports.append(report)

        passed = sum(1 for r in reports if r['passed'])
        logger.info(f"QA: {passed}/{len(clips)} clips passed")

        return reports

def main():
    """Test QA module."""
    # Test case 1: Good clip
    good_clip = {
        'clip_path': 'test.mp4',
        'quote': 'I can\'t believe I just pulled that off!',
        'start': 30.0,
        'end': 45.0,
        'platform': 'youtube_shorts'
    }

    # Test case 2: Clip with issues
    bad_clip = {
        'clip_path': 'test2.mp4',
        'quote': 'This is short',
        'start': 30.0,
        'end': 65.0,  # Too long for YouTube
        'platform': 'youtube_shorts'
    }

    qa = QualityAssurance(strictness='strict')

    for clip in [good_clip, bad_clip]:
        report = qa.check_clip(clip)
        print(f"\nClip: {clip['clip_path']}")
        print(f"Passed: {report['passed']}")
        print(f"Overall Score: {report['overall_score']:.1f}")
        print(f"Issues: {len(report['issues'])}")
        for issue in report['issues']:
            print(f"  - [{issue['severity']}] {issue['message']}")

if __name__ == '__main__':
    main()
