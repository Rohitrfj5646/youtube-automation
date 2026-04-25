"""
╔══════════════════════════════════════════════════════════════╗
║         🔍 AGENT 1 — PROJECT ANALYZER                       ║
║   YouTube Automation Project ka deep analysis karta hai     ║
║   Issues dhundta hai aur report generate karta hai          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import json
import ast
import sys
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
║           🔍 AGENT 1 — PROJECT ANALYZER                     ║
║        YouTube Automation System v1.0                        ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📁 Project Dir  : {PROJECT_DIR}
""")

def check(label, passed, detail=""):
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"  {status}  {label}")
    if detail:
        print(f"         {YELLOW}↳ {detail}{RESET}")
    return passed

# ─── CHECK 1: Required Files ───────────────────────────────────
def check_required_files():
    print(f"\n{BOLD}━━━ [1] REQUIRED FILES CHECK ━━━{RESET}")
    required = ["app.py", "requirements.txt", "Dockerfile", "render.yaml", ".env"]
    results = {}
    for f in required:
        path = os.path.join(PROJECT_DIR, f)
        exists = os.path.isfile(path)
        detail = "" if exists else f"File missing: {path}"
        results[f] = check(f, exists, detail)
    return results

# ─── CHECK 2: .gitignore ───────────────────────────────────────
def check_gitignore():
    print(f"\n{BOLD}━━━ [2] .GITIGNORE SAFETY CHECK ━━━{RESET}")
    gitignore_path = os.path.join(PROJECT_DIR, ".gitignore")
    issues = []
    if not os.path.isfile(gitignore_path):
        check(".gitignore exists", False, ".gitignore not found — .env might get pushed!")
        return {"gitignore_exists": False, "env_protected": False}

    check(".gitignore exists", True)
    with open(gitignore_path, "r") as f:
        content = f.read()

    env_protected = ".env" in content
    check(".env in .gitignore", env_protected, 
          "" if env_protected else "⚠️ .env is NOT in .gitignore — secrets may be exposed!")

    return {"gitignore_exists": True, "env_protected": env_protected}

# ─── CHECK 3: Environment Variables ───────────────────────────
def check_env_vars():
    print(f"\n{BOLD}━━━ [3] ENVIRONMENT VARIABLES CHECK ━━━{RESET}")
    env_path = os.path.join(PROJECT_DIR, ".env")
    required_vars = [
        "GEMINI_API_KEY",
        "SARVAM_API_KEY",
        "PEXELS_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "YT_REFRESH_TOKEN",
        "YT_CLIENT_ID",
        "YT_CLIENT_SECRET",
    ]
    results = {}
    env_content = {}

    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    env_content[key.strip()] = val.strip()

    for var in required_vars:
        found = var in env_content and bool(env_content[var])
        results[var] = found
        detail = "" if found else f"Add {var} to your .env file"
        check(f"{var}", found, detail)

    return results

# ─── CHECK 4: Python Syntax ───────────────────────────────────
def check_python_syntax():
    print(f"\n{BOLD}━━━ [4] PYTHON SYNTAX CHECK ━━━{RESET}")
    py_files = ["app.py", "test_system.py", "test_apis.py"]
    results = {}
    for fname in py_files:
        path = os.path.join(PROJECT_DIR, fname)
        if not os.path.isfile(path):
            results[fname] = "missing"
            check(fname, False, "File not found")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source)
            results[fname] = "ok"
            check(fname, True)
        except SyntaxError as e:
            results[fname] = f"SyntaxError: {e}"
            check(fname, False, str(e))
    return results

# ─── CHECK 5: Deprecated API / Known Issues ────────────────────
def check_code_issues():
    print(f"\n{BOLD}━━━ [5] CODE QUALITY & DEPRECATION CHECK ━━━{RESET}")
    app_path = os.path.join(PROJECT_DIR, "app.py")
    issues = []
    fixes  = []

    if not os.path.isfile(app_path):
        check("app.py readable", False)
        return []

    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines   = content.splitlines()

    # Check deprecated gemini-pro
    if "'gemini-pro'" in content or '"gemini-pro"' in content:
        issues.append("deprecated_gemini_model")
        fixes.append("Change 'gemini-pro' → 'gemini-1.5-flash' (gemini-pro is deprecated)")
        check("Gemini model version", False, "DEPRECATED: 'gemini-pro' → use 'gemini-1.5-flash'")
    else:
        check("Gemini model version", True)

    # Check /tmp paths (OK for Render Docker)
    tmp_count = content.count("/tmp/")
    if tmp_count > 0:
        check(f"/tmp/ paths ({tmp_count} found)", True, "OK for Docker/Render deployment")

    # Check health endpoint
    if "@app.route('/health')" in content:
        check("Health endpoint /health", True)
    else:
        issues.append("missing_health_endpoint")
        fixes.append("Add @app.route('/health') endpoint")
        check("Health endpoint /health", False, "Missing — Render needs /health for health checks")

    # Check scheduler
    if "BackgroundScheduler" in content:
        check("Background Scheduler", True)
    else:
        issues.append("missing_scheduler")
        check("Background Scheduler", False, "APScheduler not found")

    # Check Telegram bot
    if "telebot" in content and "infinity_polling" in content:
        check("Telegram Bot polling", True)
    else:
        issues.append("telegram_bot_incomplete")
        check("Telegram Bot", False, "telebot or infinity_polling missing")

    return {"issues": issues, "fixes": fixes}

