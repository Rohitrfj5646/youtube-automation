import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    print("Testing Gemini API...")
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, this is a test.")
        print(f"Gemini Response: {response.text}")
        return True
    except Exception as e:
        print(f"Gemini Error: {e}")
        return False

def test_sarvam():
    print("Testing Sarvam AI API...")
    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {"api-subscription-key": os.getenv("SARVAM_API_KEY"), "Content-Type": "application/json"}
        payload = {
            "text": "नमस्ते, यह एक परीक्षण है।",
            "target_language_code": "hi-IN",
            "speaker": "meera",
            "model": "bulbul:v2"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Sarvam AI Response: Success")
            return True
        else:
            print(f"Sarvam AI Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Sarvam AI Error: {e}")
        return False

def test_pexels():
    print("Testing Pexels API...")
    try:
        headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
        url = "https://api.pexels.com/videos/search?query=stocks&per_page=1"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            print("Pexels Response: Success")
            return True
        else:
            print(f"Pexels Error: {res.status_code}")
            return False
    except Exception as e:
        print(f"Pexels Error: {e}")
        return False

if __name__ == "__main__":
    test_gemini()
    test_sarvam()
    test_pexels()
