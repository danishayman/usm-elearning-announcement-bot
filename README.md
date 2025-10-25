# 🎓 USM eLearning Announcement Monitor

Automated monitoring system for Universiti Sains Malaysia's eLearning portal. Get instant email notifications when new course announcements are posted.



## 📋 Table of Contents

- [Getting Started](#-getting-started)
- [Configuration](#️-configuration-optional)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Getting Started

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

## ⚙️ Configuration (Optional)

You can customize monitoring behavior by editing `config.json` in your repository:

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
1. After the first workflow run, download the `data/courses.json` artifact from the Actions tab
2. Find the course IDs you want to exclude
3. Add them to `excluded_course_ids` in `config.json`
4. Commit and push the changes to your repository

---

## 🐛 Troubleshooting

### Login Issues
- Verify credentials are correct in GitHub Secrets
- Check workflow logs in Actions tab to see login errors
- Ensure your USM credentials are up to date

### Email Not Sending
- For Gmail, use App Password (not regular password)
- Check spam/junk folder
- Verify SMTP credentials in GitHub Secrets
- Ensure 2-Step Verification is enabled on your Gmail account

### GitHub Actions Issues
- Check that all 4 secrets are set correctly
- View workflow logs in Actions tab for error details
- Ensure workflow file syntax is correct
- Verify the workflow is enabled in the Actions tab

### No Courses Found
- Ensure you're enrolled in courses on eLearning
- Check if your USM credentials are correct
- Review workflow logs for any course fetching errors

---

## 🔒 Security

- **Use GitHub Secrets** for all credentials - never hardcode them
- **Use App Passwords** for Gmail, not your main password
- **Enable 2-Step Verification** on your Gmail account
- **Review workflow logs** regularly to ensure no sensitive data is exposed

---

## 📧 Support

Having issues? 

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review workflow logs in the Actions tab
3. [Open an issue](../../issues) on GitHub

---

<div align="center">

**Made with ❤️ for USM Students**

⭐ **Star this repo if it helps you!** ⭐

[Report Bug](../../issues) · [Request Feature](../../issues)

</div>
