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
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")

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
    # Try latest models in order of preference
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
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
    - DO NOT use words like "guaranteed returns" or "prediction".
    - Keep it under 150 words.
    """
    last_error = None
    for model_name in models_to_try:
        try:
            print(f"Trying Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"Script generated successfully with model: {model_name}")
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_error = e
    raise Exception(f"All Gemini models failed. Last error: {last_error}")

# --- VOICE GENERATION ---
def generate_voice(text, filename="voice.mp3"):
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "target_language_code": "hi-IN",
            "speaker": "meera",
            "model": "bulbul:v2"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            audio_data = base64.b64decode(response.json()['audio_content'])
            with open(filename, "wb") as f:
                f.write(audio_data)
            return filename
        else:
            print(f"Sarvam AI Error: {response.text}")
            return None
    except Exception as e:
        print(f"Voice generation failed: {e}")
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
def create_video(niche, script_text, voice_path, broll_urls, output_path="/tmp/final_video.mp4"):
    try:
        print(f"Starting MoviePy assembly for {niche}...")
        
        # 1. Load Audio
        audio = AudioFileClip(voice_path)
        total_duration = audio.duration
        
        # 2. Prepare Clips
        clips = []
        # Split script into segments for text overlays
        segments = [s.strip() for s in script_text.split('.') if len(s.strip()) > 10]
        
        # Duration per clip
        if not segments: segments = [script_text[:50]]
        num_clips = min(len(segments), len(broll_urls))
        if num_clips == 0: num_clips = 1
        
        duration_per_clip = total_duration / num_clips
        
        for i in range(num_clips):
            try:
                # Download/Load video from URL
                video_url = broll_urls[i] if i < len(broll_urls) else broll_urls[0]
                clip = VideoFileClip(video_url).subclip(0, duration_per_clip)
                
                # Resize to vertical (9:16)
                clip = clip.resize(height=1280)
                # Crop to center 720x1280
                w, h = clip.size
                clip = clip.crop(x1=(w-720)/2, y1=0, x2=(w+720)/2, y2=1280)
                
                # Add text overlay
                txt_str = segments[i] if i < len(segments) else segments[0]
                # Note: TextClip requires ImageMagick. If not available, we can skip or use a fallback.
                try:
                    txt_clip = TextClip(txt_str, fontsize=40, color='white', font='Arial-Bold', 
                                       method='caption', size=(600, None), align='center')
                    txt_clip = txt_clip.set_duration(duration_per_clip).set_position(('center', 800))
                    clip = CompositeVideoClip([clip, txt_clip])
                except Exception as te:
                    print(f"Warning: TextClip failed (likely ImageMagick missing): {te}")
                
                clips.append(clip)
            except Exception as ce:
                print(f"Error processing clip {i}: {ce}")
        
        if not clips:
            print("Error: No clips generated.")
            return None
            
        # 3. Concatenate and add Audio
        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.set_audio(audio)
        
        # 4. Write Output
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile="/tmp/temp-audio.m4a", remove_temp=True)
        
        # Close clips to free memory
        for c in clips: c.close()
        audio.close()
        
        return output_path
    except Exception as e:
        print(f"MoviePy Assembly Failed: {e}")
        return None

# --- YOUTUBE UPLOAD ---
def get_yt_service():
    creds = Credentials(
        None,
        refresh_token=YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID,
        client_secret=YT_CLIENT_SECRET
    )
    if not creds.valid:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(file_path, title, description):
    from googleapiclient.http import MediaFileUpload
    youtube = get_yt_service()
    
    body = {
        "snippet": {
            "title": title,
            "description": description + "\n\n#StockMarket #Finance #Hindi #NotFinancialAdvice",
            "categoryId": "27" # Education
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
            
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
    
    # 4. Media
    brolls = get_broll(niche)
    
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
            bot.send_message(TELEGRAM_CHAT_ID, f"✅ Video Posted: https://youtu.be/{vid_id}")
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
        threading.Thread(target=run_pipeline, args=(niche,)).start()
        return {"status": "triggered", "niche": niche}
    return {"status": "error", "message": "Invalid niche"}, 400

@app.route('/health')
def health():
    return {"status": "ok", "time": str(datetime.now())}

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