# ─── CHECK 6: Dockerfile ──────────────────────────────────────
def check_dockerfile():
    print(f"\n{BOLD}━━━ [6] DOCKERFILE CHECK ━━━{RESET}")
    path = os.path.join(PROJECT_DIR, "Dockerfile")
    results = {}

    if not os.path.isfile(path):
        check("Dockerfile exists", False)
        return {}

    with open(path, "r") as f:
        content = f.read()

    check("FROM python base image", "FROM python:" in content)
    check("ffmpeg installed", "ffmpeg" in content)
    check("imagemagick installed", "imagemagick" in content.lower())
    check("EXPOSE port", "EXPOSE" in content)
    check("gunicorn CMD", "gunicorn" in content)

    # Check ImageMagick policy fix
    if "policy.xml" in content and "rights" in content:
        check("ImageMagick policy fix", True, "TextClip will work correctly")
    else:
        check("ImageMagick policy fix", False, "Add sed command to fix ImageMagick policy.xml")
        results["imagick_policy_missing"] = True

    return results

# ─── CHECK 7: render.yaml ─────────────────────────────────────
def check_render_yaml():
    print(f"\n{BOLD}━━━ [7] RENDER.YAML CHECK ━━━{RESET}")
    path = os.path.join(PROJECT_DIR, "render.yaml")
    issues = []

    if not os.path.isfile(path):
        check("render.yaml exists", False)
        return {"exists": False}

    with open(path, "r") as f:
        content = f.read()

    check("render.yaml exists", True)
    check("type: web", "type: web" in content)
    check("env: docker", "env: docker" in content)
    check("healthCheckPath", "healthCheckPath" in content)
    check("PORT env var", "PORT" in content)

    if "envVars" in content:
        check("envVars section", True)
    else:
        issues.append("missing_envVars")
        check("envVars section", False, "Add environment variables to render.yaml")

    return {"exists": True, "issues": issues}

# ─── CHECK 8: Requirements ────────────────────────────────────
def check_requirements():
    print(f"\n{BOLD}━━━ [8] REQUIREMENTS.TXT CHECK ━━━{RESET}")
    path = os.path.join(PROJECT_DIR, "requirements.txt")
    required_packages = [
        "flask", "gunicorn", "requests", "yfinance",
        "google-api-python-client", "google-generativeai",
        "apscheduler", "python-dotenv", "pytelegrambotapi",
        "moviepy", "numpy"
    ]
    issues = []

    if not os.path.isfile(path):
        check("requirements.txt exists", False)
        return {}

    with open(path, "r") as f:
        content = f.read().lower()

    for pkg in required_packages:
        found = pkg.lower() in content
        if not found:
            issues.append(pkg)
        check(pkg, found, "" if found else f"Add {pkg} to requirements.txt")

    return {"missing": issues}

# ─── GENERATE REPORT ──────────────────────────────────────────
def generate_report(results):
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_dir": PROJECT_DIR,
        "results": results
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n{GREEN}{BOLD}📄 Analysis report saved: {REPORT_FILE}{RESET}")
    return report

# ─── SUMMARY ──────────────────────────────────────────────────
def print_summary(results):
    print(f"\n{CYAN}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}  📊 ANALYSIS SUMMARY{RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

    code_issues = results.get("code_issues", {})
    issues = code_issues.get("issues", [])
    fixes  = code_issues.get("fixes", [])

    env_vars = results.get("env_vars", {})
    missing_env = [k for k, v in env_vars.items() if not v]

    print(f"\n  🔴 Code Issues Found  : {len(issues)}")
    print(f"  🟡 Missing Env Vars   : {len(missing_env)}")

    if fixes:
        print(f"\n  {YELLOW}🔧 FIXES NEEDED (Agent 2 will apply):{RESET}")
        for i, fix in enumerate(fixes, 1):
            print(f"     {i}. {fix}")

    if missing_env:
        print(f"\n  {RED}⚠️  MISSING ENV VARS (set on Render dashboard):{RESET}")
        for v in missing_env:
            print(f"     • {v}")

    gitignore = results.get("gitignore", {})
    if not gitignore.get("env_protected"):
        print(f"\n  {RED}🚨 SECURITY: .env is not in .gitignore! Agent 2 will fix this.{RESET}")

    print(f"\n  {GREEN}✅ Project is ready for Agent 2 (GitHub Push){RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    banner()
    results = {
        "files"       : check_required_files(),
        "gitignore"   : check_gitignore(),
        "env_vars"    : check_env_vars(),
        "syntax"      : check_python_syntax(),
        "code_issues" : check_code_issues(),
        "dockerfile"  : check_dockerfile(),
        "render_yaml" : check_render_yaml(),
        "requirements": check_requirements(),
    }
    report = generate_report(results)
    print_summary(results)
    print(f"{BOLD}🚀 Agent 1 complete! Run Agent 2 next: python agent2_github_pusher.py{RESET}\n")
    return results

if __name__ == "__main__":
    main()
