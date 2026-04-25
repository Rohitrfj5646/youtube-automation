"""
╔══════════════════════════════════════════════════════════════╗
║          🎛️  MASTER ORCHESTRATOR — run_all_agents.py        ║
║   Sabko sequence mein chalata hai: 1 → 2 → 3 → 4           ║
║   Ek command se poora pipeline run karo                     ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python run_all_agents.py
    python run_all_agents.py https://your-service.onrender.com
"""

import os
import sys
import time
import subprocess
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ANSI Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def master_banner():
    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          🤖 YOUTUBE AUTOMATION — MASTER ORCHESTRATOR             ║
║                                                                  ║
║    Agent 1: 🔍 Analyze → Agent 2: 🛠️ Fix+Push →                ║
║    Agent 3: 🚀 Deploy  → Agent 4: 🧪 Test                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{RESET}
📅 Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📁 Project : {PROJECT_DIR}
""")

def section(num, icon, name, agent_file):
    print(f"""
{BLUE}{BOLD}
  ┌──────────────────────────────────────────────────────────┐
  │  {icon}  AGENT {num}: {name:<44} │
  │  📄 {agent_file:<54} │
  └──────────────────────────────────────────────────────────┘
{RESET}""")

def run_agent(agent_file, extra_args=None, timeout=600):
    """Agent ko subprocess mein run karta hai."""
    script_path = os.path.join(PROJECT_DIR, agent_file)
    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)

    print(f"  ▶ Running: {' '.join(cmd)}")
    print(f"  {'─'*55}")

    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        timeout=timeout
    )
    elapsed = int(time.time() - start)

    print(f"  {'─'*55}")
    print(f"  ⏱  Completed in {elapsed}s | Exit code: {result.returncode}")

    return result.returncode == 0

def print_pipeline_summary(results):
    agents = [
        ("🔍 Agent 1 — Analyzer",         results.get("agent1")),
        ("🛠️  Agent 2 — Fix+Push",          results.get("agent2")),
        ("🚀 Agent 3 — Deployer",           results.get("agent3")),
        ("🧪 Agent 4 — Live Tester",        results.get("agent4")),
    ]

    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║         🎯 PIPELINE EXECUTION SUMMARY                 ║{RESET}")
    print(f"{CYAN}{BOLD}╚══════════════════════════════════════════════════════╝{RESET}\n")

    all_passed = True
    for name, success in agents:
        if success is None:
            status = f"{YELLOW}⚠️  SKIPPED{RESET}"
        elif success:
            status = f"{GREEN}✅ SUCCESS{RESET}"
        else:
            status = f"{RED}❌ FAILED{RESET}"
            all_passed = False
        print(f"  {name:<35} {status}")

    if all_passed:
        print(f"\n  {GREEN}{BOLD}🎉 ALL AGENTS COMPLETED SUCCESSFULLY!{RESET}")
        print(f"  {GREEN}Your YouTube Automation is LIVE and TESTED! 🚀{RESET}")
    else:
        print(f"\n  {YELLOW}⚠️  Some agents had issues. Check logs above.{RESET}")

    print(f"\n  📅 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{CYAN}{'━'*56}{RESET}\n")


def main():
    master_banner()

    # Get optional service URL from args
    service_url = None
    if len(sys.argv) > 1:
        service_url = sys.argv[1].rstrip("/")
        print(f"  🌐 Service URL: {CYAN}{service_url}{RESET}\n")

    results = {}

    # ─── AGENT 1: ANALYZE ─────────────────────────────────────
    section(1, "🔍", "PROJECT ANALYZER", "agent1_analyzer.py")
    try:
        ok = run_agent("agent1_analyzer.py")
        results["agent1"] = ok
    except Exception as e:
        print(f"  {RED}❌ Agent 1 crashed: {e}{RESET}")
        results["agent1"] = False

    print(f"\n  {'─'*55}")
    input(f"  {YELLOW}Press ENTER to continue to Agent 2 (Fix + GitHub Push)...{RESET}")

    # ─── AGENT 2: FIX + PUSH ──────────────────────────────────
    section(2, "🛠️ ", "CODE FIXER + GITHUB PUSHER", "agent2_github_pusher.py")
    try:
        ok = run_agent("agent2_github_pusher.py")
        results["agent2"] = ok
    except Exception as e:
        print(f"  {RED}❌ Agent 2 crashed: {e}{RESET}")
        results["agent2"] = False

    print(f"\n  {'─'*55}")
    input(f"  {YELLOW}Press ENTER to continue to Agent 3 (Deploy to Render)...{RESET}")

    # ─── AGENT 3: DEPLOY ──────────────────────────────────────
    section(3, "🚀", "RENDER DEPLOYER", "agent3_deployer.py")
    try:
        extra = [service_url] if service_url else []
        ok = run_agent("agent3_deployer.py", extra_args=extra, timeout=900)
        results["agent3"] = ok
    except Exception as e:
        print(f"  {RED}❌ Agent 3 crashed: {e}{RESET}")
        results["agent3"] = False

    # Ask for URL if not provided yet
    if not service_url:
        print(f"\n  {CYAN}Please enter your Render live URL to test:{RESET}")
        print(f"  (e.g. https://youtube-automation.onrender.com)")
        service_url = input(f"  {BOLD}URL: {RESET}").strip().rstrip("/")

    print(f"\n  {'─'*55}")
    input(f"  {YELLOW}Press ENTER to continue to Agent 4 (Live Tests)...{RESET}")

    # ─── AGENT 4: TEST ────────────────────────────────────────
    section(4, "🧪", "LIVE TESTER", "agent4_tester.py")
    try:
        extra = [service_url] if service_url else []
        ok = run_agent("agent4_tester.py", extra_args=extra)
        results["agent4"] = ok
    except Exception as e:
        print(f"  {RED}❌ Agent 4 crashed: {e}{RESET}")
        results["agent4"] = False

    # ─── FINAL SUMMARY ────────────────────────────────────────
    print_pipeline_summary(results)

    all_ok = all(v for v in results.values() if v is not None)
    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
