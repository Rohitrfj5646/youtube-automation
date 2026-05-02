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
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ColorClip
import moviepy.video.fx.all as vfx
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
    prompt = f"""
    Act as a professional financial news anchor for a top news channel. 
    Create a detailed 60-second news script in Hinglish (natural Hindi + English financial terms) for the {niche} niche.
    
    Data for today: {json.dumps(data)}
    
    Structure:
    1. Hook: Catchy opening that grabs attention.
    2. Headlines: Top 2-3 news points based on the data.
    3. Deep Dive: Explain the 'why' behind the numbers in simple but professional terms.
    4. Market Sentiment: What should investors watch out for?
    5. Call to Action: Professional invitation to subscribe for daily updates.
    6. Disclaimer: Standard financial disclaimer.
    
    Rules:
    - Tone: Energetic, authoritative, and informative.
    - Style: Natural conversation, not robotic.
    - Length: Approximately 180-220 words (to hit 60 seconds).
    - Language: Primarily Hindi with English technical terms (Market, Stocks, Bullish, Bearish, etc.).
    - DO NOT use generic phrases; use the actual data provided.
    """
    
    # Try Gemini
    for model_name in ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-2.0-flash']:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            script = response.text.strip()
            if len(script.split()) > 100: # Ensure it's not too short
                return script
        except Exception as e:
            print(f"Gemini {model_name} failed: {e}")
    
    # Fallback (Improved)
    print("Using hardcoded fallback script...")
    if niche == "Stocks":
        return f"Namaste! Stock market mein aaj halchal tez rahi. Nifty {data.get('nifty')} par band hua, jisme {data.get('nifty_change')} points ki badhat dekhi gayi. Sensex bhi {data.get('sensex')} par close hua. Market experts ka manna hai ki global cues ki wajah se investors mein utsah hai. Aisi hi daily updates ke liye hamare channel ko abhi subscribe karein. Disclaimer: Yeh sirf educational information hai."
    return f"Latest {niche} update: Markets are showing interesting trends today with {json.dumps(data)}. Stay tuned and subscribe for more detailed analysis."

# --- VOICE GENERATION ---
def generate_voice(text, filename="voice.mp3"):
    path = os.path.join(TEMP_DIR, filename)
    # Sarvam allows up to 1500 chars for Bulbul v2
    safe_text = text[:1400] 
    
    # Try Sarvam
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {"text": safe_text, "target_language_code": "hi-IN", "speaker": "anushka", "model": "bulbul:v2"}
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
        tts = gTTS(text=safe_text, lang='hi')
        tts.save(path)
        return path
    except:
        pass
    return None

# --- MEDIA & VIDEO ---
def get_broll(query):
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        # Increased to 15 clips for 60s video
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"
        res = requests.get(url, headers=headers).json()
        return [v['video_files'][0]['link'] for v in res.get('videos', [])]
    except:
        return []

def create_video(niche, voice_path, broll_urls, script_text=""):
    output_path = os.path.join(TEMP_DIR, f"final_{niche}.mp4")
    try:
        audio = AudioFileClip(voice_path)
        target_duration = audio.duration
        print(f"Target Video Duration: {target_duration}s")
        
        clips = []
        current_duration = 0
        
        for i, url in enumerate(broll_urls):
            if current_duration >= target_duration:
                break
                
            tmp_vid = os.path.join(TEMP_DIR, f"tmp_{i}.mp4")
            r = requests.get(url, stream=True)
            with open(tmp_vid, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            
            try:
                clip = VideoFileClip(tmp_vid).resize(height=1280) # 9:16 target
                # Crop to 720x1280 if wider
                w, h = clip.size
                if w > 720:
                    clip = clip.crop(x1=(w-720)//2, y1=0, x2=(w+720)//2, y2=1280)
                
                # Dynamic duration for this clip
                remaining = target_duration - current_duration
                clip_dur = min(clip.duration, 5) # Use max 5s per clip for fast pacing
                clip_dur = min(clip_dur, remaining)
                
                clip = clip.subclip(0, clip_dur)
                
                # Add subtle Zoom effect (Human-like editing)
                clip = clip.resize(lambda t: 1 + 0.03 * t) 
                
                # Add crossfade transition
                if clips:
                    clip = clip.crossfadein(0.5)
                
                clips.append(clip)
                current_duration += clip_dur
            except Exception as e:
                print(f"Clip {i} error: {e}")

        if not clips:
            return None

        # Assemble Background
        bg_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
        
        # --- ADVANCED NEWS OVERLAYS ---
        
        # 1. Breaking News Ticker (Bottom)
        ticker_bg = ColorClip(size=(720, 60), color=(200, 0, 0)).set_opacity(0.8).set_duration(target_duration).set_position(('center', 1100))
        
        ticker_text = TextClip(f" BREAKING NEWS: {niche.upper()} UPDATES - LIVE ANALYSIS - SUBSCRIBE FOR MORE ", 
                              fontsize=30, color='white', font='Arial-Bold', method='caption', size=(2000, None))
        # Scrolling effect
        scrolling_ticker = ticker_text.set_duration(target_duration).set_position(lambda t: (100 - 150*t, 1115))
        
        # 2. Headline Box (Top)
        headline_bg = ColorClip(size=(600, 80), color=(0, 0, 0)).set_opacity(0.7).set_duration(target_duration).set_position(('center', 100))
        headline_text = TextClip(f"{niche.upper()} TODAY", fontsize=40, color='yellow', font='Arial-Bold').set_duration(target_duration).set_position(('center', 120))

        # 3. Channel Branding
        branding = TextClip("@FINANCE_INSIGHTS", fontsize=25, color='white', font='Arial').set_duration(target_duration).set_opacity(0.5).set_position((450, 50))

        # Combine all
        final_video = CompositeVideoClip([bg_video, ticker_bg, scrolling_ticker, headline_bg, headline_text, branding])
        
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", bitrate="3000k")
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
        client_secret=YT_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/youtube.upload']
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
        # Smart Niche Detection
        if "Crypto" in niche_arg: niche_arg = "Crypto"
        elif "Forex" in niche_arg: niche_arg = "Forex"
        elif "Stocks" in niche_arg: niche_arg = "Stocks"
        
        run(niche_arg)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
