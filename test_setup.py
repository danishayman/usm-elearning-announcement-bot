"""
Test script to verify installation and configuration.

Run this after setup to ensure everything is working correctly.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_imports():
    """Test if all required modules can be imported."""
    print_section("Testing Module Imports")
    
    modules = [
        'requests',
        'bs4',
        'dotenv',
        'playwright',
        'schedule'
    ]
    
    failed = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - NOT INSTALLED")
            failed.append(module)
    
    if failed:
        print(f"\n⚠️  Missing modules: {', '.join(failed)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def test_environment_variables():
    """Test if required environment variables are set."""
    print_section("Testing Environment Variables")
    
    load_dotenv()
    
    required_vars = [
        'USM_EMAIL',
        'USM_PASSWORD',
        'SMTP_USER',
        'SMTP_PASS',
        'SMTP_SERVER',
        'SMTP_PORT'
    ]
    
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var or 'PASS' in var:
                display_value = '*' * 8
            elif '@' in value:
                display_value = value.split('@')[0][:3] + '***@' + value.split('@')[1]
            else:
                display_value = value[:3] + '***'
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️  Missing variables: {', '.join(missing)}")
        print("   Please set them in .env file")
        return False
    
    return True


def test_file_structure():
    """Test if required files and directories exist."""
    print_section("Testing File Structure")
    
    required_items = {
        'files': [
            'main.py',
            'login.py',
            'monitor.py',
            'config.json',
            'requirements.txt'
        ],
        'directories': [
            'utils',
            'data',
            'logs'
        ]
    }
    
    all_ok = True
    
    for file in required_items['files']:
        if os.path.isfile(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NOT FOUND")
            all_ok = False
    
    for directory in required_items['directories']:
        if os.path.isdir(directory):
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ - NOT FOUND")
            all_ok = False
    
    return all_ok


def test_playwright():
    """Test if Playwright is properly installed."""
    print_section("Testing Playwright")
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("✅ Playwright module imported")
        
        # Try to launch browser
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto('about:blank')
                browser.close()
            
            print("✅ Chromium browser installed and working")
            return True
            
        except Exception as e:
            print(f"❌ Browser launch failed: {e}")
            print("   Run: playwright install chromium")
            return False
            
    except ImportError:
        print("❌ Playwright not installed")
        print("   Run: pip install playwright")
        return False


def test_smtp_connection():
    """Test SMTP connection."""
    print_section("Testing SMTP Connection")
    
    load_dotenv()
    
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    
    if not all([smtp_server, smtp_user, smtp_pass]):
        print("❌ SMTP credentials not configured")
        return False
    
    try:
        import smtplib
        
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
        
        print("✅ Connected to SMTP server")
        
        try:
            server.login(smtp_user, smtp_pass)
            print("✅ SMTP authentication successful")
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP authentication failed")
            print("   For Gmail, use App Password: https://myaccount.google.com/apppasswords")
            return False
            
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False


def run_quick_login_test():
    """Run a quick login test."""
    print_section("Testing USM Identity Login")
    
    load_dotenv()
    
    usm_email = os.getenv('USM_EMAIL')
    usm_password = os.getenv('USM_PASSWORD')
    
    if not usm_email or not usm_password:
        print("❌ USM credentials not configured")
        return False
    
    print("⚠️  This will attempt to login to USM Identity...")
    print("   (Browser will run in headless mode)")
    
    try:
        from login import USMLoginManager
        
        with USMLoginManager(usm_email, usm_password, headless=True) as login_mgr:
            cookies = login_mgr.get_authenticated_session()
            
            if cookies:
                print(f"✅ Login successful! ({len(cookies)} cookies retrieved)")
                return True
            else:
                print("❌ Login failed")
                print("   Try running with: HEADLESS=false python login.py")
                return False
                
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  🧪 USM eLearning Monitor - Setup Test")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results['imports'] = test_imports()
    results['environment'] = test_environment_variables()
    results['file_structure'] = test_file_structure()
    results['playwright'] = test_playwright()
    
    # Optional tests
    if results['environment']:
        results['smtp'] = test_smtp_connection()
    
    if results['imports'] and results['environment'] and results['playwright']:
        print("\n⚠️  About to test USM login (requires valid credentials)")
        response = input("Continue? (y/n): ").lower()
        if response == 'y':
            results['login'] = run_quick_login_test()
    
    # Summary
    print_section("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to run the monitor.")
        print("\nNext step:")
        print("  python main.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

