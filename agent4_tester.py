"""
╔══════════════════════════════════════════════════════════════╗
║           🧪 AGENT 4 — LIVE TESTER                          ║
║   Live deployed URL pe comprehensive tests chalata hai      ║
║   Har endpoint verify karta hai, report generate karta hai  ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python agent4_tester.py
    python agent4_tester.py https://your-service.onrender.com
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# ANSI Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# Default URL (override from arg or .env)
DEFAULT_URL = os.getenv("RENDER_SERVICE_URL", "").rstrip("/")

def banner(base_url):
    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║              🧪 AGENT 4 — LIVE TESTER                       ║
║           YouTube Automation System v1.0                     ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
📅 Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 Base URL: {CYAN}{base_url}{RESET}
""")

# ─── TEST RUNNER ──────────────────────────────────────────────
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []

    def add(self, name, passed, detail="", response_time=None, warning=False):
        status = "PASS" if passed else ("WARN" if warning else "FAIL")
        self.tests.append({
            "name": name,
            "status": status,
            "detail": detail,
            "response_time_ms": response_time
        })
        if passed:
            self.passed += 1
        elif warning:
            self.warnings += 1
        else:
            self.failed += 1

        rt_str = f"  {YELLOW}({response_time}ms){RESET}" if response_time else ""
        if passed:
            print(f"    {GREEN}✅ PASS{RESET}  {name}{rt_str}")
        elif warning:
            print(f"    {YELLOW}⚠️  WARN{RESET}  {name}{rt_str}")
        else:
            print(f"    {RED}❌ FAIL{RESET}  {name}{rt_str}")
        if detail:
            print(f"           {YELLOW}↳ {detail}{RESET}")

def make_request(url, method="GET", timeout=20):
    """HTTP request karta hai aur response time measure karta hai."""
    start = time.time()
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, timeout=timeout)

        elapsed_ms = int((time.time() - start) * 1000)
        return response, elapsed_ms, None
    except requests.exceptions.ConnectionError as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return None, elapsed_ms, f"Connection refused — is the service running?"
    except requests.exceptions.Timeout:
        elapsed_ms = int((time.time() - start) * 1000)
        return None, elapsed_ms, f"Request timed out after {timeout}s"
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return None, elapsed_ms, str(e)

# ─── TEST SUITE ───────────────────────────────────────────────

def test_homepage(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 1] HOMEPAGE ━━━{RESET}")
    url = f"{base_url}/"
    response, rt, error = make_request(url)

    if error:
        results.add("Homepage reachable", False, error, rt)
        return

    results.add("Homepage reachable", response.status_code == 200,
                f"Status: {response.status_code}", rt)

    if response.status_code == 200:
        body = response.text
        results.add("Homepage has content", len(body) > 5,
                    f"Response: {body[:100]}", rt)


def test_health_endpoint(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 2] HEALTH ENDPOINT ━━━{RESET}")
    url = f"{base_url}/health"
    response, rt, error = make_request(url)

    if error:
        results.add("GET /health reachable", False, error, rt)
        return

    results.add("GET /health status 200", response.status_code == 200,
                f"Status: {response.status_code}", rt)

    # Check response time
    is_fast = rt < 5000
    results.add("Response time < 5s", is_fast,
                f"{rt}ms" if not is_fast else "", rt,
                warning=not is_fast)

    if response.status_code == 200:
        try:
            data = response.json()
            results.add("Health returns JSON", True, f"Keys: {list(data.keys())}", rt)
            results.add("'status' field present", "status" in data,
                       f"Got: {data}", rt)
            if "status" in data:
                results.add("Status is 'ok'", data["status"] == "ok",
                           f"Value: {data['status']}", rt)
        except Exception:
            results.add("Health returns JSON", False, "Response is not valid JSON", rt)


def test_trigger_stocks(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 3] TRIGGER /Stocks ━━━{RESET}")
    url = f"{base_url}/trigger/Stocks"
    response, rt, error = make_request(url)

    if error:
        results.add("GET /trigger/Stocks reachable", False, error, rt)
        return

    results.add("GET /trigger/Stocks status 200", response.status_code == 200,
                f"Status: {response.status_code}", rt)

    if response.status_code == 200:
        try:
            data = response.json()
            results.add("Returns JSON", True, f"{data}", rt)
            results.add("'status' is 'triggered'", data.get("status") == "triggered",
                       f"Got: {data.get('status')}", rt)
            results.add("'niche' is 'Stocks'", data.get("niche") == "Stocks",
                       f"Got: {data.get('niche')}", rt)
        except Exception:
            results.add("Returns JSON", False, f"Raw response: {response.text[:100]}", rt)


def test_trigger_crypto(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 4] TRIGGER /Crypto ━━━{RESET}")
    url = f"{base_url}/trigger/Crypto"
    response, rt, error = make_request(url)

    if error:
        results.add("GET /trigger/Crypto reachable", False, error, rt)
        return

    results.add("GET /trigger/Crypto status 200", response.status_code == 200,
                f"Status: {response.status_code}", rt)

    if response.status_code == 200:
        try:
            data = response.json()
            results.add("'niche' is 'Crypto'", data.get("niche") == "Crypto",
                       f"Got: {data}", rt)
        except Exception:
            results.add("Returns JSON", False, f"Raw: {response.text[:100]}", rt)


