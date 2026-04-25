"""
╔══════════════════════════════════════════════════════════════╗
║         🚀 AGENT 3 — RENDER DEPLOYER                        ║
║   GitHub push ke baad Render deployment monitor karta hai   ║
║   Health check karta hai jab tak live na ho jaaye           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ANSI Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ─── CONFIGURATION ────────────────────────────────────────────
# Apna Render service URL yahan daalo (deploy hone ke baad)
RENDER_SERVICE_URL = os.getenv("RENDER_SERVICE_URL", "").rstrip("/")
RENDER_API_KEY     = os.getenv("RENDER_API_KEY", "")
RENDER_SERVICE_ID  = os.getenv("RENDER_SERVICE_ID", "")

def banner():
    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║             🚀 AGENT 3 — RENDER DEPLOYER                    ║
║          YouTube Automation System v1.0                      ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

# ─── STEP 1: Render API — Trigger Deploy ──────────────────────
def trigger_render_deploy():
    print(f"\n{BOLD}━━━ [STEP 1] TRIGGER RENDER DEPLOYMENT ━━━{RESET}")

    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        print(f"  {YELLOW}⚠️  RENDER_API_KEY or RENDER_SERVICE_ID not set in .env{RESET}")
        print(f"\n  {CYAN}📋 MANUAL DEPLOY INSTRUCTIONS:{RESET}")
        print(f"  ┌─────────────────────────────────────────────────────┐")
        print(f"  │  1. Go to: https://dashboard.render.com             │")
        print(f"  │  2. Select your service: youtube-automation         │")
        print(f"  │  3. Click 'Manual Deploy' → 'Deploy latest commit'  │")
        print(f"  │  4. Wait for 'Live' status (usually 5-10 mins)      │")
        print(f"  └─────────────────────────────────────────────────────┘")
        print(f"\n  {YELLOW}ℹ️  Skipping API trigger. Proceeding to health monitoring...{RESET}")
        return None

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        print(f"  📡 Triggering deploy via Render API...")
        url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys"
        response = requests.post(url, headers=headers, json={"clearCache": "do_not_clear"})

        if response.status_code in [200, 201]:
            deploy_data = response.json()
            deploy_id = deploy_data.get("deploy", {}).get("id", "unknown")
            print(f"  {GREEN}✅ Deploy triggered! Deploy ID: {deploy_id}{RESET}")
            return deploy_id
        else:
            print(f"  {RED}❌ Deploy trigger failed: {response.status_code}{RESET}")
            print(f"     {response.text}")
            return None
    except Exception as e:
        print(f"  {RED}❌ API call failed: {e}{RESET}")
        return None

# ─── STEP 2: Monitor Deploy Status ────────────────────────────
def monitor_deploy_status(deploy_id):
    print(f"\n{BOLD}━━━ [STEP 2] MONITORING DEPLOY STATUS ━━━{RESET}")

    if not RENDER_API_KEY or not RENDER_SERVICE_ID or not deploy_id:
        print(f"  {YELLOW}ℹ️  Skipping API monitoring (no credentials/deploy_id){RESET}")
        print(f"  {CYAN}Check your Render dashboard for build status.{RESET}")
        return True

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {RENDER_API_KEY}"
    }
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys/{deploy_id}"

    max_wait = 15 * 60  # 15 minutes max
    check_interval = 20  # check every 20 seconds
    elapsed = 0

    print(f"  ⏳ Waiting for deployment to complete (max 15 minutes)...")
    print(f"  {'─'*50}")

    while elapsed < max_wait:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data.get("deploy", {}).get("status", "unknown")
                created = data.get("deploy", {}).get("createdAt", "")

                timestamp = datetime.now().strftime('%H:%M:%S')
                status_icons = {
                    "build_in_progress": f"{YELLOW}🔨 Building...{RESET}",
                    "update_in_progress": f"{YELLOW}🔄 Updating...{RESET}",
                    "live": f"{GREEN}✅ LIVE!{RESET}",
                    "deactivated": f"{RED}❌ Deactivated{RESET}",
                    "build_failed": f"{RED}❌ Build FAILED{RESET}",
                    "pre_deploy_in_progress": f"{YELLOW}⚙️  Pre-deploy...{RESET}",
                    "created": f"{CYAN}📋 Created{RESET}",
                }
                display = status_icons.get(status, f"{YELLOW}⏳ {status}{RESET}")
                print(f"  [{timestamp}] Status: {display}")

                if status == "live":
                    print(f"\n  {GREEN}{BOLD}🎉 Deployment SUCCESSFUL! Service is LIVE!{RESET}")
                    return True
                elif status in ["build_failed", "deactivated"]:
                    print(f"\n  {RED}{BOLD}❌ Deployment FAILED! Status: {status}{RESET}")
                    print(f"  Check Render dashboard logs for details.")
                    return False

            time.sleep(check_interval)
            elapsed += check_interval

        except Exception as e:
            print(f"  {RED}⚠️  Monitor error: {e}{RESET}")
            time.sleep(check_interval)
            elapsed += check_interval

    print(f"\n  {YELLOW}⏰ Timeout after 15 minutes. Check Render dashboard manually.{RESET}")
    return False

# ─── STEP 3: Health Check ─────────────────────────────────────
def health_check(service_url, max_retries=10, interval=30):
    print(f"\n{BOLD}━━━ [STEP 3] HEALTH CHECK ━━━{RESET}")

    if not service_url:
        print(f"  {YELLOW}⚠️  RENDER_SERVICE_URL not set!{RESET}")
        print(f"  {CYAN}Set it in .env: RENDER_SERVICE_URL=https://your-service.onrender.com{RESET}")
        print(f"\n  {CYAN}After deploy, run Agent 4 to test your live URL:{RESET}")
        print(f"     python agent4_tester.py https://your-service.onrender.com")
        return False

    health_url = f"{service_url}/health"
    print(f"  🔗 Checking: {health_url}")
    print(f"  ⏳ Will retry up to {max_retries} times (every {interval}s)...")
    print(f"  {'─'*50}")

    for attempt in range(1, max_retries + 1):
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"  [{timestamp}] Attempt {attempt}/{max_retries}...", end=" ", flush=True)
            response = requests.get(health_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"{GREEN}✅ HEALTHY{RESET}")
                print(f"\n  {GREEN}{BOLD}🎉 Service is LIVE and HEALTHY!{RESET}")
                print(f"  📊 Response: {json.dumps(data, indent=4)}")
                return True
            else:
                print(f"{YELLOW}⚠️  Status {response.status_code}{RESET}")

        except requests.exceptions.ConnectionError:
            print(f"{YELLOW}⏳ Not ready yet (connection refused){RESET}")
        except requests.exceptions.Timeout:
            print(f"{YELLOW}⏳ Timeout — service starting up{RESET}")
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")

        if attempt < max_retries:
            print(f"     Waiting {interval}s before next check...")
            time.sleep(interval)

    print(f"\n  {RED}❌ Health check failed after {max_retries} attempts{RESET}")
    print(f"  {YELLOW}Check your Render dashboard for build logs.{RESET}")
    return False

# ─── STEP 4: Verify Endpoints ─────────────────────────────────
def verify_endpoints(service_url):
    print(f"\n{BOLD}━━━ [STEP 4] ENDPOINT VERIFICATION ━━━{RESET}")

    if not service_url:
        print(f"  {YELLOW}⚠️  Skipping — RENDER_SERVICE_URL not set{RESET}")
        return

    endpoints = [
        ("GET", "/",         "Service homepage"),
        ("GET", "/health",   "Health check endpoint"),
    ]

    for method, path, description in endpoints:
        url = f"{service_url}{path}"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                print(f"  {GREEN}✅ {method} {path:<25} {description}{RESET}")
            else:
                print(f"  {YELLOW}⚠️  {method} {path:<25} Status: {response.status_code}{RESET}")
        except Exception as e:
            print(f"  {RED}❌ {method} {path:<25} Error: {e}{RESET}")

# ─── SUMMARY ──────────────────────────────────────────────────
def print_summary(service_url, deploy_success, health_ok):
    print(f"\n{CYAN}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}  📊 AGENT 3 SUMMARY{RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

    deploy_st = f"{GREEN}✅ Success{RESET}" if deploy_success else f"{YELLOW}⚠️  Manual needed{RESET}"
    health_st  = f"{GREEN}✅ Healthy{RESET}" if health_ok else f"{RED}❌ Not reachable{RESET}"

    print(f"\n  Deploy Trigger : {deploy_st}")
    print(f"  Health Check   : {health_st}")

    if service_url:
        print(f"\n  🌐 Live URL: {GREEN}{service_url}{RESET}")
        print(f"\n  {BOLD}🚀 Next Step: Run Agent 4 to test live endpoints{RESET}")
        print(f"     python agent4_tester.py {service_url}")
    else:
        print(f"\n  {YELLOW}💡 After Render deploy, set RENDER_SERVICE_URL in .env and run:{RESET}")
        print(f"     python agent4_tester.py https://your-service.onrender.com")

    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    banner()

    # Get service URL from args or env
    service_url = RENDER_SERVICE_URL
    if len(sys.argv) > 1:
        service_url = sys.argv[1].rstrip("/")
        print(f"  📌 Using URL from argument: {service_url}")

    # Step 1: Trigger deploy
    deploy_id = trigger_render_deploy()
    deploy_success = deploy_id is not None or True  # True if manual

    # Step 2: Monitor if we have API access
    if deploy_id:
        monitor_deploy_status(deploy_id)

    # Step 3: Health check
    health_ok = health_check(service_url, max_retries=8, interval=30)

    # Step 4: Verify endpoints
    if health_ok:
        verify_endpoints(service_url)

    print_summary(service_url, deploy_success, health_ok)
    return health_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
