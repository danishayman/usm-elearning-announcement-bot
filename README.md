# 🎓 USM eLearning Announcement Monitor

Advanced automated monitoring system for Universiti Sains Malaysia's eLearning portal. Automatically detects new course announcements and sends instant email notifications with smart SSO authentication, course caching, and configurable monitoring rules.

## ✨ Features

### 🔒 **Smart Authentication**
- **USM Identity SSO Support**: Full ADFS authentication automation using Playwright
- **Session Persistence**: Saves and reuses login sessions to minimize re-authentication
- **Auto-Reauthentication**: Detects expired sessions and automatically logs back in
- **Headless Browser Mode**: Runs invisibly in the background or visible for debugging

### 🎯 **Intelligent Course Monitoring**
- **Auto-Discovery**: Automatically finds all enrolled courses
- **Smart Caching**: Stores course list locally to reduce server load
- **Selective Monitoring**: Configure which courses to monitor via `config.json`
- **Course Exclusion**: Exclude specific courses you don't want to track

### 📬 **Advanced Notifications**
- **Beautiful HTML Emails**: Modern, responsive email design with enhanced styling
- **Full Announcement Content**: Automatically fetches and includes complete announcement text in emails
- **Rich Metadata**: Displays announcement titles, authors, dates, and course information
- **Direct Links**: Click straight through to read announcements on eLearning portal
- **Plain Text Fallback**: Email clients without HTML support get well-formatted plain text
- **Error Alerts**: Get notified if the monitor encounters issues

### 💾 **Robust Data Management**
- **SQLite Database**: Persistent tracking of all announcements
- **Duplicate Prevention**: Never get notified twice for the same announcement
- **Historical Data**: Keep track of all past announcements
- **Auto Cleanup**: Automatically remove old records to manage database size

### ⚙️ **Flexible Operation**
- **Scheduled Mode**: Runs continuously with configurable check intervals
- **Once Mode**: Run a single check (perfect for cron jobs)
- **Configurable Intervals**: Set check frequency from minutes to hours
- **Graceful Shutdown**: Handles interrupts cleanly

### 📊 **Comprehensive Logging**
- **Dual Output**: Logs to both console and file (`logs/app.log`)
- **Detailed Statistics**: Track courses checked, new announcements, and more
- **Error Tracking**: Full error logs with stack traces for debugging

---

## 📋 Requirements

- **Python 3.8+**
- **Valid USM eLearning account**
- **Email account** (Gmail recommended) for sending notifications
- **2-5 MB disk space** for dependencies and data

---

## 🚀 Quick Start

### 1️⃣ Clone & Install

```bash
# Clone the repository
git clone https://github.com/yourusername/usm-elearning-monitor.git
cd usm-elearning-monitor

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2️⃣ Configure Environment

Create a `.env` file in the project root:

```env
# USM eLearning Login Credentials
USM_EMAIL=your_email@student.usm.my
USM_PASSWORD=your_usm_password

# Email Notification Settings (Gmail example)
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Optional: Advanced Settings
MOODLE_BASE_URL=https://elearning.usm.my/sidang2526
RUN_MODE=scheduled
HEADLESS=true
```

#### 📧 **Gmail Setup (App Password)**

Gmail requires an App Password for security:

1. Enable [2-Factor Authentication](https://myaccount.google.com/security)
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the 16-character password as `SMTP_PASS`

#### 📮 **Other Email Providers**

<details>
<summary><b>Outlook/Hotmail</b></summary>

```env
SMTP_USER=your_email@outlook.com
SMTP_PASS=your_password
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```
</details>

<details>
<summary><b>Yahoo Mail</b></summary>

```env
SMTP_USER=your_email@yahoo.com
SMTP_PASS=your_app_password
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```
</details>

<details>
<summary><b>Custom SMTP Server</b></summary>

```env
SMTP_USER=your_email@domain.com
SMTP_PASS=your_password
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
```
</details>

### 3️⃣ Configure Monitoring

Edit `config.json` to customize monitoring behavior:

```json
{
  "monitor_all_courses": true,
  "monitored_course_ids": [],
  "excluded_course_ids": ["12345", "67890"],
  "check_interval_minutes": 30,
  "notification_settings": {
    "send_email": true,
    "send_error_alerts": true
  },
  "database_cleanup_days": 90
}
```

**Configuration Options:**

- `monitor_all_courses`: `true` = monitor all courses, `false` = only monitor listed courses
- `monitored_course_ids`: Array of course IDs to monitor (when `monitor_all_courses` is `false`)
- `excluded_course_ids`: Array of course IDs to exclude from monitoring
- `check_interval_minutes`: How often to check (in minutes)
- `notification_settings`:
  - `send_email`: Enable/disable email notifications
  - `send_error_alerts`: Get notified about system errors
  - `fetch_full_content`: Fetch full announcement content for emails (default: true)
- `database_cleanup_days`: Remove announcements older than X days

### 4️⃣ Run the Monitor

```bash
# Run in scheduled mode (continuous monitoring)
python main.py

