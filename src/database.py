#!/usr/bin/env python3
"""
Database Module: SQLite database operations
Handles all database interactions for tracking videos and clips.
"""

import os
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """Handle all database operations."""

    def __init__(self, db_path: str = 'data/videos.db'):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()
        self._init_tables()

    def _ensure_directory(self):
        """Ensure database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_tables(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Videos table for tracking discovered videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE,
                title TEXT,
                channel TEXT,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                published_at TEXT,
                niche TEXT,
                processed BOOLEAN DEFAULT 0,
                discovered_at TEXT,
                url TEXT,
                metadata_json TEXT,
                status TEXT DEFAULT 'discovered',
                virality_score REAL DEFAULT 0.0,
                analyzed_at TEXT,
                processed_at TEXT
            )
        ''')
        
        # Add new columns to existing tables (for backward compatibility)
        try:
            cursor.execute('ALTER TABLE videos ADD COLUMN status TEXT DEFAULT "discovered"')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE videos ADD COLUMN virality_score REAL DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE videos ADD COLUMN analyzed_at TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE videos ADD COLUMN processed_at TEXT')
        except sqlite3.OperationalError:
            pass

        # Clips table for tracking generated clips
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                qa_passed BOOLEAN DEFAULT 0,
                published BOOLEAN DEFAULT 0,
                published_at TEXT,
                platform_video_id TEXT,
                created_at TEXT
            )
        ''')

        # Analytics table for tracking performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id INTEGER,
                platform TEXT,
                platform_video_id TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                fetched_at TEXT,
                FOREIGN KEY (clip_id) REFERENCES clips(id)
            )
        ''')

        # System state table for tracking pipeline status
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    # Video operations

    def add_video(self, video_data: Dict[str, Any]) -> int:
        """
        Add a discovered video to database.

        Args:
            video_data: Video metadata

        Returns:
            Video ID (database ID)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO videos
                (youtube_id, title, channel, view_count, like_count, comment_count,
                 published_at, niche, discovered_at, url, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data.get('youtube_id'),
                video_data.get('title'),
                video_data.get('channel'),
                video_data.get('view_count', 0),
                video_data.get('like_count', 0),
                video_data.get('comment_count', 0),
                video_data.get('published_at'),
                video_data.get('niche'),
                video_data.get('discovered_at', datetime.now().isoformat()),
                video_data.get('url'),
                video_data.get('metadata_json')
            ))

            video_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Added video: {video_data.get('youtube_id')}")
            return video_id

        except sqlite3.IntegrityError:
            logger.debug(f"Video already exists: {video_data.get('youtube_id')}")
            return -1
        except Exception as e:
            logger.error(f"Error adding video: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()

    def get_video(self, youtube_id: str) -> Optional[Dict[str, Any]]:
        """Get video by YouTube ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM videos WHERE youtube_id = ?', (youtube_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_video_dict(row)
            return None

        except Exception as e:
            logger.error(f"Error getting video: {e}")
            return None
        finally:
            conn.close()

    def get_unprocessed_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of videos that haven't been processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM videos WHERE processed = 0 ORDER BY discovered_at DESC LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            return [self._row_to_video_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting unprocessed videos: {e}")
            return []
        finally:
            conn.close()

    def mark_video_processed(self, youtube_id: str) -> bool:
        """Mark video as processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE videos SET processed = 1 WHERE youtube_id = ?
            ''', (youtube_id,))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error marking video processed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # Clip operations

    def add_clip(self, clip_data: Dict[str, Any]) -> int:
        """Add a generated clip to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            import json
            cursor.execute('''
                INSERT INTO clips
                (youtube_id, clip_path, platform, start_time, end_time, moment_type,
                 quote, virality_score, title, description, hashtags, qa_passed,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                clip_data.get('youtube_id'),
                clip_data.get('clip_path'),
                clip_data.get('platform'),
                clip_data.get('start_time'),
                clip_data.get('end_time'),
                clip_data.get('moment_type'),
                clip_data.get('quote'),
                clip_data.get('virality_score'),
                clip_data.get('title'),
                clip_data.get('description'),
                json.dumps(clip_data.get('hashtags', [])),
                clip_data.get('qa_passed', False),
                clip_data.get('created_at', datetime.now().isoformat())
            ))

            clip_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Added clip: {clip_data.get('clip_path')}")
            return clip_id

        except Exception as e:
            logger.error(f"Error adding clip: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()

    def mark_clip_published(self, clip_id: int, platform_video_id: str,
                            platform: str) -> bool:
        """Mark clip as published."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE clips
                SET published = 1, platform_video_id = ?, published_at = ?
                WHERE id = ?
            ''', (platform_video_id, datetime.now().isoformat(), clip_id))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error marking clip published: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_unpublished_clips(self, platform: str = None) -> List[Dict[str, Any]]:
        """Get clips that haven't been published yet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM clips WHERE published = 0 AND qa_passed = 1'

            if platform:
                query += ' AND platform = ?'
                cursor.execute(query, (platform,))
            else:
                cursor.execute(query)

            rows = cursor.fetchall()
            return [self._row_to_clip_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting unpublished clips: {e}")
            return []
        finally:
            conn.close()

    # State operations

    def set_state(self, key: str, value: str) -> bool:
        """Set a state value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO state (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error setting state: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_state(self, key: str) -> Optional[str]:
        """Get a state value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT value FROM state WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else None

        except Exception as e:
            logger.error(f"Error getting state: {e}")
            return None
        finally:
            conn.close()

    # Phase 2 pipeline methods

    def get_discovered_videos(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all videos not yet analyzed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM videos 
                WHERE status = 'discovered' 
                ORDER BY discovered_at DESC 
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            return [self._row_to_video_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting discovered videos: {e}")
            return []
        finally:
            conn.close()

    def get_top_analyzed_videos(self, limit: int = 2, threshold: float = 70.0) -> List[Dict[str, Any]]:
        """Get top-scoring analyzed videos above threshold."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM videos 
                WHERE status = 'analyzed' AND virality_score >= ? 
                ORDER BY virality_score DESC 
                LIMIT ?
            ''', (threshold, limit))

            rows = cursor.fetchall()
            return [self._row_to_video_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting top analyzed videos: {e}")
            return []
        finally:
            conn.close()

    def update_video_status(self, youtube_id: str, status: str, 
                           virality_score: Optional[float] = None) -> bool:
        """Update video status and optionally virality score."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if virality_score is not None:
                # Update with virality score
                if status == 'analyzed':
                    cursor.execute('''
                        UPDATE videos 
                        SET status = ?, virality_score = ?, analyzed_at = ?
                        WHERE youtube_id = ?
                    ''', (status, virality_score, datetime.now().isoformat(), youtube_id))
                elif status == 'published':
                    cursor.execute('''
                        UPDATE videos 
                        SET status = ?, processed = 1, processed_at = ?
                        WHERE youtube_id = ?
                    ''', (status, datetime.now().isoformat(), youtube_id))
                else:
                    cursor.execute('''
                        UPDATE videos 
                        SET status = ?, virality_score = ?
                        WHERE youtube_id = ?
                    ''', (status, virality_score, youtube_id))
            else:
                # Update status only
                if status == 'published':
                    cursor.execute('''
                        UPDATE videos 
                        SET status = ?, processed = 1, processed_at = ?
                        WHERE youtube_id = ?
                    ''', (status, datetime.now().isoformat(), youtube_id))
                else:
                    cursor.execute('''
                        UPDATE videos 
                        SET status = ?
                        WHERE youtube_id = ?
                    ''', (status, youtube_id))

            conn.commit()
            logger.debug(f"Updated video {youtube_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating video status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # Helper methods

    def _row_to_video_dict(self, row) -> Dict[str, Any]:
        """Convert database row to video dictionary."""
        result = {
            'id': row[0],
            'youtube_id': row[1],
            'title': row[2],
            'channel': row[3],
            'view_count': row[4],
            'like_count': row[5],
            'comment_count': row[6],
            'published_at': row[7],
            'niche': row[8],
            'processed': bool(row[9]),
            'discovered_at': row[10],
            'url': row[11],
            'metadata_json': row[12]
        }
        
        # Add new phase 2 fields if they exist
        if len(row) > 13:
            result['status'] = row[13] if row[13] else 'discovered'
            result['virality_score'] = row[14] if row[14] else 0.0
            result['analyzed_at'] = row[15]
            result['processed_at'] = row[16]
        else:
            result['status'] = 'discovered'
            result['virality_score'] = 0.0
            result['analyzed_at'] = None
            result['processed_at'] = None
        
        return result

    def _row_to_clip_dict(self, row) -> Dict[str, Any]:
        """Convert database row to clip dictionary."""
        import json
        return {
            'id': row[0],
            'youtube_id': row[1],
            'clip_path': row[2],
            'platform': row[3],
            'start_time': row[4],
            'end_time': row[5],
            'moment_type': row[6],
            'quote': row[7],
            'virality_score': row[8],
            'title': row[9],
            'description': row[10],
            'hashtags': json.loads(row[11]) if row[11] else [],
            'qa_passed': bool(row[12]),
            'published': bool(row[13]),
            'published_at': row[14],
            'platform_video_id': row[15],
            'created_at': row[16]
        }

def main():
    """Test database operations."""
    db = Database()

    # Test adding a video
    video_data = {
        'youtube_id': 'test123',
        'title': 'Test Video',
        'channel': 'Test Channel',
        'view_count': 1000,
        'niche': 'Fortnite',
        'url': 'https://youtube.com/watch?v=test123'
    }

    video_id = db.add_video(video_data)
    print(f"Added video with ID: {video_id}")

    # Test retrieving video
    video = db.get_video('test123')
    print(f"Retrieved video: {video['title']}")

if __name__ == '__main__':
    main()
