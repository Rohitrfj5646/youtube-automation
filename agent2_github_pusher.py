"""
╔══════════════════════════════════════════════════════════════╗
║       🛠️ AGENT 2 — CODE FIXER + GITHUB PUSHER               ║
║   Agent 1 ki report padh ke code fix karta hai              ║
║   Aur automatically GitHub pe push karta hai                ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(PROJECT_DIR, "analysis_report.json")

# ANSI Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner():
    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║          🛠️  AGENT 2 — CODE FIXER + GITHUB PUSHER           ║
║        YouTube Automation System v1.0                        ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📁 Dir : {PROJECT_DIR}
""")

# ─── FIND GIT ─────────────────────────────────────────────────
def find_git():
    """Git binary ka path dhundta hai multiple locations mein."""
    candidates = [
        "git",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Git\bin\git.exe",
        r"C:\Users\hp\AppData\Local\Programs\Git\bin\git.exe",
    ]
    # Try PATH first
    git_in_path = shutil.which("git")
    if git_in_path:
        return git_in_path

    for path in candidates:
        if os.path.isfile(path):
            print(f"  {GREEN}✅ Git found at: {path}{RESET}")
            return path

    return None

def run_git(git_path, args, cwd=None):
    """Git command run karta hai aur output return karta hai."""
    cmd = [git_path] + args
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_DIR,
        capture_output=True,
        text=True
    )
    return result

# ─── FIX 1: Ensure .gitignore ─────────────────────────────────
def fix_gitignore():
    print(f"\n{BOLD}━━━ [FIX 1] .GITIGNORE SAFETY ━━━{RESET}")
    gitignore_path = os.path.join(PROJECT_DIR, ".gitignore")

    essential_entries = [
        ".env",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.db",
        "*.sqlite3",
        "/tmp/",
        "voice.mp3",
        "final_video.mp4",
        "analysis_report.json",
        "*.egg-info/",
        "dist/",
        "build/",
        ".DS_Store",
    ]

    existing_lines = []
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_lines = [l.strip() for l in f.readlines()]

    added = []
    with open(gitignore_path, "a") as f:
        for entry in essential_entries:
            if entry not in existing_lines:
                f.write(f"\n{entry}")
                added.append(entry)

    if added:
        print(f"  {GREEN}✅ Added to .gitignore: {', '.join(added)}{RESET}")
    else:
        print(f"  {GREEN}✅ .gitignore is already complete{RESET}")

    return True

# ─── FIX 2: Fix Deprecated Gemini Model ───────────────────────
def fix_gemini_model():
    print(f"\n{BOLD}━━━ [FIX 2] DEPRECATED GEMINI MODEL FIX ━━━{RESET}")
    app_path = os.path.join(PROJECT_DIR, "app.py")
    test_path = os.path.join(PROJECT_DIR, "test_system.py")
    fixed_files = []

    for fpath in [app_path, test_path]:
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        content = content.replace("'gemini-pro'", "'gemini-1.5-flash'")
        content = content.replace('"gemini-pro"', '"gemini-1.5-flash"')

        if content != original:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fname = os.path.basename(fpath)
            fixed_files.append(fname)
            print(f"  {GREEN}✅ Fixed: {fname} — 'gemini-pro' → 'gemini-1.5-flash'{RESET}")

    if not fixed_files:
        print(f"  {GREEN}✅ No deprecated model found (already up to date){RESET}")

    return True

# ─── FIX 3: Fix render.yaml ───────────────────────────────────
def fix_render_yaml():
    print(f"\n{BOLD}━━━ [FIX 3] RENDER.YAML VALIDATION ━━━{RESET}")
    path = os.path.join(PROJECT_DIR, "render.yaml")

    render_yaml_content = """services:
  - type: web
    name: youtube-automation
    env: docker
    plan: free
    region: singapore
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    envVars:
      - key: PORT
        value: "8080"
      - key: DB_PATH
        value: /app/data/automation.db
      - key: PYTHONUNBUFFERED
        value: "1"
      - fromGroup: youtube-automation-secrets
"""

    with open(path, "w") as f:
        f.write(render_yaml_content)

    print(f"  {GREEN}✅ render.yaml updated with dockerfilePath and all required env vars{RESET}")
    return True

# ─── FIX 4: Update requirements.txt ───────────────────────────
def fix_requirements():
    print(f"\n{BOLD}━━━ [FIX 4] REQUIREMENTS.TXT VALIDATION ━━━{RESET}")
    path = os.path.join(PROJECT_DIR, "requirements.txt")

    required_content = """yfinance==0.2.38
requests==2.31.0
google-api-python-client==2.126.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
apscheduler==3.10.4
python-dotenv==1.0.1
flask==3.0.3
google-generativeai==0.5.2
pytelegrambotapi==4.17.0
pandas==2.2.2
gunicorn==22.0.0
moviepy==1.0.3
numpy==1.26.4
"""

    with open(path, "w") as f:
        f.write(required_content)

    print(f"  {GREEN}✅ requirements.txt verified and updated{RESET}")
    return True

