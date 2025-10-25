"""
Main entry point for USM eLearning Announcement Monitor.

Runs continuous monitoring with scheduled checks and automatic error recovery.
"""
import os
import sys
import time
import logging
import signal
from datetime import datetime
from dotenv import load_dotenv
import schedule

from monitor import ELearningMonitor
from utils.storage import ConfigManager

# Global flag for graceful shutdown
shutdown_flag = False


def setup_logging():
    """Configure logging to console and file."""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(message)s'
    )
    
    # File handler (detailed)
    file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (simple)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce verbosity of some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_flag
    print("\n\n⚠️  Shutdown signal received. Finishing current task...")
    shutdown_flag = True


def run_single_check(monitor: ELearningMonitor) -> bool:
    """
    Run a single check cycle with error handling.
    
    Args:
        monitor: ELearningMonitor instance
        
    Returns:
        True if check was successful
    """
    try:
        stats = monitor.run_check()
        return stats.get('success', False)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.error(f"❌ Check failed with error: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        return False


def run_scheduled_mode(monitor: ELearningMonitor, interval_minutes: int):
    """
    Run monitor in scheduled mode with continuous checking.
    
    Args:
        monitor: ELearningMonitor instance
        interval_minutes: Check interval in minutes
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("🤖 USM eLearning Monitor - Scheduled Mode")
    logger.info("=" * 70)
    logger.info(f"Check interval: Every {interval_minutes} minute(s)")
    logger.info("Press Ctrl+C to stop\n")
    
    # Schedule the check
    schedule.every(interval_minutes).minutes.do(run_single_check, monitor)
    
    # Run first check immediately
    logger.info("🚀 Running initial check...\n")
    run_single_check(monitor)
    
    # Keep running scheduled checks
    consecutive_failures = 0
    max_failures = 5
    
    while not shutdown_flag:
        try:
            # Run pending scheduled tasks
            schedule.run_pending()
            
            # Sleep for a bit
            time.sleep(10)
            
            # Reset failure counter on successful check
            if schedule.idle_seconds() < 0:
                consecutive_failures = 0
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"❌ Scheduler error: {e}")
            
            if consecutive_failures >= max_failures:
                logger.error(f"❌ Too many consecutive failures ({max_failures}), stopping...")
                break
            
            logger.info(f"⏳ Waiting 1 minute before retry... ({consecutive_failures}/{max_failures})")
            time.sleep(60)
    
    logger.info("\n👋 Monitor stopped")


def run_once_mode(monitor: ELearningMonitor):
    """
    Run monitor once and exit.
    
    Args:
        monitor: ELearningMonitor instance
    """
    success = run_single_check(monitor)
    sys.exit(0 if success else 1)


def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    usm_email = os.getenv('USM_EMAIL')
    usm_password = os.getenv('USM_PASSWORD')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    base_url = os.getenv('MOODLE_BASE_URL', 'https://elearning.usm.my/sidang2526')
    
    # Validate required environment variables
    required_vars = {
        'USM_EMAIL': usm_email,
        'USM_PASSWORD': usm_password,
        'SMTP_USER': smtp_user,
        'SMTP_PASS': smtp_pass,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        logger.error("\nPlease set them in .env file")
        sys.exit(1)
    
    # Determine run mode
    run_mode = os.getenv('RUN_MODE', 'scheduled').lower()
    headless = os.getenv('HEADLESS', 'true').lower() in ('true', '1', 'yes')
    
    # Initialize monitor
    try:
        monitor = ELearningMonitor(
            usm_email=usm_email,
            usm_password=usm_password,
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            base_url=base_url,
            headless=headless
        )
        
        # Get check interval from config
        config_mgr = ConfigManager()
        interval_minutes = config_mgr.get_check_interval()
        
        # Run in appropriate mode
        if run_mode == 'once':
            logger.info("🔄 Running in ONCE mode (single check)\n")
            run_once_mode(monitor)
        else:
            run_scheduled_mode(monitor, interval_minutes)
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