# Run once and exit (useful for cron jobs)
RUN_MODE=once python main.py

# Run with visible browser (for debugging)
HEADLESS=false python main.py
```

---

## 📁 Project Structure

```
usm-elearning-monitor/
├── main.py                    # Main entry point with scheduling
├── login.py                   # USM Identity SSO authentication
├── monitor.py                 # Core monitoring logic
├── utils/
│   ├── __init__.py
│   ├── emailer.py            # Email notification system
│   ├── parser.py             # HTML parsing for courses/announcements
│   └── storage.py            # Database & cache management
├── data/
│   ├── announcements.db      # SQLite database (auto-created)
│   ├── courses.json          # Course cache (auto-created)
│   └── session.json          # Login session (auto-created)
├── logs/
│   └── app.log               # Application logs (auto-created)
├── config.json               # Monitoring configuration
├── .env                      # Environment variables (you create this)
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🐳 Deployment

### **Render.com** (Recommended)

Render.com offers free hosting with persistent storage.

#### Setup Steps:

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render.com](https://render.com)
   - Connect your GitHub repository
   - Select **Web Service**
   - Choose the forked repository

3. **Configure the service:**
   ```yaml
   Name: usm-elearning-monitor
   Environment: Python 3
   Build Command: pip install -r requirements.txt && playwright install chromium --with-deps
   Start Command: python main.py
   ```

4. **Add Environment Variables** in Render dashboard:
   - `USM_EMAIL`
   - `USM_PASSWORD`
   - `SMTP_USER`
   - `SMTP_PASS`
   - `SMTP_SERVER`
   - `SMTP_PORT`
   - `RUN_MODE=scheduled`
   - `HEADLESS=true`

5. **Add Persistent Disk** (to save data between restarts):
   - Mount Path: `/opt/render/project/src/data`
   - Size: 1GB (free tier)

6. **Deploy!** 🚀

#### Important Notes:
- Free tier sleeps after 15 minutes of inactivity
- Use **Background Worker** instead of Web Service for 24/7 operation
- Logs are available in the Render dashboard

---

### **Railway.app**

Railway offers excellent developer experience with automatic deployments.

#### Setup Steps:

1. **Fork this repository**

2. **Create new project** on [Railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository

3. **Add environment variables:**
   ```
   USM_EMAIL=your_email
   USM_PASSWORD=your_password
   SMTP_USER=your_smtp_email
   SMTP_PASS=your_smtp_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   RUN_MODE=scheduled
   HEADLESS=true
   ```

4. **Configure start command** (in Railway settings):
   ```bash
   playwright install chromium --with-deps && python main.py
   ```

5. **Add volume** for persistent storage:
   - Mount path: `/app/data`

6. **Deploy!** 🎉

---

### **Docker Deployment**

<details>
<summary><b>Docker Setup</b></summary>

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application files
COPY . .

# Create data and logs directories
RUN mkdir -p data logs

# Run the application
CMD ["python", "main.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  monitor:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

Run with Docker:

```bash
docker-compose up -d
```
</details>

---

### **Linux Server (systemd)**

<details>
<summary><b>Systemd Service Setup</b></summary>

Create `/etc/systemd/system/usm-elearning-monitor.service`:

```ini
[Unit]
Description=USM eLearning Announcement Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/usm-elearning-monitor
Environment="PATH=/path/to/venv/bin:/usr/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable usm-elearning-monitor
sudo systemctl start usm-elearning-monitor
sudo systemctl status usm-elearning-monitor
```

View logs:

```bash
sudo journalctl -u usm-elearning-monitor -f
```
</details>

---

## 🛠️ Advanced Usage

### Finding Course IDs

To configure selective monitoring, you need course IDs:

1. Run the monitor once to fetch all courses
2. Check `data/courses.json` - it will list all courses with IDs
3. Add desired course IDs to `config.json`

Example `data/courses.json`:
```json
{
  "last_updated": "2025-01-15T10:30:00",
  "courses": [
    {
      "id": "12345",
      "name": "Introduction to Computer Science",
      "url": "https://elearning.usm.my/..."
    }
  ]
}
```

### Running as Cron Job

Instead of continuous monitoring, you can run periodic checks:

```bash
# Edit crontab
crontab -e

# Add: Check every 30 minutes
*/30 * * * * cd /path/to/usm-elearning-monitor && RUN_MODE=once /path/to/python main.py >> logs/cron.log 2>&1
```

### Testing Individual Components

```bash
# Test SSO login only
python login.py

# Test monitoring (single check)
python monitor.py

# Run in debug mode (visible browser)
HEADLESS=false python main.py
```

---

## 🐛 Troubleshooting

### Login Issues

**Problem:** Authentication fails

**Solutions:**
- ✅ Verify credentials in `.env`
- ✅ Try logging in manually via browser to ensure account works
- ✅ Run with `HEADLESS=false` to watch the login process
- ✅ Check if USM Identity page structure changed
- ✅ Ensure Playwright browsers are installed: `playwright install chromium`

### Email Not Sending

**Problem:** No email notifications received

**Solutions:**
- ✅ Verify SMTP credentials are correct
- ✅ For Gmail, ensure you're using App Password, not regular password
- ✅ Check spam/junk folder
- ✅ Test SMTP settings with a simple Python script
- ✅ Check firewall isn't blocking SMTP ports (587/465)

### No Courses Found

**Problem:** "No courses found" message

**Solutions:**
- ✅ Ensure you're actually enrolled in courses
- ✅ Check if semester dates are active
- ✅ Verify `MOODLE_BASE_URL` is correct for current semester
- ✅ Try refreshing courses: delete `data/courses.json` and run again

### Browser/Playwright Errors

**Problem:** Playwright fails to launch browser

**Solutions:**
- ✅ Install system dependencies: `playwright install-deps chromium`
- ✅ On Linux servers, ensure Xvfb or similar is available
- ✅ Check if running as correct user with proper permissions
- ✅ Try reinstalling: `playwright install --force chromium`

### High Memory Usage

**Problem:** Process uses too much memory

**Solutions:**
- ✅ Increase `check_interval_minutes` to reduce frequency
- ✅ Enable database cleanup (reduce `database_cleanup_days`)
- ✅ Run in `RUN_MODE=once` with cron instead of scheduled mode
- ✅ Restart service periodically using systemd or supervisor

### Database Locked Errors

**Problem:** SQLite database locked

**Solutions:**
- ✅ Ensure only one instance is running
- ✅ Check file permissions on `data/` directory
- ✅ Delete `data/announcements.db` and let it recreate

---

## 📊 Monitoring & Logs

### Log Files

Logs are stored in `logs/app.log` with rotation:

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# Check last check summary
grep "Check Summary" logs/app.log | tail -1
```

### Database Inspection

```bash
# Open database
sqlite3 data/announcements.db

# View all courses
SELECT * FROM courses;

# View recent announcements
SELECT * FROM announcements ORDER BY first_seen DESC LIMIT 10;

# Count unnotified announcements
SELECT COUNT(*) FROM announcements WHERE notified = 0;
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** - it contains sensitive credentials
2. **Use App Passwords** for email instead of main account password
3. **Keep dependencies updated**: `pip install -U -r requirements.txt`
4. **Limit file permissions**: `chmod 600 .env`
5. **Use environment variables** in production, not `.env` files
6. **Enable 2FA** on your USM and email accounts
7. **Monitor logs** for suspicious activity

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature-name`
7. Open a Pull Request

---

## 📝 Changelog

### Version 2.0.0 (2025-01-15)
- ✨ Added USM Identity SSO authentication with Playwright
- ✨ Implemented session persistence and auto-reauthentication
- ✨ Added SQLite database for robust announcement tracking
- ✨ Course caching to reduce server load
- ✨ Configurable selective monitoring via config.json
- ✨ Enhanced email notifications with modern HTML design
- ✨ Comprehensive logging system
- ✨ Scheduled mode with automatic retry
- ✨ Deployment guides for Render, Railway, and Docker

### Version 1.0.0
- Initial release with basic monitoring

---

## ⚠️ Disclaimer

This tool is for **personal educational use only**. Use responsibly and in accordance with:
- Universiti Sains Malaysia's IT policies
- Your email provider's terms of service
- Applicable laws and regulations

The authors are **not responsible** for:
- Misuse or violations of university policies
- Account suspension or termination
- Any damages resulting from use of this software

**Use at your own risk.**

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for **Universiti Sains Malaysia** students
- Powered by **Python**, **Playwright**, and **BeautifulSoup**
- Inspired by the need for timely course communication
- Special thanks to the open-source community

---

## 📧 Support

### Get Help:

1. **Check [Troubleshooting](#-troubleshooting)** section
2. **Review logs** in `logs/app.log`
3. **Search [Issues](../../issues)** on GitHub
4. **Open a [new issue](../../issues/new)** with:
   - Error messages
   - Log excerpts (remove sensitive data!)
   - Environment details (OS, Python version)
   - Steps to reproduce

### Useful Commands:

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Verify Playwright installation
playwright --version

# Test email settings
python -c "import smtplib; print('SMTP available')"

# Check environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('USM_EMAIL:', bool(os.getenv('USM_EMAIL')))"
```

---

<div align="center">

**Made with ❤️ for USM Students**

⭐ **Star this repo if it helps you!** ⭐

[Report Bug](../../issues) · [Request Feature](../../issues) · [Contribute](../../pulls)

</div>
