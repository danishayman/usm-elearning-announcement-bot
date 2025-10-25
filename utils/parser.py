"""
Parser utilities for extracting course and announcement data from eLearning pages.

Provides robust HTML parsing with multiple fallback strategies.
"""
import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs

logger = logging.getLogger(__name__)


class Course:
    """Represents an enrolled course."""
    
    def __init__(self, course_id: str, name: str, url: str):
        """
        Initialize a course.
        
        Args:
            course_id: Unique course identifier
            name: Course name/title
            url: Full URL to course page
        """
        self.id = course_id
        self.name = name
        self.url = url
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Course':
        """Create Course from dictionary."""
        return cls(data['id'], data['name'], data['url'])
    
    def __repr__(self):
        return f"Course(id={self.id}, name={self.name})"
    
    def __eq__(self, other):
        if isinstance(other, Course):
            return self.id == other.id
        return False
    
    def __hash__(self):
        return hash(self.id)


class Announcement:
    """Represents an announcement/forum post."""
    
    def __init__(
        self,
        title: str,
        url: str,
        preview: str = "",
        author: str = "",
        date: str = ""
    ):
        """
        Initialize an announcement.
        
        Args:
            title: Announcement title
            url: Direct link to announcement
            preview: Short preview/excerpt of content
            author: Author name
            date: Date posted
        """
        self.title = title
        self.url = url
        self.preview = preview
        self.author = author
        self.date = date
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON/database storage."""
        return {
            'title': self.title,
            'url': self.url,
            'preview': self.preview,
            'author': self.author,
            'date': self.date
        }
    
    def __repr__(self):
        return f"Announcement(title={self.title[:50]}...)"


class MoodleParser:
    """Parses Moodle pages to extract courses and announcements."""
    
    def __init__(self, base_url: str = "https://elearning.usm.my/sidang2526"):
        """
        Initialize parser.
        
        Args:
            base_url: Base URL of the Moodle instance
        """
        self.base_url = base_url.rstrip('/')
    
    def extract_courses(self, html: str) -> List[Course]:
        """
        Extract all enrolled courses from dashboard HTML.
        
        Args:
            html: HTML content of dashboard/my page
            
        Returns:
            List of Course objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        courses = []
        seen_ids = set()
        
        logger.info("🔍 Parsing courses from dashboard...")
        
        # Strategy 1: Find course view links
        course_links = soup.find_all('a', href=re.compile(r'/course/view\.php\?id=\d+'))
        
        for link in course_links:
            course = self._extract_course_from_link(link)
            if course and course.id not in seen_ids:
                courses.append(course)
                seen_ids.add(course.id)
        
        # Strategy 2: Look for course cards/blocks
        course_cards = soup.find_all('div', class_=re.compile(
            r'coursebox|course-info-container|card-body|course-content'
        ))
        
        for card in course_cards:
            link = card.find('a', href=re.compile(r'/course/view\.php\?id=\d+'))
            if link:
                course = self._extract_course_from_link(link)
                if course and course.id not in seen_ids:
                    courses.append(course)
                    seen_ids.add(course.id)
        
        # Strategy 3: Look in navigation or course list
        nav_items = soup.find_all('li', class_=re.compile(r'type_course'))
        for item in nav_items:
            link = item.find('a', href=re.compile(r'/course/view\.php\?id=\d+'))
            if link:
                course = self._extract_course_from_link(link)
                if course and course.id not in seen_ids:
                    courses.append(course)
                    seen_ids.add(course.id)
        
        logger.info(f"✅ Found {len(courses)} course(s)")
        return courses
    
    def _extract_course_from_link(self, link) -> Optional[Course]:
        """
        Extract course information from an anchor tag.
        
        Args:
            link: BeautifulSoup tag object for an anchor
            
        Returns:
            Course object or None
        """
        try:
            href = link.get('href', '')
            
            # Extract course ID from URL
            match = re.search(r'id=(\d+)', href)
            if not match:
                return None
            
            course_id = match.group(1)
            
            # Get course name
            course_name = link.get_text(strip=True)
            if not course_name:
                course_name = link.get('title', f"Course {course_id}")
            
            # Build full URL
            course_url = urljoin(self.base_url, href)
            
            return Course(course_id, course_name, course_url)
            
        except Exception as e:
            logger.debug(f"Error extracting course from link: {e}")
            return None
    
    def find_announcement_forum(self, html: str) -> Optional[str]:
        """
        Find the announcement forum URL in a course page.
        
        Args:
            html: HTML content of course page
            
        Returns:
            Forum URL or None if not found
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Keywords that indicate announcement forums
        announcement_keywords = [
            'announcement', 'announcements', 'news', 'news forum',
            'pengumuman', 'berita', 'pemberitahuan'
        ]
        
        # Find all forum links
        forum_links = soup.find_all('a', href=re.compile(r'/mod/forum/view\.php\?id=\d+'))
        
        # First pass: Look for explicit announcement forums
        for link in forum_links:
            link_text = link.get_text(strip=True).lower()
            
            if any(keyword in link_text for keyword in announcement_keywords):
                url = urljoin(self.base_url, link.get('href'))
                logger.debug(f"Found announcement forum: {link_text}")
                return url
        
        # Second pass: Check parent containers for keywords
        for link in forum_links:
            parent = link.find_parent('div') or link.find_parent('li')
            if parent:
                parent_text = parent.get_text(strip=True).lower()
                if any(keyword in parent_text for keyword in announcement_keywords):
                    url = urljoin(self.base_url, link.get('href'))
                    logger.debug(f"Found announcement forum via parent: {parent_text[:50]}")
                    return url
        
        # Fallback: Return first forum if any exists
        if forum_links:
            url = urljoin(self.base_url, forum_links[0].get('href'))
            logger.debug("Using first available forum as fallback")
            return url
        
        return None
    
    def extract_announcements(self, html: str) -> List[Announcement]:
        """
        Extract announcements from a forum page.
        
        Args:
            html: HTML content of forum/announcements page
            
        Returns:
            List of Announcement objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        announcements = []
        
        # Strategy 1: Look for discussion names (most common in Moodle)
        discussions = soup.find_all('a', class_=re.compile(r'discussionname'))
        
        for link in discussions:
            announcement = self._extract_announcement_from_discussion(link, soup)
            if announcement:
                announcements.append(announcement)
        
        # Strategy 2: Look for discussion table rows
        if not announcements:
            discussion_rows = soup.find_all('tr', class_=re.compile(r'discussion'))
            
            for row in discussion_rows:
                link = row.find('a', href=re.compile(r'/mod/forum/discuss\.php'))
                if link:
                    announcement = self._extract_announcement_from_discussion(link, row)
                    if announcement:
                        announcements.append(announcement)
        
        # Strategy 3: Any forum discussion links
        if not announcements:
            discussion_links = soup.find_all('a', href=re.compile(r'/mod/forum/discuss\.php\?d=\d+'))
            
            for link in discussion_links:
                title = link.get_text(strip=True)
                if title:
                    url = urljoin(self.base_url, link.get('href', ''))
                    announcements.append(Announcement(title, url))
        
        logger.debug(f"Extracted {len(announcements)} announcement(s)")
        return announcements
    
    def _extract_announcement_from_discussion(
        self,
        link,
        context
    ) -> Optional[Announcement]:
        """
        Extract announcement details from a discussion link and its context.
        
        Args:
            link: BeautifulSoup tag for the discussion link
            context: Parent context (could be soup, row, or container)
            
        Returns:
            Announcement object or None
        """
        try:
            title = link.get_text(strip=True)
            url = urljoin(self.base_url, link.get('href', ''))
            
            # Try to find parent row/container
            parent = link.find_parent('tr') or link.find_parent('div', class_=re.compile(r'discussion|forum'))
            if not parent:
                parent = context
            
            # Extract metadata
            author = ""
            date = ""
            preview = ""
            
            # Look for author
            author_link = parent.find('a', href=re.compile(r'/user/view\.php'))
            if author_link:
                author = author_link.get_text(strip=True)
            
            # Look for date/time
            time_elem = parent.find('time')
            if time_elem:
                date = time_elem.get_text(strip=True)
            else:
                # Try other date indicators
                date_elem = parent.find('span', class_=re.compile(r'date|time|posted'))
                if date_elem:
                    date = date_elem.get_text(strip=True)
            
            # Try to extract preview/excerpt
            preview_elem = parent.find('div', class_=re.compile(r'content|excerpt|summary|shortpost'))
            if preview_elem:
                preview = preview_elem.get_text(strip=True)[:300]
            
            return Announcement(title, url, preview, author, date)
            
        except Exception as e:
            logger.debug(f"Error extracting announcement: {e}")
            return None
    
    def extract_announcement_content(self, html: str) -> str:
        """
        Extract the main content/body of an announcement from its discussion page.
        
        Args:
            html: HTML content of announcement discussion page
            
        Returns:
            Announcement content text
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Strategy 1: Look for the first post/forum post content
        content_containers = soup.find_all(['div', 'article'], class_=re.compile(
            r'post|forumpost|posting|discussion|firstpost'
        ))
        
        for container in content_containers:
            # Try to find the actual content text with multiple selectors
            text_elem = container.find('div', class_=re.compile(
                r'post-content-container|post_content|content-text|message|posting-content|post-body|no-overflow'
            ))
            
            if not text_elem:
                # Fallback: look for generic content divs
                text_elem = container.find('div', class_=re.compile(r'content'))
            
            if text_elem:
                # Remove unwanted nested elements
                for unwanted in text_elem.find_all(['div', 'span'], class_=re.compile(
                    r'reply|responses|attachments|commands|rating|footer|controls|author'
                )):
                    unwanted.decompose()
                
                # Remove any script or style tags
                for script in text_elem.find_all(['script', 'style']):
                    script.decompose()
                
                # Get text with better formatting
                text = text_elem.get_text(separator='\n', strip=True)
                
                # Clean up excessive whitespace
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = '\n'.join(lines)
                
                if len(text) > 30:  # Ensure it's substantial content
                    return text[:2000]  # Increased limit for full content
        
        # Strategy 2: Look for any div with role="main" or similar
        main_content = soup.find('div', {'role': 'main'})
        if main_content:
            # Remove navigation and footer elements
            for nav in main_content.find_all(['nav', 'footer', 'header']):
                nav.decompose()
            
            text = main_content.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            if len(text) > 30:
                return text[:2000]
        
        # Strategy 3: Fallback to finding any substantial text block
        all_paragraphs = soup.find_all('p')
        if all_paragraphs:
            text_parts = []
            for p in all_paragraphs[:10]:  # Limit to first 10 paragraphs
                p_text = p.get_text(strip=True)
                if len(p_text) > 20:
                    text_parts.append(p_text)
            
            if text_parts:
                text = '\n\n'.join(text_parts)
                return text[:2000]
        
        return ""