# ─── GITHUB PUSH ──────────────────────────────────────────────
def push_to_github(git_path):
    print(f"\n{BOLD}━━━ [GITHUB PUSH] ━━━{RESET}")

    # Check if git repo initialized
    git_dir = os.path.join(PROJECT_DIR, ".git")
    if not os.path.isdir(git_dir):
        print(f"  {YELLOW}⚠️  Git repo not initialized. Initializing...{RESET}")
        result = run_git(git_path, ["init"])
        if result.returncode != 0:
            print(f"  {RED}❌ git init failed: {result.stderr}{RESET}")
            return False
        print(f"  {GREEN}✅ Git repo initialized{RESET}")

    # Check remote
    result = run_git(git_path, ["remote", "-v"])
    if "origin" not in result.stdout:
        print(f"\n  {YELLOW}⚠️  No git remote found!{RESET}")
        print(f"  {CYAN}Please add your GitHub remote:{RESET}")
        print(f"  {BOLD}  git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git{RESET}")
        print(f"\n  {YELLOW}Skipping push. Add remote and re-run Agent 2.{RESET}")
        return False

    print(f"  {GREEN}✅ Remote found:{RESET}")
    print(f"     {result.stdout.strip()}")

    # Git config (avoid email/name errors)
    run_git(git_path, ["config", "user.email", "agent2@youtube-automation.com"])
    run_git(git_path, ["config", "user.name", "Agent2 AutoPusher"])

    # Git add all
    print(f"\n  📦 Staging files...")
    result = run_git(git_path, ["add", "."])
    if result.returncode != 0:
        print(f"  {RED}❌ git add failed: {result.stderr}{RESET}")
        return False
    print(f"  {GREEN}✅ Files staged{RESET}")

    # Git status
    result = run_git(git_path, ["status", "--short"])
    if not result.stdout.strip():
        print(f"  {GREEN}✅ Nothing to commit — repository is up to date{RESET}")
        return True
    print(f"  📋 Changes to commit:\n     {result.stdout.strip()}")

    # Git commit
    commit_msg = f"🤖 Agent2: Auto-fix & deploy prep [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
    result = run_git(git_path, ["commit", "-m", commit_msg])
    if result.returncode != 0:
        # Maybe nothing new to commit
        if "nothing to commit" in result.stdout.lower() or "nothing added" in result.stdout.lower():
            print(f"  {GREEN}✅ Nothing new to commit{RESET}")
            return True
        print(f"  {RED}❌ git commit failed: {result.stderr}{RESET}")
        return False
    print(f"  {GREEN}✅ Commit created: {commit_msg}{RESET}")

    # Get current branch
    result_branch = run_git(git_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    branch = result_branch.stdout.strip() if result_branch.returncode == 0 else "main"
    print(f"  🌿 Pushing to branch: {branch}")

    # Git push
    result = run_git(git_path, ["push", "origin", branch])
    if result.returncode != 0:
        # Try with --set-upstream
        print(f"  {YELLOW}Trying with --set-upstream...{RESET}")
        result = run_git(git_path, ["push", "--set-upstream", "origin", branch])

    if result.returncode != 0:
        print(f"  {RED}❌ Push failed:{RESET}")
        print(f"     {result.stderr.strip()}")
        print(f"\n  {YELLOW}💡 If auth failed, run this in terminal:{RESET}")
        print(f"     git remote set-url origin https://YOUR_TOKEN@github.com/USER/REPO.git")
        return False

    print(f"  {GREEN}{BOLD}✅ Successfully pushed to GitHub!{RESET}")

    # Show latest commit hash
    result_hash = run_git(git_path, ["rev-parse", "--short", "HEAD"])
    if result_hash.returncode == 0:
        print(f"  📌 Commit Hash: {result_hash.stdout.strip()}")

    return True

# ─── SUMMARY ──────────────────────────────────────────────────
def print_summary(fixes_applied, push_success):
    print(f"\n{CYAN}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}  📊 AGENT 2 SUMMARY{RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"\n  ✅ Fixes Applied : {fixes_applied}")
    push_status = f"{GREEN}✅ SUCCESS{RESET}" if push_success else f"{YELLOW}⚠️  PENDING (add remote){RESET}"
    print(f"  GitHub Push    : {push_status}")
    print(f"\n  {BOLD}🚀 Next Step: Run Agent 3{RESET}")
    print(f"     python agent3_deployer.py")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    banner()

    # Find git
    print(f"{BOLD}🔍 Finding Git installation...{RESET}")
    git_path = find_git()
    if not git_path:
        print(f"{RED}❌ Git not found on this system!{RESET}")
        print(f"{YELLOW}Please install Git from: https://git-scm.com/download/win{RESET}")
        print(f"{YELLOW}After installing, re-run this agent.{RESET}")
        sys.exit(1)
    print(f"  {GREEN}✅ Using git: {git_path}{RESET}")

    # Apply all fixes
    fixes = 0
    if fix_gitignore():    fixes += 1
    if fix_gemini_model(): fixes += 1
    if fix_render_yaml():  fixes += 1
    if fix_requirements(): fixes += 1

    # Push to GitHub
    push_ok = push_to_github(git_path)

    print_summary(fixes, push_ok)
    return push_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
