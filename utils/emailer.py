"""
Email notification system for sending announcement alerts.

Supports both Gmail SMTP and configurable SMTP servers with HTML formatting.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Handles email notifications for new announcements."""
    
    def __init__(
        self,
        smtp_user: str,
        smtp_pass: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        recipient: str = None
    ):
        """
        Initialize email notifier.
        
        Args:
            smtp_user: SMTP username/email address
            smtp_pass: SMTP password or app-specific password
            smtp_server: SMTP server address (default: Gmail)
            smtp_port: SMTP port (587 for TLS, 465 for SSL)
            recipient: Default recipient email (can be overridden per message)
        """
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.recipient = recipient or smtp_user
        
    def send_notification(
        self,
        course_name: str,
        announcements: List[Dict[str, str]],
        recipient: str = None
    ) -> bool:
        """
        Send email notification for new announcements.
        
        Args:
            course_name: Name of the course
            announcements: List of announcement dictionaries with:
                - title: Announcement title
                - url: Direct link to announcement
                - preview: Short preview text (optional)
                - author: Author name (optional)
                - date: Date posted (optional)
            recipient: Override default recipient
        
        Returns:
            True if email sent successfully
        """
        to_email = recipient or self.recipient
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎓 New: {announcements[0]['title'][:50]}" if len(announcements) == 1 else f"🎓 {len(announcements)} New Announcements - {course_name}"
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            
            # Create email body
            text_body = self._create_text_body(course_name, announcements)
            html_body = self._create_html_body(course_name, announcements)
            
            # Attach both versions
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            if self.smtp_port == 465:
                # Use SSL
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, to_email, msg.as_string())
            else:
                # Use TLS (port 587)
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            logger.info(f"📧 Email sent: {course_name} ({len(announcements)} announcement(s))")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Email authentication failed")
            logger.error("   Check SMTP credentials. For Gmail, use App Password:")
            logger.error("   https://support.google.com/accounts/answer/185833")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    def _create_text_body(
        self,
        course_name: str,
        announcements: List[Dict[str, str]]
    ) -> str:
        """Create plain text email body."""
        body = f"📢 New Announcement{'s' if len(announcements) > 1 else ''} in {course_name}\n"
        body += "=" * 70 + "\n\n"
        
        for i, announcement in enumerate(announcements, 1):
            body += f"{i}. {announcement['title']}\n"
            body += f"   🔗 {announcement['url']}\n"
            
            if announcement.get('author'):
                body += f"   👤 Author: {announcement['author']}\n"
            
            if announcement.get('date'):
                body += f"   📅 Posted: {announcement['date']}\n"
            
            if announcement.get('preview'):
                body += f"\n   📝 Content:\n"
                # Wrap long text for better readability
                preview = announcement['preview']
                words = preview.split()
                line = "   "
                for word in words:
                    if len(line) + len(word) + 1 > 70:
                        body += line + "\n"
                        line = "   " + word + " "
                    else:
                        line += word + " "
                body += line.strip() + "\n"
            
            body += "\n" + "-" * 70 + "\n\n"
        
        body += f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body += "USM eLearning Monitoring Bot\n"
        
        return body
    
    def _create_html_body(
        self,
        course_name: str,
        announcements: List[Dict[str, str]]
    ) -> str:
        """Create HTML email body with modern styling."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 650px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 35px 25px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 26px;
            font-weight: 600;
        }}
        .header p {{
            margin: 0;
            font-size: 17px;
            opacity: 0.95;
            font-weight: 500;
        }}
        .content {{
            padding: 30px 25px;
        }}
        .announcement {{
            background-color: #f9fafb;
            border-left: 5px solid #667eea;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .announcement-number {{
            display: inline-block;
            background-color: #667eea;
            color: white;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            margin-bottom: 10px;
        }}
        .announcement-title {{
            font-size: 20px;
            font-weight: 600;
            color: #1f2937;
            margin: 8px 0 16px 0;
            line-height: 1.4;
        }}
        .announcement-meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e5e7eb;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
        }}
        .meta-item-icon {{
            font-size: 16px;
        }}
        .announcement-content {{
            background-color: white;
            padding: 18px;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
            margin: 16px 0;
        }}
        .content-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: #667eea;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
        }}
        .content-text {{
            color: #374151;
            font-size: 15px;
            line-height: 1.7;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .announcement-link {{
            display: inline-block;
            color: white;
            background-color: #667eea;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            margin-top: 16px;
            padding: 12px 24px;
            border-radius: 6px;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
        }}
        .announcement-link:hover {{
            background-color: #5568d3;
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
            transform: translateY(-1px);
        }}
        .footer {{
            background-color: #f9fafb;
            text-align: center;
            padding: 24px;
            font-size: 13px;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}
        .footer-time {{
            font-weight: 500;
            color: #4b5563;
            margin-bottom: 8px;
        }}
        .footer-links {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
        }}
        .footer-links a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 12px;
            font-weight: 500;
            transition: color 0.2s;
        }}
        .footer-links a:hover {{
            color: #5568d3;
            text-decoration: underline;
        }}
        @media only screen and (max-width: 600px) {{
            .container {{
                border-radius: 0;
                margin: 0;
            }}
            .content {{
                padding: 20px 15px;
            }}
            .announcement {{
                padding: 18px;
            }}
            .announcement-meta {{
                flex-direction: column;
                gap: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📢 New Announcement{'s' if len(announcements) > 1 else ''}</h1>
            <p>{course_name}</p>
        </div>
        <div class="content">
"""
        
        for i, announcement in enumerate(announcements, 1):
            html += f"""
            <div class="announcement">
                <span class="announcement-number">#{i}</span>
                <div class="announcement-title">{announcement['title']}</div>
"""
            
            # Add metadata if available
            meta_items = []
            if announcement.get('author'):
                meta_items.append(f'''
                    <div class="meta-item">
                        <span class="meta-item-icon">👤</span>
                        <span>{announcement["author"]}</span>
                    </div>''')
            if announcement.get('date'):
                meta_items.append(f'''
                    <div class="meta-item">
                        <span class="meta-item-icon">📅</span>
                        <span>{announcement["date"]}</span>
                    </div>''')
            
            if meta_items:
                html += f"""
                <div class="announcement-meta">
                    {''.join(meta_items)}
                </div>
"""
            
            # Add full content if available
            if announcement.get('preview'):
                # Escape HTML and preserve line breaks
                content = announcement['preview'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html += f"""
                <div class="announcement-content">
                    <div class="content-label">📝 Announcement Content</div>
                    <div class="content-text">{content}</div>
                </div>
"""
            
            html += f"""
                <a href="{announcement['url']}" class="announcement-link">
                    📖 View Full Announcement →
                </a>
            </div>
"""
        
        html += f"""
        </div>
        <div class="footer">
            <p class="footer-time">⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>🤖 USM eLearning Monitoring Bot</p>
            <div class="footer-links">
                <a href="https://elearning.usm.my/sidang2526/my/">📊 Dashboard</a>
                <a href="https://elearning.usm.my/sidang2526/">🎓 eLearning Portal</a>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def send_error_alert(self, error_message: str, details: str = "") -> bool:
        """
        Send an error alert email to notify about system issues.
        
        Args:
            error_message: Brief error description
            details: Additional error details
            
        Returns:
            True if email sent successfully
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"⚠️ USM eLearning Monitor - Error Alert"
            msg['From'] = self.smtp_user
            msg['To'] = self.recipient
            
            text_body = f"""
USM eLearning Monitor - Error Alert
{'=' * 60}

Error: {error_message}

{details if details else 'No additional details available.'}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system logs for more information.
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc2626; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ background-color: #fef2f2; padding: 20px; margin-top: 20px; border-left: 4px solid #dc2626; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">⚠️ Error Alert</h2>
            <p style="margin: 5px 0 0 0;">USM eLearning Monitor</p>
        </div>
        <div class="content">
            <h3>Error Details</h3>
            <p><strong>{error_message}</strong></p>
            {f'<p>{details}</p>' if details else ''}
            <p><small>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </div>
        <div class="footer">
            <p>Please check the system logs for more information.</p>
        </div>
    </div>
</body>
</html>
"""
            
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, self.recipient, msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, self.recipient, msg.as_string())
            
            logger.info("📧 Error alert email sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")
            return False

