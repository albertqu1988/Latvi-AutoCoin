#!/usr/bin/env python3
"""
latvi.space Auto Coin — GOST 代理 + SeleniumBase UC 浏览器完整流程
同步自 freecloud 的成功方案 (多代理自动切换)
"""
import time, re, json, os, subprocess, requests
from datetime import datetime, timezone
from seleniumbase import Driver

BASE = "https://dash.latvi.space"
EMAIL = os.environ.get("LATVI_EMAIL", "btpp03@gmail.com")
PASSWORD = os.environ.get("LATVI_PASSWORD", "Hlm@0649")
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "20"))
LOCAL_PROXY = "http://127.0.0.1:8080"
PROXY_LIST = [p.strip() for p in os.environ.get("PROXY_LIST", "").split(",") if p.strip()]

def log(m): print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {m}", flush=True)

def start_gost(proxy_url):
    subprocess.run(["pkill", "-f", "gost"], capture_output=True)
    time.sleep(1)
    cmd = ["nohup", "./gost", "-L", f"http://:8080", "-F", proxy_url]
    with open("gost.log", "a") as f:
        subprocess.Popen(cmd, stdout=f, stderr=f)
    time.sleep(3)
    try:
        r = requests.get("https://api.ipify.org", proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=10)
        ip = r.text.strip()
        log(f"✅ GOST代理 | IP: {ip}")
        return ip
    except:
        log("❌ GOST启动失败"); return None

def balance(d):
    d.get(f"{BASE}/home"); time.sleep(1)
    m = re.search(r'([\d.]+)\s*(?:credit|coin)', d.get_page_source(), re.I)
    return float(m.group(1)) if m else 0.0

def cooldown(d):
    d.get(f"{BASE}/linkvertise"); time.sleep(1)
    m = re.search(r'Claims Today:\s*(\d+)\s*/\s*(\d+)', d.get_page_source())
    if m:
        rem = int(m.group(2)) - int(m.group(1))
        log(f"{m.group(1)}/{m.group(2)} ({rem} left)"); return rem
    return MAX_CLAIMS

def earn(d):
    # Go to linkvertise page
    d.get(f"{BASE}/linkvertise"); time.sleep(2)
    try: d.click('a:contains("Start Now")')
    except:
        try: d.click('button:contains("Start")')
        except: log("❌ no start"); return False

    time.sleep(5)
    current = d.current_url
    log(f"redirected: {current[:60]}...")
    
    if "linkvertise" not in current:
        log("❌ not on linkvertise"); return False

    # Extract campaign
    m = re.search(r'linkvertise\.com/(\d+)', current)
    if not m: log("❌ no campaign"); return False
    cid = m.group(1)
    log(f"campaign: {cid}")

    # Wait for tasks - browser handles WaitTask via JS
    # The SeleniumBase UC browser + residential proxy should bypass CF on API too
    log("waiting for task chain...")
    start = time.time()
    while time.time() - start < 110:
        time.sleep(3)
        
        # Check if redirected back
        if "latvi.space" in d.current_url:
            time.sleep(2)
            body = d.get_page_source()
            if "success" in body.lower() or "credited" in body.lower():
                log("✅ credited!"); return True
            log("back on latvi"); return True

        # Try visiting API directly (browser has proxy cookies)
        if int(time.time() - start) % 20 == 0:
            d.get(f"https://linkvertise.com/api/v1/getContent?campaign={cid}")
            time.sleep(2)
            body = d.get_page_source()
            log(f"API: {body[:100]}")
            if "DetailPageTargetData" in body:
                try:
                    data = json.loads(body)
                    link = data.get("data", {}).get("link", "")
                    if link:
                        log(f"verify: {link[:60]}")
                        d.get(link); time.sleep(3)
                        log("✅ credited!"); return True
                except: pass
            # Navigate back to linkvertise page
            d.get(current); time.sleep(2)
        
        log(f"  waiting ({int(time.time()-start)}s)")

    log(f"❌ timeout"); return False

def try_proxy(proxy_url, idx, total):
    log(f"\n{'='*40}")
    log(f"代理 [{idx}/{total}]: {proxy_url[:30]}...")
    ip = start_gost(proxy_url)
    if not ip:
        log("⚠️ 代理不可用"); return False

    d = Driver(uc=True, headless=True, proxy=LOCAL_PROXY, browser="chrome")
    try:
        # Login
        d.get(f"{BASE}/login"); time.sleep(2)
        d.type('input[name="email"]', EMAIL)
        d.type('input[name="password"]', PASSWORD)
        d.click('button[type="submit"]'); time.sleep(2)
        if "/home" not in d.current_url:
            log("❌ login failed"); return None
        log("✅ login")

        # Balance
        b0 = balance(d)
        log(f"balance: {b0}")

        # Check cooldown
        rem = cooldown(d)
        if rem <= 0:
            log("done for today"); return True

        ok_cnt = 0
        for i in range(min(rem, MAX_CLAIMS)):
            log(f"--- #{i+1} ---")
            if earn(d): ok_cnt += 1
            else: break
            time.sleep(3)

        b1 = balance(d)
        log(f"done {ok_cnt} ok {b0}→{b1} (+{b1-b0})")
        return True

    finally:
        try: d.quit(); except: pass

def main():
    log("🚀 latvi (GOST + proxy list)")
    
    if not PROXY_LIST:
        log("❌ 未配置 PROXY_LIST")
        return

    log(f"共 {len(PROXY_LIST)} 个代理")
    
    for idx, proxy in enumerate(PROXY_LIST, 1):
        result = try_proxy(proxy, idx, len(PROXY_LIST))
        if result is True:
            log(f"✅ 完成！"); return
        elif result is False:
            log(f"⚠️ 换下一个代理..."); continue
        else:
            log(f"⚠️ 操作失败，停止"); break
    
    log("❌ 所有代理都失败了")

if __name__ == "__main__":
    main()
