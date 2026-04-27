import os
import time
import json
import sqlite3
import subprocess
import requests
import yfinance as yf
from datetime import datetime
import google.generativeai as genai
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from dotenv import load_dotenv
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
import telebot
import threading
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

load_dotenv()

# --- CONFIGURATION ---
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")  # Kept for reference but not used
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# --- LOGGING SETUP ---
def log_config():
    print("--- Environment Check ---")
    print(f"PORT: {os.getenv('PORT')}")
    print(f"DB_PATH: {os.getenv('DB_PATH')}")
    print(f"GEMINI_API_KEY: {'Set' if os.getenv('GEMINI_API_KEY') else 'Not Set'}")
    print(f"SARVAM_API_KEY: {'Set' if os.getenv('SARVAM_API_KEY') else 'Not Set'}")
    print(f"TELEGRAM_BOT_TOKEN: {'Set' if os.getenv('TELEGRAM_BOT_TOKEN') else 'Not Set'}")
    print(f"YT_REFRESH_TOKEN: {'Set' if os.getenv('YT_REFRESH_TOKEN') else 'Not Set'}")
    print("-------------------------")

log_config()

genai.configure(api_key=GENAI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# --- DATABASE SETUP ---
DB_PATH = os.environ.get("DB_PATH", "automation.db")

def init_db():
    # Ensure directory exists if path is in a subdirectory
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (topic TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    # Default: Auto Upload Mode ON (no manual approval needed)
    c.execute('''INSERT OR IGNORE INTO settings VALUES ('auto_mode', 'on')''')
    conn.commit()
    conn.close()

init_db()

def is_topic_recent(topic):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE topic=? AND date > ?", (topic, datetime.now().strftime('%Y-%m-%d')))
    res = c.fetchone()
    conn.close()
    return res is not None

# --- DATA FETCHERS ---
def fetch_stock_data():
    try:
        nifty = yf.Ticker("^NSEI").history(period="1d")
        sensex = yf.Ticker("^BSESN").history(period="1d")
        
        if nifty.empty or sensex.empty:
            # Try 5d if 1d is empty (e.g. weekend)
            nifty = yf.Ticker("^NSEI").history(period="5d")
            sensex = yf.Ticker("^BSESN").history(period="5d")

        data = {
            "nifty": round(nifty['Close'].iloc[-1], 2),
            "nifty_change": round(nifty['Close'].iloc[-1] - nifty['Open'].iloc[-1], 2),
            "sensex": round(sensex['Close'].iloc[-1], 2),
            "news": "FII/DII data shows positive sentiment. Market observing global cues."
        }
        return data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return {
            "nifty": 0,
            "nifty_change": 0,
            "sensex": 0,
            "news": "Data fetch failed. Please check later."
        }

def fetch_forex_data():
    try:
        # Using a free exchange rate API
        url = f"https://api.exchangerate-api.com/v4/latest/USD"
        res = requests.get(url).json()
        data = {
            "usd_inr": res['rates']['INR'],
            "eur_inr": round(res['rates']['INR'] / res['rates']['EUR'], 2),
            "sentiment": "RBI monetary policy update expected next week. Rupee remains stable."
        }
        return data
    except Exception as e:
        print(f"Error fetching forex data: {e}")
        return {
            "usd_inr": 0,
            "eur_inr": 0,
            "sentiment": "Forex data unavailable."
        }

def fetch_crypto_data():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
        res = requests.get(url).json()
        data = {
            "btc": res['bitcoin']['usd'],
            "btc_change": round(res['bitcoin']['usd_24h_change'], 2),
            "eth": res['ethereum']['usd'],
            "eth_change": round(res['ethereum']['usd_24h_change'], 2),
            "trend": "Bitcoin consolidating near resistance levels. Altcoins showing strength."
        }
        return data
    except Exception as e:
        print(f"Error fetching crypto data: {e}")
        return {
            "btc": 0,
            "btc_change": 0,
            "eth": 0,
            "eth_change": 0,
            "trend": "Market data temporarily unavailable."
        }

# --- SCRIPT GENERATION ---
def generate_script(niche, data):
    prompt = f"""
    Act as a professional financial news anchor. Create a 60-second YouTube Short script in Hinglish (Hindi + English) for the {niche} niche.
    Data for today: {json.dumps(data)}
    
    Structure:
    1. Hook: Catchy opening.
    2. Data: Mention the key numbers from the data provided.
    3. Analysis: Quick 1-sentence insight.
    4. Call to Action: Ask to subscribe.
    5. Disclaimer: Standard SEBI/Financial disclaimer at the end.
    
    Rules:
    - Language: Hinglish (Natural conversation like a news channel).
    - Tone: Energetic and professional.
    - DO NOT use words like 'guaranteed returns' or 'prediction'.
    - Keep it under 150 words.
    """
    
    # Method 1: Try Gemini SDK models
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-flash']
    for model_name in models_to_try:
        try:
            print(f"Trying Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"Script generated successfully with model: {model_name}")
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
    
    # Method 2: Try Gemini REST API directly (sometimes bypasses SDK quota issues)
    try:
        print("Trying Gemini REST API directly...")
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GENAI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(api_url, json=payload, timeout=30)
        if r.status_code == 200:
            text = r.json()['candidates'][0]['content']['parts'][0]['text']
            print("Script generated via REST API")
            return text
        else:
            print(f"REST API failed: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"REST API method failed: {e}")
    
    # Method 3: Hardcoded fallback script using live data (always works)
    print("Using hardcoded fallback script with live data")
    if niche == "Stocks":
        return f"""Namaste doston! Aaj ki sabse badi khabar — Nifty aaj {data.get('nifty', 'N/A')} pe band hua, 
        change raha {data.get('nifty_change', 'N/A')} points ka. Sensex bhi {data.get('sensex', 'N/A')} pe close hua. 
        {data.get('news', 'Market mein aaj mixed sentiment dikh raha hai.')} 
        Agar aap market updates chahte hain daily, toh abhi subscribe karein is channel ko. 
        Disclaimer: Yeh sirf educational information hai, koi financial advice nahi. 
        SEBI registered advisor se salah zaroor lein."""
    elif niche == "Forex":
        return f"""Namaste! Aaj dollar ke against rupee ka rate hai {data.get('usd_inr', 'N/A')}. 
        Euro rate hai {data.get('eur_inr', 'N/A')} rupaye. 
        {data.get('sentiment', 'Forex market mein stability dikh rahi hai.')} 
        Daily forex updates ke liye subscribe karein. 
        Disclaimer: Yeh educational content hai, investment advice nahi."""
    else:
        return f"""Crypto lovers, sun lo! Bitcoin aaj {data.get('btc', 'N/A')} dollar pe hai, 
        24 ghante mein change {data.get('btc_change', 'N/A')} percent raha. 
        Ethereum {data.get('eth', 'N/A')} dollar pe trade ho raha hai. 
        {data.get('trend', 'Crypto market mein volatility bani hui hai.')} 
        Subscribe karein aur bell icon dabao updates ke liye. 
        Disclaimer: Crypto mein invest karna high risk hai. Apna research zaroor karein."""

# --- VOICE GENERATION ---
def generate_voice(text, filename="voice.mp3"):
    # Method 1: Sarvam AI TTS
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {
            "text": text[:500],  # Sarvam has text length limits
            "target_language_code": "hi-IN",
            "speaker": "anushka",
            "model": "bulbul:v2"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            resp_json = response.json()
            # Handle both old ('audio_content') and new ('audios') response formats
            if 'audios' in resp_json and resp_json['audios']:
                audio_data = base64.b64decode(resp_json['audios'][0])
            elif 'audio_content' in resp_json:
                audio_data = base64.b64decode(resp_json['audio_content'])
            else:
                print(f"Sarvam: Unknown response format: {list(resp_json.keys())}")
                raise Exception("Unknown Sarvam response format")
            with open(filename, "wb") as f:
                f.write(audio_data)
            print(f"Voice generated via Sarvam AI: {filename}")
            return filename
        else:
            print(f"Sarvam AI Error ({response.status_code}): {response.text[:200]}")
    except Exception as e:
        print(f"Sarvam TTS failed: {e}")
    
    # Method 2: gTTS fallback (always free, no API key needed)
    try:
        from gtts import gTTS
        print("Falling back to gTTS...")
        tts = gTTS(text=text[:500], lang='hi', slow=False)
        tts.save(filename)
        print(f"Voice generated via gTTS: {filename}")
        return filename
    except Exception as e:
        print(f"gTTS also failed: {e}")
    
    return None

# --- MEDIA (B-ROLL) ---
def get_broll(query, count=3):
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}&orientation=portrait"
        res = requests.get(url, headers=headers).json()
        videos = [v['video_files'][0]['link'] for v in res['videos']]
        return videos
    except Exception as e:
        print(f"Pexels Error: {e}")
        return []

# --- VIDEO ASSEMBLY (MOVIEPY) ---
def download_video(url, path):
    """Download a video from URL to a local temp file"""
    try:
        # Pick lowest quality file to save RAM
        r = requests.get(url, stream=True, timeout=60)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        return path
    except Exception as e:
        print(f"Download failed: {e}")
        return None

def get_best_pexels_url(video_item):
    """Get lowest quality video file to conserve RAM on Render free plan"""
    files = video_item.get('video_files', [])
    # Sort by quality ascending (lowest first to save RAM)
    files_sorted = sorted(files, key=lambda x: x.get('width', 9999))
    for f in files_sorted:
        if f.get('width', 0) >= 360:  # At least 360p
            return f['link']
    return files[0]['link'] if files else None

def get_broll_with_urls(query, count=3):
    """Get broll URLs with metadata for quality selection"""
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}&orientation=portrait"
        res = requests.get(url, headers=headers, timeout=10).json()
        return [get_best_pexels_url(v) for v in res.get('videos', []) if get_best_pexels_url(v)]
    except Exception as e:
        print(f"Pexels Error: {e}")
        return []

def create_video(niche, script_text, voice_path, broll_urls, output_path="/tmp/final_video.mp4"):
    temp_files = []
    try:
        print(f"Starting video assembly for {niche}...")

        # 1. Load Audio
        audio = AudioFileClip(voice_path)
        total_duration = min(audio.duration, 60)  # Cap at 60 seconds

        # 2. Download broll videos to temp files (avoid streaming RAM issues)
        local_videos = []
        for i, url in enumerate(broll_urls[:3]):  # Max 3 clips
            tmp_path = f"/tmp/broll_{i}.mp4"
            temp_files.append(tmp_path)
            result = download_video(url, tmp_path)
            if result:
                local_videos.append(tmp_path)
            if len(local_videos) >= 3:
                break

        if not local_videos:
            print("No broll videos downloaded. Cannot create video.")
            return None

        # 3. Build clips
        num_clips = len(local_videos)
        duration_per_clip = total_duration / num_clips
        clips = []

        for i, vid_path in enumerate(local_videos):
            try:
                clip = VideoFileClip(vid_path)
                # Use subclip safely
                clip_dur = min(duration_per_clip, clip.duration)
                clip = clip.subclip(0, clip_dur)
                # Resize to 720x1280 (9:16) - low quality to save RAM
                clip = clip.resize(height=720)
                w, h = clip.size
                if w > 405:
                    clip = clip.crop(x1=(w-405)//2, y1=0, x2=(w+405)//2, y2=720)
                clips.append(clip)
            except Exception as ce:
                print(f"Clip {i} failed: {ce}")

        if not clips:
            print("No clips assembled.")
            return None

        # 4. Concatenate + Audio
        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.set_audio(audio.subclip(0, final_video.duration))

        # 5. Write output - low bitrate to save RAM/disk
        final_video.write_videofile(
            output_path, fps=24, codec="libx264",
            audio_codec="aac", bitrate="800k",
            temp_audiofile="/tmp/temp-audio.m4a",
            remove_temp=True, verbose=False, logger=None
        )
        print(f"Video created: {output_path}")

        # 6. Cleanup
        for c in clips:
            try: c.close()
            except: pass
        audio.close()
        final_video.close()

        return output_path

    except Exception as e:
        print(f"Video assembly failed: {e}")
        return None
    finally:
        # Always clean up temp video files
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except: pass



# --- YOUTUBE UPLOAD ---
def get_youtube_service():
    client_id = os.getenv("YT_CLIENT_ID")
    client_secret = os.getenv("YT_CLIENT_SECRET")
    refresh_token = os.getenv("YT_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise Exception("Missing YouTube OAuth credentials in .env")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    if creds.expired and creds.has_scopes():
        pass # build() will refresh it
    
    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(file_path, title, description):
    print(f"Uploading {file_path} to YouTube directly via Python...")
    youtube = get_youtube_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description + "\n\n#Shorts #Finance #NotFinancialAdvice",
            'tags': ['Shorts', 'Finance', 'Crypto', 'Stocks', 'Forex'],
            'categoryId': '27' # Education
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
            
    print(f"Upload Complete! Video ID: {response['id']}")
    return response['id']

# --- MAIN PIPELINE ---
def run_pipeline(niche):
    print(f"Starting pipeline for {niche}...")
    
    # 0. Check if already run today
    if is_topic_recent(niche):
        print(f"Pipeline for {niche} already completed today. Skipping.")
        return
    
    # 1. Fetch Data
    if niche == "Stocks": data = fetch_stock_data()
    elif niche == "Forex": data = fetch_forex_data()
    else: data = fetch_crypto_data()
    
    if not data: return
    
    # 2. Generate Script
    script = generate_script(niche, data)
    print(f"Script generated: {script[:50]}...")
    
    # 3. Voice
    voice_path = generate_voice(script)
    if not voice_path: return
    
    # 4. Media (use low-quality videos to save RAM on Render free plan)
    brolls = get_broll_with_urls(niche)
    
    # 5. Video
    video_path = create_video(niche, script, voice_path, brolls)
    if not video_path: return
    
    # 6. Approval / Upload
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='auto_mode'")
    auto_mode = c.fetchone()[0]
    
    title = f"{niche} Update: {datetime.now().strftime('%d %b %Y')}"
    
    if auto_mode == 'on':
        try:
            vid_id = upload_to_youtube(video_path, title, script)
            # Record in history
            c.execute("INSERT INTO history (topic, date) VALUES (?, ?)", (niche, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            bot.send_message(TELEGRAM_CHAT_ID, f"✅ Video Successfully Uploaded to YouTube! ID: {vid_id}\nLink: https://youtu.be/{vid_id}")
        except Exception as e:
            bot.send_message(TELEGRAM_CHAT_ID, f"❌ Auto-upload failed for {niche}: {e}")
    else:
        # Send to Telegram for approval
        try:
            with open(video_path, 'rb') as v:
                bot.send_video(TELEGRAM_CHAT_ID, v, caption=f"Pending Approval: {niche}\n\nTitle: {title}\n\nType /approve to post.")
            # We don't record in history yet, only after approval
        except Exception as e:
            bot.send_message(TELEGRAM_CHAT_ID, f"❌ Failed to send video to Telegram: {e}")
    
    conn.close()

# --- SCHEDULER ---
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_job(lambda: run_pipeline("Stocks"), 'cron', hour=8, minute=0)
scheduler.add_job(lambda: run_pipeline("Forex"), 'cron', hour=12, minute=0)
scheduler.add_job(lambda: run_pipeline("Crypto"), 'cron', hour=17, minute=0)
scheduler.start()

# --- FLASK ROUTES (For Keep-Alive & Triggers) ---
@app.route('/')
def home():
    return "YouTube Automation System is Running 24/7."

@app.route('/trigger/<niche>')
def trigger_pipeline(niche):
    if niche in ["Stocks", "Forex", "Crypto"]:
        # Run in background to avoid timeout
        import threading
        bot.send_message(TELEGRAM_CHAT_ID, f"🚀 [DEBUG] API Triggered for {niche}. Starting background pipeline...")
        threading.Thread(target=run_pipeline, args=(niche,)).start()
        return {"status": "triggered", "niche": niche}
    return {"status": "error", "message": "Invalid niche"}, 400

@app.route('/health')
def health():
    return {"status": "ok", "time": str(datetime.now())}

@app.route('/status_web')
def status_web():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='auto_mode'")
    auto_mode = c.fetchone()
    c.execute("SELECT topic, date FROM history ORDER BY date DESC LIMIT 5")
    history = c.fetchall()
    conn.close()
    return {
        "auto_mode": auto_mode[0] if auto_mode else "unknown",
        "recent_uploads": [{"topic": h[0], "date": h[1]} for h in history],
        "env_check": {
            "GEMINI_API_KEY": "SET" if GENAI_API_KEY else "MISSING",
            "SARVAM_API_KEY": "SET" if SARVAM_API_KEY else "MISSING",
            "PEXELS_API_KEY": "SET" if PEXELS_API_KEY else "MISSING",
            "TELEGRAM_BOT_TOKEN": "SET" if TELEGRAM_BOT_TOKEN else "MISSING",
            "MAKE_WEBHOOK_URL": "SET" if MAKE_WEBHOOK_URL else "MISSING",
        }
    }

@app.route('/test_upload')
def test_upload_route():
    import threading
    def test_task():
        try:
            bot.send_message(TELEGRAM_CHAT_ID, "🚀 [DEBUG] Test Upload Route Triggered...")
            # create a small text file as dummy video
            dummy_path = "/tmp/dummy.mp4"
            with open(dummy_path, "w") as f:
                f.write("dummy video data")
            bot.send_message(TELEGRAM_CHAT_ID, "🚀 [DEBUG] Uploading dummy video to YouTube...")
            vid_id = upload_to_youtube(dummy_path, "Test Render Upload", "Debug test")
            bot.send_message(TELEGRAM_CHAT_ID, f"✅ [DEBUG] Upload Success! ID: {vid_id}")
        except Exception as e:
            bot.send_message(TELEGRAM_CHAT_ID, f"❌ [DEBUG] Upload Failed: {str(e)}")
    
    threading.Thread(target=test_task).start()
    return {"status": "test_upload_started"}

@app.route('/test')
def run_test():
    results = {}

    # Test 1: Gemini
    try:
        models_tried = []
        script = None
        for m in ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m)
                r = model.generate_content("Say 'OK' in one word only.")
                script = r.text.strip()
                models_tried.append(f"{m}: OK")
                break
            except Exception as me:
                models_tried.append(f"{m}: FAIL - {str(me)[:80]}")
        results["gemini"] = {"status": "OK" if script else "FAIL", "models_tried": models_tried, "response": script}
    except Exception as e:
        results["gemini"] = {"status": "FAIL", "error": str(e)[:200]}

    # Test 2: Sarvam TTS
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {"text": "Test.", "target_language_code": "hi-IN", "speaker": "anushka", "model": "bulbul:v2"}
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        results["sarvam_tts"] = {"status": "OK" if r.status_code == 200 else "FAIL", "http_code": r.status_code, "response": r.text[:200]}
    except Exception as e:
        results["sarvam_tts"] = {"status": "FAIL", "error": str(e)[:200]}

    # Test 3: Pexels API
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        r = requests.get("https://api.pexels.com/videos/search?query=stocks&per_page=1&orientation=portrait", headers=headers, timeout=10)
        data = r.json()
        vid_url = data['videos'][0]['video_files'][0]['link'] if data.get('videos') else None
        results["pexels"] = {"status": "OK" if r.status_code == 200 else "FAIL", "http_code": r.status_code, "sample_video_url": vid_url}
    except Exception as e:
        results["pexels"] = {"status": "FAIL", "error": str(e)[:200]}

    # Test 4: Make.com Webhook Check
    try:
        if MAKE_WEBHOOK_URL:
            results["make_webhook"] = {"status": "OK", "url_set": True}
        else:
            results["make_webhook"] = {"status": "FAIL", "error": "MAKE_WEBHOOK_URL is missing in environment variables"}
    except Exception as e:
        results["make_webhook"] = {"status": "FAIL", "error": str(e)[:300]}

    # Overall
    all_ok = all(v.get("status") == "OK" for v in results.values())
    results["overall"] = "ALL SYSTEMS GO ✅" if all_ok else "SOME FAILURES ❌ - Check above"
    return results

# --- TELEGRAM HANDLERS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"👋 Welcome to YouTube Automation Bot!\n\nYour Chat ID is: `{chat_id}`\n\nCommands:\n/status - Check system status\n/approve - Upload pending video\n/auto_on - Enable fully auto mode\n/auto_off - Enable manual approval mode")

@bot.message_handler(commands=['status'])
def check_status(message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='auto_mode'")
    auto_mode = c.fetchone()[0]
    c.execute("SELECT topic, date FROM history ORDER BY date DESC LIMIT 1")
    last_run = c.fetchone()
    conn.close()
    
    status_msg = f"📊 *System Status*\n\nMode: `{'Fully Automated' if auto_mode == 'on' else 'Manual Approval'}`\n"
    if last_run:
        status_msg += f"Last Upload: {last_run[0]} on {last_run[1]}"
    else:
        status_msg += "Last Upload: None"
    
    bot.reply_to(message, status_msg, parse_mode='Markdown')

@bot.message_handler(commands=['auto_on'])
def auto_on(message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE settings SET value='on' WHERE key='auto_mode'")
    conn.commit()
    conn.close()
    bot.reply_to(message, "🚀 Auto-mode is ON! No more approvals needed.")

@bot.message_handler(commands=['auto_off'])
def auto_off(message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE settings SET value='off' WHERE key='auto_mode'")
    conn.commit()
    conn.close()
    bot.reply_to(message, "🛑 Auto-mode is OFF. Manual approval required.")

@bot.message_handler(commands=['approve'])
def approve_video(message):
    try:
        video_path = "/tmp/final_video.mp4"
        if os.path.exists(video_path):
            bot.reply_to(message, "🚀 Approval received! Uploading to YouTube...")
            vid_id = upload_to_youtube(video_path, "Market Update", "Daily financial analysis.")
            
            # Record in history (generic 'Approved Video' or try to guess niche)
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO history (topic, date) VALUES (?, ?)", ("Approved Video", datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
            
            bot.send_message(TELEGRAM_CHAT_ID, f"✅ Successfully Posted: https://youtu.be/{vid_id}")
        else:
            bot.reply_to(message, "❌ No video found to approve.")
    except Exception as e:
        bot.reply_to(message, f"❌ Upload failed: {e}")

def run_bot():
    print("Telegram Bot is starting...")
    bot.infinity_polling()

# --- START SERVICES ---
init_db()
print("Starting background services...")

# Start Telegram bot
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# Scheduler is already started above in the global scope

if __name__ == "__main__":
    # Fallback for local testing
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
