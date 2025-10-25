"""
Database storage for tracking announcements and courses.

Uses SQLite for persistent storage with automatic migrations.
"""
import os
import json
import sqlite3
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from .parser import Course, Announcement

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for announcement tracking."""
    
    def __init__(self, db_path: str = "data/announcements.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Courses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Announcements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    preview TEXT,
                    author TEXT,
                    date TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0,
                    FOREIGN KEY (course_id) REFERENCES courses(id)
                )
            """)
            
            # Metadata table for tracking check times
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_announcements_course
                ON announcements(course_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_announcements_notified
                ON announcements(course_id, notified)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_announcements_first_seen
                ON announcements(first_seen)
            """)
            
            conn.commit()
            
        logger.debug("Database initialized")
    
    def save_courses(self, courses: List[Course]):
        """
        Save or update courses in database.
        
        Args:
            courses: List of Course objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for course in courses:
                cursor.execute("""
                    INSERT OR REPLACE INTO courses (id, name, url, last_checked)
                    VALUES (?, ?, ?, ?)
                """, (course.id, course.name, course.url, datetime.now()))
            
            conn.commit()
            
        logger.info(f"💾 Saved {len(courses)} course(s) to database")
    
    def get_courses(self) -> List[Course]:
        """
        Retrieve all courses from database.
        
        Returns:
            List of Course objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, url FROM courses ORDER BY name")
            
            courses = []
            for row in cursor.fetchall():
                courses.append(Course(row[0], row[1], row[2]))
            
            return courses
    
    def get_new_announcements(
        self,
        course_id: str,
        announcements: List[Announcement]
    ) -> List[Announcement]:
        """
        Identify new announcements that haven't been seen before.
        
        Args:
            course_id: Course identifier
            announcements: Current list of announcements
            
        Returns:
            List of new announcements
        """
        if not announcements:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get existing announcement URLs for this course
            cursor.execute("""
                SELECT url FROM announcements
                WHERE course_id = ?
            """, (course_id,))
            
            existing_urls = {row[0] for row in cursor.fetchall()}
        
        # Filter to only new announcements
        new_announcements = [
            ann for ann in announcements
            if ann.url not in existing_urls
        ]
        
        return new_announcements
    
    def save_announcements(
        self,
        course_id: str,
        announcements: List[Announcement],
        mark_notified: bool = False
    ):
        """
        Save announcements to database.
        
        Args:
            course_id: Course identifier
            announcements: List of Announcement objects
            mark_notified: Whether to mark as notified (default: False)
        """
        if not announcements:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for ann in announcements:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO announcements
                        (course_id, title, url, preview, author, date, notified)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        course_id,
                        ann.title,
                        ann.url,
                        ann.preview,
                        ann.author,
                        ann.date,
                        1 if mark_notified else 0
                    ))
                except sqlite3.IntegrityError:
                    # URL already exists, skip
                    continue
            
            conn.commit()
        
        logger.debug(f"Saved {len(announcements)} announcement(s) for course {course_id}")
    
    def mark_as_notified(self, course_id: str, announcement_urls: List[str]):
        """
        Mark announcements as notified.
        
        Args:
            course_id: Course identifier
            announcement_urls: List of announcement URLs to mark
        """
        if not announcement_urls:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(announcement_urls))
            cursor.execute(f"""
                UPDATE announcements
                SET notified = 1
                WHERE course_id = ? AND url IN ({placeholders})
            """, [course_id] + announcement_urls)
            
            conn.commit()
        
        logger.debug(f"Marked {len(announcement_urls)} announcement(s) as notified")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total courses
            cursor.execute("SELECT COUNT(*) FROM courses")
            total_courses = cursor.fetchone()[0]
            
            # Total announcements
            cursor.execute("SELECT COUNT(*) FROM announcements")
            total_announcements = cursor.fetchone()[0]
            
            # New (unnotified) announcements
            cursor.execute("SELECT COUNT(*) FROM announcements WHERE notified = 0")
            unnotified = cursor.fetchone()[0]
            
            # Courses with new announcements
            cursor.execute("""
                SELECT COUNT(DISTINCT course_id)
                FROM announcements
                WHERE notified = 0
            """)
            courses_with_new = cursor.fetchone()[0]
            
            return {
                'total_courses': total_courses,
                'total_announcements': total_announcements,
                'unnotified_announcements': unnotified,
                'courses_with_new': courses_with_new
            }
    
    def cleanup_old_announcements(self, days: int = 90):
        """
        Remove old announcements to keep database size manageable.
        
        Args:
            days: Remove announcements older than this many days
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM announcements
                WHERE first_seen < datetime('now', '-' || ? || ' days')
                AND notified = 1
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
        
        if deleted > 0:
            logger.info(f"🗑️  Cleaned up {deleted} old announcement(s)")
    
    def get_last_check_time(self) -> Optional[datetime]:
        """
        Get the timestamp of the last check.
        
        Returns:
            Datetime of last check, or None if never checked
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT value FROM metadata WHERE key = 'last_check_time'
                """)
                result = cursor.fetchone()
                
                if result:
                    return datetime.fromisoformat(result[0])
                return None
        except Exception as e:
            logger.debug(f"Error getting last check time: {e}")
            return None
    
    def update_last_check_time(self, check_time: Optional[datetime] = None):
        """
        Update the last check timestamp.
        
        Args:
            check_time: Datetime to record (defaults to now)
        """
        if check_time is None:
            check_time = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES ('last_check_time', ?, ?)
            """, (check_time.isoformat(), datetime.now()))
            conn.commit()
        
        logger.debug(f"Updated last check time to {check_time}")
    
    def get_recent_new_announcements(
        self,
        course_id: str,
        since: datetime
    ) -> List[Dict]:
        """
        Get new announcements for a course that appeared since a given time.
        
        Args:
            course_id: Course identifier
            since: Only return announcements first seen after this time
            
        Returns:
            List of announcement dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, course_id, title, url, preview, author, date, first_seen, notified
                FROM announcements
                WHERE course_id = ?
                AND first_seen >= ?
                AND notified = 0
                ORDER BY first_seen DESC
            """, (course_id, since.isoformat()))
            
            announcements = []
            for row in cursor.fetchall():
                announcements.append({
                    'id': row[0],
                    'course_id': row[1],
                    'title': row[2],
                    'url': row[3],
                    'preview': row[4],
                    'author': row[5],
                    'date': row[6],
                    'first_seen': row[7],
                    'notified': row[8]
                })
            
            return announcements


class CourseCache:
    """JSON-based cache for enrolled courses."""
    
    def __init__(self, cache_file: str = "data/courses.json"):
        """
        Initialize course cache.
        
        Args:
            cache_file: Path to JSON cache file
        """
        self.cache_file = cache_file
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    def save_courses(self, courses: List[Course]):
        """
        Save courses to cache file.
        
        Args:
            courses: List of Course objects
        """
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'courses': [course.to_dict() for course in courses]
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Cached {len(courses)} course(s)")
            
        except Exception as e:
            logger.error(f"Failed to save course cache: {e}")
    
    def load_courses(self) -> Optional[List[Course]]:
        """
        Load courses from cache file.
        
        Returns:
            List of Course objects or None if cache doesn't exist/is invalid
        """
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            courses = [Course.from_dict(c) for c in data.get('courses', [])]
            
            if courses:
                logger.info(f"✅ Loaded {len(courses)} course(s) from cache")
                logger.info(f"   Last updated: {data.get('last_updated', 'Unknown')}")
            
            return courses
            
        except Exception as e:
            logger.debug(f"Could not load course cache: {e}")
            return None
    
    def is_cache_fresh(self, max_age_hours: int = 24) -> bool:
        """
        Check if cache is fresh enough to use.
        
        Args:
            max_age_hours: Maximum age in hours before cache is stale
            
        Returns:
            True if cache is fresh
        """
        try:
            if not os.path.exists(self.cache_file):
                return False
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            last_updated = datetime.fromisoformat(data.get('last_updated', ''))
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600
            
            return age_hours < max_age_hours
            
        except Exception:
            return False


class ConfigManager:
    """Manages configuration for selective course monitoring."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize config manager.
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create default config if it doesn't exist."""
        if not os.path.exists(self.config_file):
            default_config = {
                "monitor_all_courses": True,
                "monitored_course_ids": [],
                "excluded_course_ids": [],
                "check_interval_minutes": 30,
                "notification_settings": {
                    "send_email": True,
                    "send_error_alerts": True
                },
                "database_cleanup_days": 90
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"✅ Created default config: {self.config_file}")
    
    def load_config(self) -> Dict:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def should_monitor_course(self, course_id: str) -> bool:
        """
        Check if a course should be monitored based on config.
        
        Args:
            course_id: Course identifier
            
        Returns:
            True if course should be monitored
        """
        config = self.load_config()
        
        # Check exclusion list first
        if course_id in config.get('excluded_course_ids', []):
            return False
        
        # If monitor_all_courses is True, monitor everything (except excluded)
        if config.get('monitor_all_courses', True):
            return True
        
        # Otherwise, only monitor specifically listed courses
        return course_id in config.get('monitored_course_ids', [])
    
    def get_check_interval(self) -> int:
        """
        Get check interval in minutes.
        
        Returns:
            Interval in minutes
        """
        config = self.load_config()
        return config.get('check_interval_minutes', 30)
    
    def get_notification_settings(self) -> Dict[str, bool]:
        """
        Get notification settings.
        
        Returns:
            Dictionary with notification preferences
        """
        config = self.load_config()
        return config.get('notification_settings', {
            'send_email': True,
            'send_error_alerts': True
        })

