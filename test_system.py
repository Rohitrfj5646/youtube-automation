import os
import json
import requests
import yfinance as yf
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import base64

load_dotenv()

# --- CONFIGURATION ---
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

genai.configure(api_key=GENAI_API_KEY)

def test_pipeline(niche):
    print(f"\n--- Testing Pipeline for {niche} ---")
    
    # 1. Data Fetching
    print("Step 1: Fetching data...")
    if niche == "Stocks":
        try:
            nifty = yf.Ticker("^NSEI").history(period="1d")
            print(f"✅ Stock Data Fetched: Nifty @ {nifty['Close'].iloc[-1]}")
            data = {"nifty": nifty['Close'].iloc[-1], "news": "Test News"}
        except Exception as e:
            print(f"❌ Stock Data Failed: {e}")
            return
    elif niche == "Crypto":
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            res = requests.get(url).json()
            print(f"✅ Crypto Data Fetched: BTC @ {res['bitcoin']['usd']}")
            data = {"btc": res['bitcoin']['usd'], "trend": "Consolidating"}
        except Exception as e:
            print(f"❌ Crypto Data Failed: {e}")
            return
            
    # 2. Script Generation
    print("Step 2: Generating script with Gemini...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Create a 15-word Hinglish update for {niche} using data {json.dumps(data)}"
        response = model.generate_content(prompt)
        script = response.text
        print(f"✅ Script Generated: {script}")
    except Exception as e:
        print(f"❌ Script Generation Failed: {e}")
        return

    # 3. Voice Generation (Dry Run - just check API)
    print("Step 3: Checking Sarvam AI connectivity...")
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
        payload = {
            "text": "नमस्ते",
            "target_language_code": "hi-IN",
            "speaker": "meera",
            "model": "bulbul:v2"
        }
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            print("✅ Sarvam AI Connected Successfully.")
        else:
            print(f"❌ Sarvam AI Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ Sarvam AI Failed: {e}")

    # 4. Media
    print("Step 4: Checking Pexels B-Roll search...")
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={niche}&per_page=1"
        res = requests.get(url, headers=headers).json()
        if 'videos' in res and len(res['videos']) > 0:
            print(f"✅ Pexels Found Media: {res['videos'][0]['video_files'][0]['link'][:50]}...")
        else:
            print("❌ Pexels found no media.")
    except Exception as e:
        print(f"❌ Pexels Failed: {e}")

if __name__ == "__main__":
    print("Starting System Integration Test (Dry Run Mode)")
    test_pipeline("Stocks")
    test_pipeline("Crypto")
    print("\n--- Test Completed ---")
