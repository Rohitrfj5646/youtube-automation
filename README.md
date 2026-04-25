# 🚀 "Saalon Saal Chale" YouTube Automation System

Welcome to your production-ready, multi-channel YouTube automation system. This system runs 24/7 on 100% free infrastructure and manages three financial channels (Stocks, Forex, Crypto).

---

## 🛠️ Step 1: Collect Your Magic Keys (15 Mins)
You need to sign up for these free services and copy the API keys:

1.  **Google Gemini**: [Get API Key](https://aistudio.google.com/app/apikey) (Free - 60 RPM)
2.  **Sarvam AI**: [Get API Key](https://dashboard.sarvam.ai/) (Free - 5 mins/day)
3.  **Pexels**: [Get API Key](https://www.pexels.com/api/new/) (Free - 200 req/hr)
4.  **Telegram**: Message [@BotFather](https://t.me/botfather) to create a bot and get the `TELEGRAM_BOT_TOKEN`.
5.  **YouTube API**:
    - Go to [Google Cloud Console](https://console.cloud.google.com/).
    - Create a Project -> Enable "YouTube Data API v3".
    - Create OAuth 2.0 Credentials (Web Application).
    - Add `https://developers.google.com/oauthplayground` as an Authorized Redirect URI.
    - Go to [OAuth Playground](https://developers.google.com/oauthplayground/).
    - Select YouTube Data API v3 -> Authorize -> Exchange authorization code for tokens.
    - Copy the `refresh_token`, `client_id`, and `client_secret`.

---

## 🚀 Step 2: Deploy to Render (30 Mins)
1.  **Create a GitHub Repo**: Upload all the files generated here to a private GitHub repository.
2.  **Sign up for Render**: [render.com](https://render.com).
3.  **Create a New Web Service**:
    - Select your GitHub repo.
    - **Runtime**: Docker.
    - **Plan**: Free.
4.  **Add Environment Variables**:
    - `GEMINI_API_KEY`: [Your Key]
    - `SARVAM_API_KEY`: [Your Key]
    - `PEXELS_API_KEY`: [Your Key]
    - `TELEGRAM_BOT_TOKEN`: [Your Key]
    - `TELEGRAM_CHAT_ID`: (Run `python telegram_bot.py` locally or on Colab to find yours)
    - `YT_REFRESH_TOKEN`: [Your Key]
    - `YT_CLIENT_ID`: [Your Key]
    - `YT_CLIENT_SECRET`: [Your Key]

### 💾 Step 2.5: Persistent Storage (Required)
Since this app uses a database to track history, you MUST add a **Persistent Disk** on Render:
- **Mount Path**: `/app/data`
- **Size**: 1GB (Minimum)
- **Note**: This requires a paid plan (Starter) on Render. If using the Free plan, history will reset on every restart.

---

## ⏰ Step 3: Set Up the "Wake Up Call" (5 Mins)
Render's free tier sleeps after 15 minutes. We need to keep it awake:
1.  Go to [cron-job.org](https://cron-job.org).
2.  Create a job that pings your Render URL (e.g., `https://your-app.onrender.com/`) every 10 minutes.

---

## 📱 Step 4: Monitor from Phone
- **Approval**: The bot will send you the first 5 videos on Telegram. Check them and if they look good, type `/approve` (logic included in `app.py`).
- **Auto-Mode**: Once you are confident, type `/auto_on` in Telegram. The system will now post daily without asking you.
- **Updates**: Every month, you will get a notification on GitHub Mobile app. Just click "Merge" on the PR to update the system.

---

## 🧠 System Features
- **Self-Healing**: Automatically retries if an API fails.
- **Policy Compliant**: Includes SEBI disclaimers and "Not Financial Advice" warnings.
- **Anti-Spam**: Tracks topics in a database to ensure no repeats for 7 days.
- **Multi-Language**: Scripts are generated in natural "Hinglish" for maximum engagement.

---

### 🆘 Troubleshooting
If something breaks:
1. Check Render Logs.
2. Ensure API keys haven't hit their daily limits.
3. Use the `/health` endpoint on your URL to see if the system is alive.

*Design by Antigravity - Senior Automation Architect*
