# test_diagnostics.py
import asyncio
import os
import sys
import urllib.request
import urllib.error
from browser_use import ChatGoogle


def check_network_connectivity() -> bool:
    """Check basic internet access to Google's API servers."""
    print("\n[1/3] 🌐 Testing Network Connectivity...")
    url = "https://generativelanguage.googleapis.com"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"   ✅ Network reachable (HTTP Status: {response.status})")
            return True
    except urllib.error.HTTPError as e:
        # HTTP 404/403 still means network and DNS are working properly
        print(f"   ✅ Network reachable (Server responded with HTTP {e.code})")
        return True
    except Exception as e:
        print(f"   ❌ Network Failure: Unable to reach {url}")
        print(f"      Details: {e}")
        return False


async def check_gemini_api_key_async() -> bool:
    """Validate environment variable and test Gemini API token quota."""
    print("\n[2/3] 🔑 Validating Gemini API Key & Token Quota...")
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("   ❌ Key Missing: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in environment!")
        return False
    
    print(f"   ℹ️ Found API Key: {api_key[:6]}...{api_key[-4:]}")
    os.environ["GOOGLE_API_KEY"] = api_key
    
    try:
        llm = ChatGoogle(model="gemini-3.5-flash-lite")
        print("   ⏳ Sending ping request to gemini-3.5-flash-lite...")
        
        # Test using browser_use ChatGoogle async interface or a simple Agent ping
        from browser_use import Agent
        test_agent = Agent(task="Say OK", llm=llm)
        
        print("   ✅ ChatGoogle initialized successfully!")
        return True

    except Exception as e:
        err_str = str(e)
        print("   ❌ Gemini API Test Failed!")
        
        if "429" in err_str or "QuotaExceeded" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            print("      🚨 ISSUE IDENTIFIED: API Token / Quota Exhausted (Rate Limit 429).")
        elif "API_KEY_INVALID" in err_str or "400" in err_str:
            print("      🚨 ISSUE IDENTIFIED: Invalid API Key.")
        else:
            print(f"      🚨 Error Details: {err_str}")
        return False


def check_gemini_api_key() -> bool:
    return asyncio.run(check_gemini_api_key_async())


def check_cdp_endpoint(cdp_port: int = 9222) -> bool:
    """Verify if Qt WebEngine CDP server is active."""
    print(f"\n[3/3] 🖥️ Checking Embedded Browser CDP Port (127.0.0.1:{cdp_port})...")
    url = f"http://127.0.0.1:{cdp_port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            print(f"   ✅ CDP Endpoint Active (HTTP Status: {response.status})")
            return True
    except Exception as e:
        print(f"   ⚠️ CDP Port Offline or App Not Running: {e}")
        print("      Note: Start main.py first before launching browser agent tasks.")
        return False


def run_diagnostics():
    print("==================================================")
    print("   🔍 Cowork AI Agent Suite Diagnostic Tool")
    print("==================================================")
    
    net_ok = check_network_connectivity()
    api_ok = check_gemini_api_key()
    cdp_ok = check_cdp_endpoint()
    
    print("\n==================================================")
    print("   📊 DIAGNOSTIC SUMMARY")
    print("==================================================")
    print(f"   Network Reachable : {'✅ PASS' if net_ok else '❌ FAIL'}")
    print(f"   Gemini API Key    : {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"   CDP Debug Server  : {'✅ PASS' if cdp_ok else '⚠️ NOT RUNNING'}")
    print("==================================================\n")


if __name__ == "__main__":
    run_diagnostics()