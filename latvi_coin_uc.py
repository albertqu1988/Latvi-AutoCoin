#!/usr/bin/env python3
"""
latvi.space Auto Coin — Hybrid mode
SeleniumBase UC 绕过 Cloudflare 取 cookie, requests 走任务链
"""
import os, sys, time, re, json, subprocess
from datetime import datetime, timezone
from seleniumbase import Driver

BASE = "https://dash.latvi.space"
LVLINK = "https://linkvertise.com"
EMAIL = os.environ.get("LATVI_EMAIL", "btpp03@gmail.com")
PASSWORD = os.environ.get("LATVI_PASSWORD", "Hlm@0649")
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "20"))

def log(m): print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {m}", flush=True)
def ok(m): log(f"✅ {m}")
def er(m): log(f"❌ {m}")

# ─── curl helper ─────────────────────────
def curl(args, timeout=25):
    cmd = ["curl", "-s", "--connect-timeout", "20", "--max-time", str(timeout)] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+10)
        return r.stdout, r.stderr
    except Exception as e:
        return "", f"ERR:{e}"

# ─── init ────────────────────────────────
def init_driver():
    d = Driver(uc=True, headless=True, browser="chrome")
    return d

# ─── login ───────────────────────────────
def login(d):
    d.get(f"{BASE}/login")
    time.sleep(2)
    d.type('input[name="email"]', EMAIL)
    d.type('input[name="password"]', PASSWORD)
    d.click('button[type="submit"]')
    time.sleep(2)
    if "/home" in d.current_url:
        ok("login")
        return True
    er(f"login: {d.current_url}"); return False

# ─── daily reward ─────────────────────────
def daily_reward(d):
    d.get(f"{BASE}/daily-rewards")
    try:
        d.click('button:contains("Claim")')
        time.sleep(2); ok("daily claim")
    except:
        log("daily skip")

# ─── cooldown ─────────────────────────────
def cooldown(d):
    d.get(f"{BASE}/linkvertise"); time.sleep(1)
    body = d.get_page_source()
    m = re.search(r'Claims Today:\s*(\d+)\s*/\s*(\d+)', body)
    if m:
        rem = int(m.group(2)) - int(m.group(1))
        log(f"progress {m.group(1)}/{m.group(2)} ({rem} left)"); return rem
    return MAX_CLAIMS

# ─── balance ──────────────────────────────
def balance(d):
    d.get(f"{BASE}/home"); time.sleep(1)
    m = re.search(r'([\d.]+)\s*(?:credit|coin)', d.get_page_source(), re.I)
    return float(m.group(1)) if m else 0.0

# ─── gen link & pass Cloudflare via UC ────
def gen_link(d):
    d.get(f"{BASE}/linkvertise"); time.sleep(2)
    try:
        d.click('a:contains("Start Now")')
    except:
        try: d.click('button:contains("Start")')
        except: er("no start btn"); return None
    
    log("waiting for linkvertise..."); time.sleep(5)
    url = d.current_url
    if "linkvertise" not in url:
        er(f"not linkvertise: {url[:60]}"); return None
    
    # We reached linkvertise via UC browser — Cloudflare passed!
    # Now extract cookies and return the linkvertise URL
    cookies = d.get_cookies()
    lv_cookies = {c["name"]: c["value"] for c in cookies}
    d.quit()  # Close browser now, use requests for task chain
    return url, lv_cookies

# ─── linkvertise task chain via requests ──
def earn_via_chain(linkvertise_url, cookies):
    """Simulate losy's task chain with requests"""
    lv_id = re.search(r'linkvertise\.com/(\d+)', linkvertise_url)
    if not lv_id: er("no lv id"); return False
    campaign = lv_id.group(1)
    
    jar = "/tmp/lv_jar2.txt"
    # Write cookies to netscape format for curl
    open(jar, "w").close()
    for name, value in cookies.items():
        open(jar, "a+").write(f"linkvertise.com\tFALSE\t/\tTRUE\t0\t{name}\t{value}\n")
    
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    r, _ = curl(["-b", jar, "-c", jar, "-H", f"User-Agent: {ua}", linkvertise_url])
    
    # Step 1: getContent → extract task data
    r2, _ = curl(["-b", jar, "-c", jar, "-H", f"User-Agent: {ua}",
        f"https://linkvertise.com/api/v1/getContent?campaign={campaign}"])
    log(f"getContent: {r2[:100]}")
    
    # Check if we need to do tasks
    if "WaitTask" in r2:
        log("WaitTask present, need to complete chain")
        # losy just waits and then does AdTask
        # Try to find & complete tasks
        tasks = json.loads(r2)
        log(f"tasks: {json.dumps(tasks)[:200]}")
        
        # Complete WaitTask
        time.sleep(12)
        
        # Check for AdTask
        r3, _ = curl(["-b", jar, "-c", jar, "-H", f"User-Agent: {ua}",
            f"https://linkvertise.com/api/v1/getContent?campaign={campaign}"])
        log(f"getContent after wait: {r3[:100]}")
    else:
        log(f"no WaitTask, response: {r2[:100]}")
    
    er("chain not complete")
    return False

# ─── main ─────────────────────────────────
def main():
    log("🚀 latvi hybrid")
    d = init_driver()
    
    try:
        login(d)
        daily_reward(d)
        rem = cooldown(d)
        if rem <= 0: log("done for today"); return
        
        b0 = balance(d); ok(f"balance {b0}")
        
        # Use UC to get past Cloudflare once, then reuse cookies
        result = gen_link(d)
        if not result:
            er("gen_link failed"); return
        linkvertise_url, lv_cookies = result
        ok(f"Cloudflare bypassed! on {linkvertise_url[:50]}...")
        
        # Try task chain with requests
        earn_via_chain(linkvertise_url, lv_cookies)
        
    finally:
        try: d.quit()
        except: pass

if __name__ == "__main__":
    main()
