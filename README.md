# 🎓 USM eLearning Announcement Monitor

Automated monitoring system for Universiti Sains Malaysia's eLearning portal. Get instant email notifications when new course announcements are posted.



## 📋 Table of Contents

- [Getting Started](#-getting-started)
  - [Option 1: Local Setup](#option-1-local-setup-run-on-your-computer)
  - [Option 2: GitHub Actions Setup](#option-2-github-actions-setup-free-automated-cloud-monitoring) (Recommended for 24/7 monitoring)
- [Configuration](#️-configuration-optional)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Getting Started

### Option 1: Local Setup (Run on Your Computer)

Perfect if you want to run the monitor on your personal computer.

#### 1️⃣ Fork & Clone

```bash
# Fork the repository on GitHub first (click "Fork" button)
# Then clone YOUR fork
git clone https://github.com/danishayman/usm-elearning-announcement-bot.git
cd usm-elearning-announcement-bot

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

#### 2️⃣ Configure Credentials

Create a `.env` file in the project root with your credentials (only 4 required!):

```env
USM_EMAIL=your_email@student.usm.my
USM_PASSWORD=your_usm_password
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_gmail_app_password
```

**That's it!** Everything else uses smart defaults.

#### 📧 Gmail Setup (App Password)

Gmail requires an App Password for security. Follow these steps:

**Step 1: Enable 2-Step Verification**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Scroll down to "How you sign in to Google"
3. Click on "2-Step Verification"
4. Follow the prompts to set it up (you'll need your phone)
5. Complete the setup process

**Step 2: Generate App Password**
1. Once 2-Step Verification is enabled, go to [App Passwords](https://myaccount.google.com/apppasswords)
2. You may need to sign in again
3. Under "Select app", choose "Mail"
4. Under "Select device", choose "Other (Custom name)"
5. Type "USM eLearning Bot" or any name you prefer
6. Click "Generate"
7. Copy the 16-character password shown (format: `xxxx xxxx xxxx xxxx`)
8. Use this password as your `SMTP_PASS` value (you can include or remove spaces)

**💡 Important:** This App Password is different from your regular Gmail password and is specifically for third-party apps.

#### 📬 Force Notifications for Self-Sent Mail (Optional)

If you're using the **same Gmail account** for both sending and receiving notifications, Gmail might not notify you by default. Here's how to fix that:

**Create a Gmail Filter:**
1. Go to [Gmail](https://mail.google.com)
2. Click the gear icon ⚙️ → **See all settings**
3. Go to **Filters and Blocked Addresses** tab
4. Click **Create a new filter**
5. In the filter creation form:
   - **From:** `your_email@gmail.com` (your Gmail address)
   - **To:** `your_email@gmail.com` (same Gmail address)
6. Click **Create filter**
7. Check these options:
   - ✅ **Mark as important**
   - ✅ **Never send it to Spam**
   - ✅ **Categorize as: Primary** (optional, but recommended)
8. Click **Create filter**

This ensures Gmail treats your bot's emails as important and sends you mobile/desktop notifications.

**Alternative:** Use a different email address for receiving notifications to avoid this issue entirely.

#### 3️⃣ Run the Monitor

```bash
# Run in scheduled mode (continuous monitoring)
python main.py
```

---

### Option 2: GitHub Actions Setup (Free Automated Cloud Monitoring)

Run the monitor automatically on GitHub's servers for free! Perfect for 24/7 monitoring without keeping your computer on.

#### 1️⃣ Fork the Repository

1. Go to the [original repository](https://github.com/danishayman/usm-elearning-announcement-bot)
2. Click the **Fork** button in the top right
3. This creates your own copy of the project

#### 2️⃣ Set Up Repository Secrets

Secrets keep your credentials secure in GitHub Actions.

1. Go to your forked repository on GitHub
2. Click **Settings** (top menu bar)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** button
5. Add these 4 secrets one by one:

| Secret Name | Value | Example |
|------------|-------|---------|
| `USM_EMAIL` | Your USM email | `student@student.usm.my` |
| `USM_PASSWORD` | Your USM password | `YourPassword123` |
| `SMTP_USER` | Your email for notifications | `yourname@gmail.com` |
| `SMTP_PASS` | Gmail App Password (see setup below) | `abcd efgh ijkl mnop` |

**How to add each secret:**
- Click "New repository secret"
- Enter the **Name** (e.g., `USM_EMAIL`)
- Enter the **Value** (your actual credential)
- Click "Add secret"
- Repeat for all 4 secrets

#### 📧 Getting Your Gmail App Password

Before adding the `SMTP_PASS` secret, you need to generate a Gmail App Password:

**Step 1: Enable 2-Step Verification**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Scroll down to "How you sign in to Google"
3. Click on "2-Step Verification" and complete the setup

**Step 2: Generate App Password**
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (Custom name)"
3. Enter "USM eLearning Bot"
4. Click "Generate"
5. Copy the 16-character password
6. Use this as your `SMTP_PASS` secret value

#### 📬 Force Notifications for Self-Sent Mail (Optional)

If using the same Gmail for both sending and receiving, create a filter to ensure notifications:

1. Go to Gmail → Settings ⚙️ → **Filters and Blocked Addresses**
2. **Create a new filter** with:
   - **From:** your_email@gmail.com
   - **To:** your_email@gmail.com
3. Apply these actions:
   - ✅ Star it
   - ✅ Mark as important
   - ✅ Never send it to Spam
   - ✅ Categorize as: Primary

This ensures you get notified for all announcements!

#### 3️⃣ Enable GitHub Actions

The workflow file is already included in the repository (`.github/workflows/check.yml`).

1. Go to the **Actions** tab in your repository
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You should see the **"USM eLearning Monitor"** workflow listed

#### 4️⃣ Test Your Setup

1. Go to **Actions** tab
2. Click on **"USM eLearning Monitor"** workflow
3. Click **"Run workflow"** button (on the right)
4. Select branch (usually `main`)
5. Click **"Run workflow"**
6. Wait for it to complete (usually 1-2 minutes)
7. Check your email for any new announcements!

#### 📅 Schedule Customization

The default schedule runs every 30 minutes. To change this, edit the `cron` line in the workflow file:

```yaml
# Every 15 minutes
- cron: '*/15 * * * *'

# Every hour
- cron: '0 * * * *'

# Every 2 hours
- cron: '0 */2 * * *'

# Every day at 8 AM UTC
- cron: '0 8 * * *'
```

**Note:** GitHub Actions may delay scheduled runs by 3-10 minutes during peak times.

#### 🔍 Monitoring Your Workflow

- **Check run history:** Go to Actions tab to see all past runs
- **View logs:** Click any run to see detailed logs
- **Email notifications:** GitHub can email you if a workflow fails (Settings → Notifications)

#### ⚠️ Important Notes

- **Free tier limits:** 2,000 minutes/month (plenty for this use case)
- **Data persistence:** The workflow automatically saves and restores the announcements database between runs using GitHub Actions artifacts
- **Manual runs:** Use "Run workflow" button to trigger immediately
- **Disable anytime:** Go to Actions → Select workflow → "..." menu → Disable workflow

---

## 📁 Project Structure

```
usm-elearning-announcement-bot/
├── main.py                    # Main entry point
├── login.py                   # USM SSO authentication
├── monitor.py                 # Core monitoring logic
├── utils/
│   ├── emailer.py            # Email notifications
│   ├── parser.py             # HTML parsing
│   └── storage.py            # Database management
├── data/                     # Auto-created data folder
│   ├── announcements.db      # SQLite database
│   └── courses.json          # Course cache
├── logs/                     # Auto-created logs
│   └── app.log
├── config.json               # Configuration file
├── .env                      # Your credentials (create this)
├── requirements.txt          # Python dependencies
└── README.md
```

---

## ⚙️ Configuration (Optional)

Edit `config.json` to customize monitoring behavior:

```json
{
  "monitor_all_courses": true,
  "excluded_course_ids": [],
  "check_interval_minutes": 30,
  "notification_settings": {
    "send_email": true,
    "send_error_alerts": true,
    "fetch_full_content": true
  }
}
```

**To exclude specific courses:**
1. Run the monitor once to generate `data/courses.json`
2. Find the course IDs you want to exclude
3. Add them to `excluded_course_ids` in `config.json`

---

## 🐛 Troubleshooting

### Login Issues
- Verify credentials are correct
- Run with `HEADLESS=false` to watch browser login
- Ensure Playwright is installed: `playwright install chromium`

### Email Not Sending
- For Gmail, use App Password (not regular password)
- Check spam/junk folder
- Verify SMTP credentials

### GitHub Actions Issues
- Check that all 4 secrets are set correctly
- View workflow logs in Actions tab for error details
- Ensure workflow file syntax is correct

### No Courses Found
- Ensure you're enrolled in courses
- Check if `MOODLE_BASE_URL` is correct for current semester

---

## 🔒 Security

- **Never commit `.env` file** - add it to `.gitignore`
- **Use GitHub Secrets** for credentials in GitHub Actions
- **Use App Passwords** for email, not your main password
- **Keep dependencies updated**: `pip install -U -r requirements.txt`

---

## 📧 Support

Having issues? 

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review logs in `logs/app.log` (local) or Actions logs (GitHub Actions)
3. [Open an issue](../../issues) on GitHub

---

<div align="center">

**Made with ❤️ for USM Students**

⭐ **Star this repo if it helps you!** ⭐

[Report Bug](../../issues) · [Request Feature](../../issues)

</div>