def test_trigger_forex(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 5] TRIGGER /Forex ━━━{RESET}")
    url = f"{base_url}/trigger/Forex"
    response, rt, error = make_request(url)

    if error:
        results.add("GET /trigger/Forex reachable", False, error, rt)
        return

    results.add("GET /trigger/Forex status 200", response.status_code == 200,
                f"Status: {response.status_code}", rt)

    if response.status_code == 200:
        try:
            data = response.json()
            results.add("'niche' is 'Forex'", data.get("niche") == "Forex",
                       f"Got: {data}", rt)
        except Exception:
            results.add("Returns JSON", False, f"Raw: {response.text[:100]}", rt)


def test_invalid_niche(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 6] INVALID NICHE (Error Handling) ━━━{RESET}")
    url = f"{base_url}/trigger/InvalidNiche"
    response, rt, error = make_request(url)

    if error:
        results.add("Invalid niche returns error", False, error, rt)
        return

    results.add("Invalid niche returns 400", response.status_code == 400,
                f"Got: {response.status_code} (expected 400)", rt)


def test_response_times(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 7] PERFORMANCE CHECK ━━━{RESET}")
    endpoints = ["/", "/health"]
    times = []

    for ep in endpoints:
        _, rt, _ = make_request(f"{base_url}{ep}")
        times.append(rt)

    avg_rt = int(sum(times) / len(times)) if times else 0
    results.add(f"Average response time < 3s", avg_rt < 3000,
                f"Average: {avg_rt}ms", avg_rt,
                warning=(3000 <= avg_rt < 8000))


def test_ssl(base_url, results):
    print(f"\n{BOLD}━━━ [TEST 8] SSL / HTTPS CHECK ━━━{RESET}")
    is_https = base_url.startswith("https://")
    results.add("Using HTTPS", is_https,
                "" if is_https else "Use https:// URL for production")


# ─── SAVE REPORT ──────────────────────────────────────────────
def save_report(results, base_url):
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "summary": {
            "total": results.passed + results.failed + results.warnings,
            "passed": results.passed,
            "failed": results.failed,
            "warnings": results.warnings,
        },
        "tests": results.tests
    }
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  {GREEN}📄 Test report saved: {report_path}{RESET}")
    return report

# ─── FINAL SUMMARY ────────────────────────────────────────────
def print_final_summary(results, base_url):
    total = results.passed + results.failed + results.warnings
    pass_rate = int((results.passed / total) * 100) if total > 0 else 0

    print(f"\n{CYAN}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}  📊 AGENT 4 — FINAL TEST REPORT{RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"\n  🌐 Tested URL  : {CYAN}{base_url}{RESET}")
    print(f"  📋 Total Tests : {total}")
    print(f"  {GREEN}✅ Passed       : {results.passed}{RESET}")
    print(f"  {YELLOW}⚠️  Warnings    : {results.warnings}{RESET}")
    print(f"  {RED}❌ Failed       : {results.failed}{RESET}")
    print(f"\n  📈 Pass Rate   : ", end="")

    if pass_rate >= 90:
        print(f"{GREEN}{BOLD}{pass_rate}% — EXCELLENT! 🚀{RESET}")
    elif pass_rate >= 70:
        print(f"{YELLOW}{BOLD}{pass_rate}% — GOOD (minor issues){RESET}")
    else:
        print(f"{RED}{BOLD}{pass_rate}% — NEEDS FIXES ⚠️{RESET}")

    if results.failed == 0:
        print(f"\n  {GREEN}{BOLD}🎉 ALL TESTS PASSED! Your YouTube Automation is LIVE!{RESET}")
        print(f"\n  💡 Useful Commands:")
        print(f"     curl {base_url}/health")
        print(f"     curl {base_url}/trigger/Stocks")
        print(f"     curl {base_url}/trigger/Crypto")
        print(f"     curl {base_url}/trigger/Forex")
    else:
        print(f"\n  {YELLOW}⚠️  {results.failed} test(s) failed. Check Render logs.{RESET}")

    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    # Get base URL
    base_url = DEFAULT_URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip("/")

    if not base_url:
        print(f"\n{RED}❌ No URL provided!{RESET}")
        print(f"{YELLOW}Usage: python agent4_tester.py https://your-service.onrender.com{RESET}")
        print(f"{YELLOW}OR set RENDER_SERVICE_URL in your .env file{RESET}")
        sys.exit(1)

    banner(base_url)

    results = TestResults()

    # Run all test suites
    test_ssl(base_url, results)
    test_homepage(base_url, results)
    test_health_endpoint(base_url, results)
    test_trigger_stocks(base_url, results)
    test_trigger_crypto(base_url, results)
    test_trigger_forex(base_url, results)
    test_invalid_niche(base_url, results)
    test_response_times(base_url, results)

    # Save & show report
    save_report(results, base_url)
    print_final_summary(results, base_url)

    # Exit code: 0 if all pass, 1 if any fail
    return results.failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
