import os
import sys
import json
import sqlite3
import requests
import yfinance as yf
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
import telebot
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import time

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")

# Constants
HISTORY_FILE = "history.json"
TEMP_DIR = "temp" if os.name == 'nt' else "/tmp"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize APIs
genai.configure(api_key=GENAI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

def send_telegram(message):
    print(f"[TELEGRAM] {message}")
    if bot and TELEGRAM_CHAT_ID:
        try:
            bot.send_message(TELEGRAM_CHAT_ID, message)
        except Exception as e:
            print(f"Telegram failed: {e}")

# --- HISTORY TRACKING ---
def has_already_uploaded(niche):
    if not os.path.exists(HISTORY_FILE):
        return False
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            today = datetime.now().strftime('%Y-%m-%d')
            return history.get(today, {}).get(niche, False)
    except:
        return False

def mark_as_uploaded(niche):
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            pass
    
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in history:
        history[today] = {}
    history[today][niche] = True
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# --- DATA FETCHERS ---
def fetch_data(niche):
    try:
        if niche == "Stocks":
            nifty_ticker = yf.Ticker("^NSEI")
            sensex_ticker = yf.Ticker("^BSESN")
            
            # Try 1d, then 5d if empty
            nifty = nifty_ticker.history(period="1d")
            if nifty.empty: nifty = nifty_ticker.history(period="5d")
            
            sensex = sensex_ticker.history(period="1d")
            if sensex.empty: sensex = sensex_ticker.history(period="5d")
            
            if nifty.empty or sensex.empty:
                raise Exception("Stock data is empty for both 1d and 5d periods.")

            return {
                "nifty": round(nifty['Close'].iloc[-1], 2),
                "nifty_change": round(nifty['Close'].iloc[-1] - nifty['Open'].iloc[-1], 2),
                "sensex": round(sensex['Close'].iloc[-1], 2),
                "news": "Market is reacting to global cues and FII data."
            }
        elif niche == "Forex":
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            res = requests.get(url).json()
            return {
                "usd_inr": res['rates']['INR'],
                "eur_inr": round(res['rates']['INR'] / res['rates']['EUR'], 2),
                "sentiment": "Rupee remains stable against the greenback."
            }
        elif niche == "Crypto":
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
            res = requests.get(url).json()
            return {
                "btc": res['bitcoin']['usd'],
                "btc_change": round(res['bitcoin']['usd_24h_change'], 2),
                "eth": res['ethereum']['usd'],
                "eth_change": round(res['ethereum']['usd_24h_change'], 2),
                "trend": "Crypto market showing mixed signals today."
            }
    except Exception as e:
        print(f"Data fetch error: {e}")
    return None

# --- SCRIPT GENERATION ---
def generate_script(niche, data):
    prompt = f"Create a 60-second YouTube Short script in Hinglish for {niche}. Data: {json.dumps(data)}. Rules: Catchy hook, energetic tone, natural conversation."
    
    # Try Gemini
    for model_name in ['gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini {model_name} failed: {e}")
    
    # Fallback
    print("Using hardcoded fallback script...")
    if niche == "Stocks":
        return f"Nifty aaj {data.get('nifty')} pe band hua. Market mein tezi dikh rahi hai. Subscribe karein!"
    return f"Latest {niche} update: Check out the numbers! Follow for more."

# --- VOICE GENERATION ---
def generate_voice(text, filename="voice.mp3"):
    path = os.path.join(TEMP_DIR, filename)
    # Try Sarvam
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {"text": text[:500], "target_language_code": "hi-IN", "speaker": "anushka", "model": "bulbul:v2"}
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            audio_data = base64.b64decode(r.json()['audios'][0])
            with open(path, "wb") as f:
                f.write(audio_data)
            return path
    except Exception as e:
        print(f"Sarvam failed: {e}")
    
    # Try gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:500], lang='hi')
        tts.save(path)
        return path
    except:
        pass
    return None

# --- MEDIA & VIDEO ---
def get_broll(query):
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=3&orientation=portrait"
        res = requests.get(url, headers=headers).json()
        return [v['video_files'][0]['link'] for v in res.get('videos', [])]
    except:
        return []

def create_video(niche, voice_path, broll_urls):
    output_path = os.path.join(TEMP_DIR, f"final_{niche}.mp4")
    try:
        audio = AudioFileClip(voice_path)
        clips = []
        for i, url in enumerate(broll_urls):
            tmp_vid = os.path.join(TEMP_DIR, f"tmp_{i}.mp4")
            r = requests.get(url, stream=True)
            with open(tmp_vid, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            clip = VideoFileClip(tmp_vid).subclip(0, audio.duration/len(broll_urls)).resize(height=720)
            clips.append(clip)
        
        final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", bitrate="2000k")
        return output_path
    except Exception as e:
        print(f"Video Creation Error: {e}")
    return None

# --- YOUTUBE UPLOAD ---
def upload_to_youtube(file_path, title, description):
    print(f"Uploading to YouTube: {title}")
    creds = Credentials(
        token=None,
        refresh_token=YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID,
        client_secret=YT_CLIENT_SECRET
    )
    youtube = build('youtube', 'v3', credentials=creds)
    
    body = {
        'snippet': {'title': title, 'description': description, 'categoryId': '27'},
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
    return response['id']

# --- MAIN RUNNER ---
def run(niche):
    print(f"🚀 Starting CLI Pipeline for {niche}")
    
    if has_already_uploaded(niche):
        print(f"Already uploaded {niche} today. Skipping.")
        return

    data = fetch_data(niche)
    if not data:
        raise Exception(f"Failed to fetch data for {niche}. Check API/Network.")
    
    script = generate_script(niche, data)
    voice = generate_voice(script)
    if not voice:
        raise Exception("Failed to generate voice (Sarvam/gTTS failed).")
    
    brolls = get_broll(niche)
    if not brolls:
        raise Exception(f"Failed to get B-Roll for {niche} from Pexels.")
    
    video = create_video(niche, voice, brolls)
    if not video:
        raise Exception("Failed to create video (MoviePy crash?).")
    
    title = f"{niche} Update: {datetime.now().strftime('%d %b %Y')}"
    try:
        vid_id = upload_to_youtube(video, title, script)
        mark_as_uploaded(niche)
        send_telegram(f"✅ Video Uploaded! ID: {vid_id}\nLink: https://youtu.be/{vid_id}")
    except Exception as e:
        send_telegram(f"❌ Critical Pipeline Error for {niche}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        niche_arg = sys.argv[1] if len(sys.argv) > 1 else "Stocks"
        run(niche_arg)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
