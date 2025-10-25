"""
Login automation for USM Identity (ADFS) using Playwright.

Handles SSO authentication flow without session persistence for enhanced security.
Every authentication is performed fresh to prevent session hijacking.
"""
import os
import time
import logging
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class USMLoginManager:
    """Manages USM Identity SSO login without session persistence for enhanced security."""
    
    def __init__(
        self, 
        email: str, 
        password: str, 
        headless: bool = True
    ):
        """
        Initialize login manager.
        
        Args:
            email: USM email/username
            password: USM password
            headless: Run browser in headless mode (default: True)
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.cookies = None
        self.playwright = None
        self.browser = None
        self.context = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser resources."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")
    
    def is_logged_in(self, page: Page) -> bool:
        """
        Check if currently logged in by inspecting page content.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if logged in
        """
        try:
            # Navigate to dashboard
            page.goto("https://elearning.usm.my/sidang2526/my/", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Check for login indicators
            content = page.content()
            
            # If redirected to login page, not logged in
            if "login/index.php" in page.url or "adfs/ls" in page.url:
                return False
            
            # Check for user-specific elements
            if any(indicator in content.lower() for indicator in [
                'dashboard', 'logout', 'my courses', 'kursus saya'
            ]):
                logger.info("✅ Login successful - verified access")
                return True
                
        except Exception as e:
            logger.debug(f"Login check failed: {e}")
        
        return False
    
    def perform_sso_login(self) -> bool:
        """
        Perform full SSO login flow through USM Identity (ADFS).
        
        Returns:
            True if login successful
        """
        try:
            logger.info("🔐 Starting SSO login flow...")
            
            # Initialize Playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = self.context.new_page()
            
            # Step 1: Go to eLearning login page
            logger.info("📄 Loading eLearning login page...")
            page.goto("https://elearning.usm.my/sidang2526/login/index.php", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Step 2: Click "Login using USM Identity" button
            # Look for the USM Identity login button
            try:
                # Try multiple possible selectors
                usm_identity_selectors = [
                    'a:has-text("Login using USM Identity")',
                    'a:has-text("USM Identity")',
                    'a[href*="adfs"]',
                    'button:has-text("USM Identity")',
                ]
                
                clicked = False
                for selector in usm_identity_selectors:
                    try:
                        logger.info(f"🔍 Looking for login button: {selector}")
                        if page.locator(selector).count() > 0:
                            logger.info("✅ Found USM Identity button, clicking...")
                            page.click(selector, timeout=5000)
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    logger.error("❌ Could not find USM Identity login button")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error clicking USM Identity button: {e}")
                return False
            
            # Step 3: Wait for ADFS login page to load
            logger.info("⏳ Waiting for ADFS login page...")
            try:
                page.wait_for_url("**/adfs/ls/**", timeout=15000)
            except PlaywrightTimeout:
                logger.warning("ADFS page not detected, continuing...")
            
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Step 4: Fill in credentials
            logger.info("📝 Entering credentials...")
            
            try:
                # Common ADFS form field selectors
                username_selectors = [
                    'input[name="UserName"]',
                    'input[type="email"]',
                    'input[id*="username" i]',
                    'input[name="username"]'
                ]
                
                password_selectors = [
                    'input[name="Password"]',
                    'input[type="password"]',
                    'input[id*="password" i]'
                ]
                
                # Fill username
                for selector in username_selectors:
                    if page.locator(selector).count() > 0:
                        page.fill(selector, self.email)
                        logger.info("✅ Username entered")
                        break
                
                # Fill password
                for selector in password_selectors:
                    if page.locator(selector).count() > 0:
                        page.fill(selector, self.password)
                        logger.info("✅ Password entered")
                        break
                
            except Exception as e:
                logger.error(f"❌ Error filling credentials: {e}")
                return False
            
            # Step 5: Submit login form
            logger.info("🚀 Submitting login form...")
            
            try:
                # Wait a moment for form to be ready
                time.sleep(1)
                
                # Common submit button selectors
                submit_selectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'input[value*="Sign in" i]',
                    'button:has-text("Sign in")',
                    'input[id*="submit" i]',
                    'button:has-text("submit")',
                    '#submitButton'
                ]
                
                submitted = False
                for selector in submit_selectors:
                    try:
                        logger.info(f"🔍 Looking for submit button: {selector}")
                        if page.locator(selector).count() > 0:
                            # Wait for button to be visible and enabled
                            page.locator(selector).first.wait_for(state="visible", timeout=5000)
                            
                            # Click the button
                            page.locator(selector).first.click(timeout=5000)
                            logger.info(f"✅ Clicked submit button: {selector}")
                            submitted = True
                            
                            # Wait a moment for form submission to process
                            time.sleep(2)
                            break
                    except Exception as e:
                        logger.debug(f"Could not click {selector}: {e}")
                        continue
                
                if not submitted:
                    logger.error("❌ Could not find or click submit button")
                    # Take a screenshot for debugging if not headless
                    if not self.headless:
                        page.screenshot(path="login_debug.png")
                        logger.info("📸 Saved screenshot to login_debug.png")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error submitting form: {e}")
                return False
            
            # Step 6: Wait for redirect back to eLearning
            logger.info("⏳ Waiting for authentication to complete...")
            
            try:
                # Wait for redirect back to elearning.usm.my
                page.wait_for_url("**/elearning.usm.my/**", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                
            except PlaywrightTimeout:
                logger.warning("Redirect took longer than expected, checking login status...")
            
            # Step 7: Verify login success
            time.sleep(2)  # Brief pause for any final redirects
            
            if self.is_logged_in(page):
                logger.info("✅ Login successful!")
                
                # Store cookies in memory (not persisted to disk for security)
                cookies = self.context.cookies()
                self.cookies = cookies
                
                return True
            else:
                logger.error("❌ Login failed - could not verify authentication")
                
                # Check for error messages
                content = page.content().lower()
                if any(err in content for err in ['invalid', 'incorrect', 'failed', 'error']):
                    logger.error("❌ Invalid credentials detected")
                
                return False
                
        except Exception as e:
            logger.error(f"❌ SSO login error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
        
        finally:
            # Keep browser open briefly for debugging if not headless
            if not self.headless:
                time.sleep(2)
    
    def get_authenticated_session(self, force_reauth: bool = False) -> Optional[Dict[str, str]]:
        """
        Get authenticated session cookies by performing fresh login.
        
        Note: Session persistence has been disabled for security.
        Every call performs a fresh authentication.
        
        Args:
            force_reauth: Ignored (kept for API compatibility)
            
        Returns:
            Dictionary of cookies for requests session, or None if auth failed
        """
        logger.info("🔐 Performing fresh authentication (no session persistence)")
        
        # Always perform fresh login (no session caching)
        if self.perform_sso_login():
            # Convert cookies to dict for requests
            cookie_dict = {cookie['name']: cookie['value'] for cookie in self.cookies}
            self.cleanup()
            return cookie_dict
        
        self.cleanup()
        return None


def test_login():
    """Test the login functionality."""
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv('USM_EMAIL')
    password = os.getenv('USM_PASSWORD')
    
    if not email or not password:
        print("❌ Please set USM_EMAIL and USM_PASSWORD in .env")
        return
    
    print("Testing USM Identity SSO Login...")
    print("=" * 60)
    
    with USMLoginManager(email, password, headless=False) as login_mgr:
        cookies = login_mgr.get_authenticated_session()
        
        if cookies:
            print("\n✅ Login test successful!")
            print(f"📊 Retrieved {len(cookies)} session cookies")
        else:
            print("\n❌ Login test failed")


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    test_login()

