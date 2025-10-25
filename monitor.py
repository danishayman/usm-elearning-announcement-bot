"""
Main monitoring module that orchestrates course checking and notifications.

Handles the core logic of fetching courses, checking announcements, and sending notifications.
"""
import os
import logging
import requests
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from login import USMLoginManager
from utils.parser import MoodleParser, Course, Announcement
from utils.storage import Database, CourseCache, ConfigManager
from utils.emailer import EmailNotifier

logger = logging.getLogger(__name__)


class ELearningMonitor:
    """Main monitoring class that orchestrates the checking process."""
    
    def __init__(
        self,
        usm_email: str,
        usm_password: str,
        smtp_user: str,
        smtp_pass: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        base_url: str = "https://elearning.usm.my/sidang2526",
        headless: bool = True
    ):
        """
        Initialize monitor.
        
        Args:
            usm_email: USM login email/username
            usm_password: USM password
            smtp_user: SMTP email for sending notifications
            smtp_pass: SMTP password
            smtp_server: SMTP server address
            smtp_port: SMTP port
            base_url: Moodle base URL
            headless: Run browser in headless mode
        """
        self.usm_email = usm_email
        self.usm_password = usm_password
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        
        # Initialize components
        self.parser = MoodleParser(base_url)
        self.db = Database()
        self.course_cache = CourseCache()
        self.config = ConfigManager()
        self.notifier = EmailNotifier(smtp_user, smtp_pass, smtp_server, smtp_port)
        
        # Session for making requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Track if we're logged in
        self.logged_in = False
    
    def authenticate(self, force: bool = False) -> bool:
        """
        Authenticate with USM Identity SSO.
        
        Note: Session persistence is disabled for security.
        Every authentication performs a fresh login.
        
        Args:
            force: Ignored (kept for API compatibility)
            
        Returns:
            True if authentication successful
        """
        try:
            logger.info("🔐 Authenticating with USM Identity (fresh login)...")
            
            with USMLoginManager(
                self.usm_email,
                self.usm_password,
                headless=self.headless
            ) as login_mgr:
                # Always performs fresh authentication (no session caching)
                cookies = login_mgr.get_authenticated_session(force_reauth=force)
                
                if cookies:
                    # Add cookies to requests session
                    for name, value in cookies.items():
                        self.session.cookies.set(name, value)
                    
                    self.logged_in = True
                    logger.info("✅ Authentication successful")
                    return True
                else:
                    logger.error("❌ Authentication failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def check_session_valid(self) -> bool:
        """
        Check if current session is still valid.
        
        Returns:
            True if session is valid
        """
        try:
            response = self.session.get(
                f"{self.base_url}/my/",
                timeout=30,
                allow_redirects=False
            )
            
            # If we get redirected to login, session expired
            if response.status_code == 302 and 'login' in response.headers.get('Location', ''):
                logger.warning("⚠️  Session expired")
                return False
            
            # Check if we can access the page
            if response.status_code == 200:
                content = response.text.lower()
                if 'dashboard' in content or 'my courses' in content:
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Session check error: {e}")
            return False
    
    def ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid authenticated session, reauthenticating if needed.
        
        Note: With session persistence disabled, this will check if we're already
        authenticated in this run, but will not reuse sessions across runs.
        
        Returns:
            True if we have a valid session
        """
        if self.logged_in and self.check_session_valid():
            logger.debug("Session still valid from current run")
            return True
        
        logger.info("🔄 Authenticating (session expired or first auth)...")
        return self.authenticate(force=True)
    
    def fetch_courses(self, use_cache: bool = True) -> List[Course]:
        """
        Fetch list of enrolled courses.
        
        Args:
            use_cache: Whether to use cached courses if available
            
        Returns:
            List of Course objects
        """
        # Try cache first if requested
        if use_cache:
            cached_courses = self.course_cache.load_courses()
            if cached_courses and self.course_cache.is_cache_fresh(max_age_hours=24):
                return cached_courses
        
        # Fetch from server
        logger.info("📚 Fetching enrolled courses...")
        
        if not self.ensure_authenticated():
            logger.error("Cannot fetch courses - authentication failed")
            return []
        
        try:
            response = self.session.get(f"{self.base_url}/my/", timeout=30)
            response.raise_for_status()
            
            courses = self.parser.extract_courses(response.text)
            
            if courses:
                # Save to cache and database
                self.course_cache.save_courses(courses)
                self.db.save_courses(courses)
            
            return courses
            
        except requests.RequestException as e:
            logger.error(f"❌ Error fetching courses: {e}")
            
            # Try to return cached courses as fallback
            cached_courses = self.course_cache.load_courses()
            if cached_courses:
                logger.warning("⚠️  Using cached courses as fallback")
                return cached_courses
            
            return []
    
    def check_course_announcements(
        self,
        course: Course,
        fetch_full_content: bool = True
    ) -> List[Announcement]:
        """
        Check a single course for announcements.
        
        Args:
            course: Course to check
            fetch_full_content: Whether to fetch full announcement content
            
        Returns:
            List of new announcements
        """
        try:
            logger.info(f"📖 Checking: {course.name}")
            
            if not self.ensure_authenticated():
                logger.error("Cannot check course - authentication failed")
                return []
            
            # Get course page
            response = self.session.get(course.url, timeout=30)
            response.raise_for_status()
            
            # Find announcement forum
            forum_url = self.parser.find_announcement_forum(response.text)
            
            if not forum_url:
                logger.info("   ℹ️  No announcement forum found")
                return []
            
            # Get forum page
            response = self.session.get(forum_url, timeout=30)
            response.raise_for_status()
            
            # Extract announcements
            announcements = self.parser.extract_announcements(response.text)
            
            if not announcements:
                logger.info("   ℹ️  No announcements in forum")
                return []
            
            logger.info(f"   📝 Found {len(announcements)} total announcement(s)")
            
            # Identify new announcements
            new_announcements = self.db.get_new_announcements(course.id, announcements)
            
            if new_announcements:
                logger.info(f"   🆕 {len(new_announcements)} new announcement(s)!")
                
                # Fetch full content for new announcements if requested
                if fetch_full_content:
                    logger.info(f"   📄 Fetching full content for new announcements...")
                    for announcement in new_announcements:
                        try:
                            response = self.session.get(announcement.url, timeout=30)
                            response.raise_for_status()
                            full_content = self.parser.extract_announcement_content(response.text)
                            if full_content and len(full_content) > len(announcement.preview):
                                announcement.preview = full_content
                        except Exception as e:
                            logger.debug(f"   Could not fetch full content for {announcement.title}: {e}")
                
                # Save new announcements to database
                self.db.save_announcements(course.id, new_announcements)
            else:
                logger.info("   ✓ No new announcements")
            
            return new_announcements
            
        except requests.RequestException as e:
            logger.error(f"   ❌ Error checking course: {e}")
            return []
        except Exception as e:
            logger.error(f"   ❌ Unexpected error: {e}")
            return []
    
    def run_check(self) -> Dict[str, any]:
        """
        Run a full check cycle across all courses.
        
        Returns:
            Statistics dictionary
        """
        check_start_time = datetime.now()
        
        logger.info("=" * 70)
        logger.info("🎓 USM eLearning Monitor - Check Starting")
        logger.info("=" * 70)
        logger.info(f"⏰ {check_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get last check time for filtering
        last_check_time = self.db.get_last_check_time()
        if last_check_time:
            time_since_last = (check_start_time - last_check_time).total_seconds() / 60
            logger.info(f"📅 Last check: {last_check_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_since_last:.1f} min ago)")
        else:
            logger.info(f"📅 First check - will record all announcements but only notify for recent ones")
        
        stats = {
            'total_courses': 0,
            'monitored_courses': 0,
            'courses_with_new': 0,
            'total_new_announcements': 0,
            'success': True,
            'errors': [],
            'last_check_time': last_check_time.isoformat() if last_check_time else None
        }
        
        try:
            # Step 1: Authenticate
            if not self.ensure_authenticated():
                error_msg = "Authentication failed"
                stats['success'] = False
                stats['errors'].append(error_msg)
                
                # Send error alert
                if self.config.get_notification_settings().get('send_error_alerts'):
                    self.notifier.send_error_alert(error_msg)
                
                return stats
            
            # Step 2: Fetch courses
            courses = self.fetch_courses(use_cache=True)
            
            if not courses:
                logger.warning("⚠️  No courses found")
                stats['success'] = False
                return stats
            
            stats['total_courses'] = len(courses)
            logger.info(f"✅ Found {len(courses)} course(s)")
            
            # Step 3: Filter courses based on config
            monitored_courses = [
                course for course in courses
                if self.config.should_monitor_course(course.id)
            ]
            
            stats['monitored_courses'] = len(monitored_courses)
            
            if len(monitored_courses) < len(courses):
                logger.info(f"📌 Monitoring {len(monitored_courses)} of {len(courses)} courses (filtered by config)")
            
            # Step 4: Check each course
            logger.info("\n🔍 Checking courses for announcements...\n")
            
            # Calculate time window for notifications
            # On first run, use a 60 minute window to avoid spamming with old announcements
            # On subsequent runs, use time since last check + buffer
            if last_check_time:
                # Add 5 minute buffer to account for processing time
                notification_window_start = last_check_time - timedelta(minutes=5)
            else:
                # First run: only notify for very recent announcements (last hour)
                notification_window_start = check_start_time - timedelta(minutes=60)
            
            logger.info(f"📬 Will notify for announcements first seen after: {notification_window_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Get configuration for full content fetching
            fetch_full_content = self.config.get_notification_settings().get('fetch_full_content', True)
            
            for course in monitored_courses:
                new_announcements = self.check_course_announcements(course, fetch_full_content)
                
                if new_announcements:
                    stats['courses_with_new'] += 1
                    stats['total_new_announcements'] += len(new_announcements)
                    
                    # Filter announcements to only those within notification window
                    recent_announcements = self.db.get_recent_new_announcements(
                        course.id,
                        notification_window_start
                    )
                    
                    if recent_announcements:
                        logger.info(f"   📧 {len(recent_announcements)} announcement(s) within notification window")
                        
                        # Send notification if enabled
                        if self.config.get_notification_settings().get('send_email'):
                            success = self.notifier.send_notification(
                                course.name,
                                recent_announcements
                            )
                            
                            if success:
                                # Mark as notified
                                urls = [ann['url'] for ann in recent_announcements]
                                self.db.mark_as_notified(course.id, urls)
                    else:
                        logger.info(f"   ℹ️  New announcements found but outside notification window (recorded only)")
            
            # Step 5: Print summary
            logger.info("\n" + "=" * 70)
            logger.info("📊 Check Summary")
            logger.info("=" * 70)
            logger.info(f"Total courses: {stats['total_courses']}")
            logger.info(f"Monitored courses: {stats['monitored_courses']}")
            logger.info(f"Courses with new announcements: {stats['courses_with_new']}")
            logger.info(f"Total new announcements: {stats['total_new_announcements']}")
            
            db_stats = self.db.get_stats()
            logger.info(f"\n💾 Database Statistics:")
            logger.info(f"   Tracked courses: {db_stats['total_courses']}")
            logger.info(f"   Total announcements: {db_stats['total_announcements']}")
            logger.info(f"   Unnotified: {db_stats['unnotified_announcements']}")
            
            logger.info("\n✅ Check complete!")
            
            # Update last check time
            self.db.update_last_check_time(check_start_time)
            
            # Cleanup old announcements periodically
            cleanup_days = self.config.load_config().get('database_cleanup_days', 90)
            self.db.cleanup_old_announcements(days=cleanup_days)
            
        except Exception as e:
            logger.error(f"\n❌ Unexpected error during check: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            stats['success'] = False
            stats['errors'].append(str(e))
            
            # Send error alert
            if self.config.get_notification_settings().get('send_error_alerts'):
                self.notifier.send_error_alert(
                    "Monitor check failed",
                    str(e)
                )
        
        return stats
    
    def refresh_courses(self) -> List[Course]:
        """
        Force refresh courses from server, ignoring cache.
        
        Returns:
            List of Course objects
        """
        logger.info("🔄 Refreshing course list...")
        return self.fetch_courses(use_cache=False)


def test_monitor():
    """Test the monitoring functionality."""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get credentials from environment
    usm_email = os.getenv('USM_EMAIL')
    usm_password = os.getenv('USM_PASSWORD')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    # Validate
    if not all([usm_email, usm_password, smtp_user, smtp_pass]):
        print("❌ Missing required environment variables")
        print("   Required: USM_EMAIL, USM_PASSWORD, SMTP_USER, SMTP_PASS")
        return
    
    # Create and run monitor
    monitor = ELearningMonitor(
        usm_email=usm_email,
        usm_password=usm_password,
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        headless=False  # Show browser for testing
    )
    
    monitor.run_check()


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_monitor()

