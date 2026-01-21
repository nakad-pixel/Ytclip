#!/usr/bin/env python3
"""
Analytics Module: Track performance metrics from all platforms
Fetches views, likes, comments, and calculates success metrics.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

try:
    from .publishers.youtube import YouTubePublisher
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsTracker:
    """Track and analyze performance metrics from platforms."""

    def __init__(self, db_path: str = 'data/videos.db'):
        """
        Initialize analytics tracker.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.youtube_publisher = None

        if YOUTUBE_AVAILABLE:
            try:
                self.youtube_publisher = YouTubePublisher()
            except Exception as e:
                logger.warning(f"Could not initialize YouTube publisher: {e}")

        self._init_tables()

    def _init_tables(self):
        """Initialize analytics tables in database."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create clips table for tracking published clips
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT,
                video_id TEXT,
                platform TEXT,
                published_at TEXT,
                title TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                last_updated TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def track_clip(self, platform: str, video_id: str, youtube_id: str,
                    title: str) -> None:
        """
        Track a published clip in the database.

        Args:
            platform: Platform name
            video_id: Platform's video ID
            youtube_id: Original YouTube video ID
            title: Clip title
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO clips (youtube_id, video_id, platform, published_at, title, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (youtube_id, video_id, platform, datetime.now().isoformat(), title, datetime.now().isoformat()))

            conn.commit()
            logger.info(f"Tracked clip: {platform}/{video_id}")

        except Exception as e:
            logger.error(f"Failed to track clip: {e}")
        finally:
            conn.close()

    def fetch_metrics(self, platform: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Fetch metrics for published clips.

        Args:
            platform: Optional platform filter
            hours: Hours since publication to fetch

        Returns:
            List of clip metrics
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get clips published within time window
            cutoff_time = datetime.now() - timedelta(hours=hours)

            query = 'SELECT * FROM clips WHERE published_at >= ?'
            params = [cutoff_time.isoformat()]

            if platform:
                query += ' AND platform = ?'
                params.append(platform)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            clips = []
            for row in rows:
                clip = {
                    'id': row[0],
                    'youtube_id': row[1],
                    'video_id': row[2],
                    'platform': row[3],
                    'published_at': row[4],
                    'title': row[5],
                    'views': row[6],
                    'likes': row[7],
                    'comments': row[8],
                    'last_updated': row[9]
                }
                clips.append(clip)

            return clips

        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            return []
        finally:
            conn.close()

    def update_metrics(self, platform: str, video_id: str,
                       metrics: Dict[str, int]) -> bool:
        """
        Update metrics for a clip.

        Args:
            platform: Platform name
            video_id: Platform's video ID
            metrics: Dictionary with views, likes, comments

        Returns:
            True if successful, False otherwise
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE clips
                SET views = ?, likes = ?, comments = ?, last_updated = ?
                WHERE platform = ? AND video_id = ?
            ''', (
                metrics.get('views', 0),
                metrics.get('likes', 0),
                metrics.get('comments', 0),
                datetime.now().isoformat(),
                platform,
                video_id
            ))

            conn.commit()
            logger.info(f"Updated metrics for {platform}/{video_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return False
        finally:
            conn.close()

    def refresh_youtube_metrics(self) -> int:
        """
        Fetch and update metrics from YouTube API.

        Returns:
            Number of clips updated
        """
        if not self.youtube_publisher:
            logger.warning("YouTube publisher not available")
            return 0

        clips = self.fetch_metrics(platform='youtube', hours=24 * 7)  # Last 7 days
        updated_count = 0

        for clip in clips:
            metrics = self.youtube_publisher.get_video_stats(clip['video_id'])

            if metrics:
                success = self.update_metrics('youtube', clip['video_id'], metrics)
                if success:
                    updated_count += 1

        logger.info(f"Refreshed {updated_count}/{len(clips)} YouTube clips")
        return updated_count

    def get_top_performers(self, platform: str = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing clips by views.

        Args:
            platform: Optional platform filter
            limit: Number of results

        Returns:
            List of top clips
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM clips WHERE views > 0'
            params = []

            if platform:
                query += ' AND platform = ?'
                params.append(platform)

            query += ' ORDER BY views DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            clips = []
            for row in rows:
                clip = {
                    'id': row[0],
                    'youtube_id': row[1],
                    'video_id': row[2],
                    'platform': row[3],
                    'published_at': row[4],
                    'title': row[5],
                    'views': row[6],
                    'likes': row[7],
                    'comments': row[8],
                    'engagement_rate': self._calculate_engagement_rate(row[6], row[7])
                }
                clips.append(clip)

            return clips

        except Exception as e:
            logger.error(f"Failed to get top performers: {e}")
            return []
        finally:
            conn.close()

    def _calculate_engagement_rate(self, views: int, likes: int) -> float:
        """Calculate engagement rate (likes/views)."""
        if views == 0:
            return 0.0
        return round((likes / views) * 100, 2)

    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate analytics report.

        Args:
            hours: Time window in hours

        Returns:
            Report dictionary
        """
        clips = self.fetch_metrics(hours=hours)

        if not clips:
            return {
                'total_clips': 0,
                'total_views': 0,
                'total_likes': 0,
                'top_clip': None,
                'platform_breakdown': {}
            }

        total_views = sum(c['views'] for c in clips)
        total_likes = sum(c['likes'] for c in clips)

        # Find top clip
        top_clip = max(clips, key=lambda x: x['views']) if clips else None

        # Platform breakdown
        platform_breakdown = {}
        for clip in clips:
            platform = clip['platform']
            if platform not in platform_breakdown:
                platform_breakdown[platform] = {
                    'count': 0,
                    'views': 0,
                    'likes': 0
                }
            platform_breakdown[platform]['count'] += 1
            platform_breakdown[platform]['views'] += clip['views']
            platform_breakdown[platform]['likes'] += clip['likes']

        report = {
            'period_hours': hours,
            'total_clips': len(clips),
            'total_views': total_views,
            'total_likes': total_likes,
            'avg_views_per_clip': round(total_views / len(clips), 1) if clips else 0,
            'top_clip': {
                'title': top_clip['title'],
                'views': top_clip['views'],
                'platform': top_clip['platform']
            } if top_clip else None,
            'platform_breakdown': platform_breakdown
        }

        return report

def main():
    """Test analytics tracker."""
    tracker = AnalyticsTracker()

    # Generate report
    report = tracker.generate_report(hours=24 * 7)

    print(f"\nAnalytics Report (Last 7 days):")
    print(f"Total clips: {report['total_clips']}")
    print(f"Total views: {report['total_views']:,}")
    print(f"Total likes: {report['total_likes']:,}")
    print(f"Avg views per clip: {report['avg_views_per_clip']}")

    if report['top_clip']:
        print(f"\nTop clip:")
        print(f"  Title: {report['top_clip']['title']}")
        print(f"  Views: {report['top_clip']['views']:,}")
        print(f"  Platform: {report['top_clip']['platform']}")

    print(f"\nPlatform breakdown:")
    for platform, stats in report['platform_breakdown'].items():
        print(f"  {platform}: {stats['count']} clips, {stats['views']:,} views")

if __name__ == '__main__':
    main()
