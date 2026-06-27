#!/usr/bin/env python3
"""
latvi.space Auto Coin — 纯 requests + SOCKS5 代理 (losy 方法)
"""
import time, re, json, os, subprocess, requests
from datetime import datetime, timezone

BASE = "https://dash.latvi.space"
EMAIL = os.environ.get("LATVI_EMAIL", "btpp03@gmail.com")
PASSWORD = os.environ.get("LATVI_PASSWORD", "Hlm@0649")
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "20"))
LOCAL_PROXY = "http://127.0.0.1:8080"
PROXY_LIST = [p.strip() for p in os.environ.get("PROXY_LIST", "").split(",") if p.strip()]

sess = requests.Session()

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
        log(f"✅ GOST | IP: {ip}")
        return ip
    except Exception as e:
        log(f"❌ GOST: {e}"); return None

def latvi_get(path, **kw):
    url = f"{BASE}{path}"
    proxies = {"http": LOCAL_PROXY, "https": LOCAL_PROXY}
    return sess.get(url, proxies=proxies, timeout=20, **kw)

def latvi_post(path, data=None, **kw):
    url = f"{BASE}{path}"
    proxies = {"http": LOCAL_PROXY, "https": LOCAL_PROXY}
    return sess.post(url, data=data, proxies=proxies, timeout=20, **kw)

def login():
    r = latvi_get("/login")
    # Extract CSRF token if any
    m = re.search(r'name="_token"[^>]*value="([^"]*)"', r.text)
    token = m.group(1) if m else None
    log(f"CSRF: {'✓' if token else '✗'}")
    
    r2 = latvi_post("/login", data={
        "email": EMAIL, "password": PASSWORD,
        **(("_token", token) if token else {})
    })
    log(f"login: {r2.status_code}  {r2.url[:50]}...")
    if "/home" in r2.url:
        log("✅ login"); return True
    # Try GET after POST
    r3 = latvi_get("/home")
    if "logout" in r3.text.lower():
        log("✅ login (by cookie)");
        return True
    log(f"❌ login failed"); return False

def balance():
    r = latvi_get("/home")
    m = re.search(r'([\d.]+)\s*(?:credit|coin)', r.text, re.I)
    return float(m.group(1)) if m else 0.0

def cooldown():
    r = latvi_get("/linkvertise")
    m = re.search(r'Claims Today:\s*(\d+)\s*/\s*(\d+)', r.text)
    if m:
        rem = int(m.group(2)) - int(m.group(1))
        log(f"{m.group(1)}/{m.group(2)} ({rem} left)"); return rem
    return MAX_CLAIMS

def earn():
    """Complete one linkvertise task chain"""
    # Get linkvertise URL from latvi
    r = latvi_get("/linkvertise")
    
    # Extract campaign from redirect chain  
    m = re.search(r'linkvertise\.com/(\d+)', r.text)
    if not m:
        log("❌ no campaign"); return False
    cid = m.group(1)
    log(f"campaign: {cid}")
    
    # Try to get content via linkvertise API
    api_url = f"https://linkvertise.com/api/v1/getContent?campaign={cid}"
    
    for attempt in range(3):
        try:
            rapi = sess.get(api_url, proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=15)
            log(f"getContent ({attempt+1}): {rapi.text[:120]}")
            
            if "WaitTask" in rapi.text:
                log("WaitTask ✓")
                time.sleep(14)
                
                rapi2 = sess.get(api_url, proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=15)
                log(f"after wait: {rapi2.text[:120]}")
                
                if "DetailPageTargetData" in rapi2.text:
                    try:
                        data = json.loads(rapi2.text)
                        link = data.get("data", {}).get("link", "")
                        if link:
                            log(f"verify: {link[:60]}")
                            rv = sess.get(link, proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=15)
                            log(f"verify {rv.status_code} ✓")
                            return True
                    except: pass
                
                time.sleep(8)
                rapi3 = sess.get(api_url, proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=15)
                if "DetailPageTargetData" in rapi3.text:
                    try:
                        data = json.loads(rapi3.text)
                        link = data.get("data", {}).get("link", "")
                        if link:
                            log(f"verify: {link[:60]}")
                            sess.get(link, proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=15)
                            log("✅ credited!"); return True
                    except: pass
            
            if "DetailPageTargetData" in rapi.text or "COMPLETED" in rapi.text:
                try:
                    data = json.loads(rapi.text)
                    link = data.get("data", {}).get("link", "")
                    if link:
                        log(f"verify (immediate): {link[:60]}")
                        sess.get(link, proxies={"http": LOCAL_PROXY, "https": LOCAL_PROXY}, timeout=15)
                        log("✅ credited!"); return True
                except: pass
            
        except Exception as e:
            log(f"  attempt {attempt+1} error: {str(e)[:60]}")
            time.sleep(5)
    
    # Fallback: check latvi for success
    r2 = latvi_get("/linkvertise")
    if "success" in r2.text.lower():
        log("✅ credited!"); return True
    
    log("❌ failed"); return False

def try_proxy(proxy_url, idx, total):
    log(f"\n{'='*40}")
    log(f"代理 [{idx}/{total}]: {proxy_url[:30]}...")
    ip = start_gost(proxy_url)
    if not ip:
        return False
    
    if not login(): return None
    
    b0 = balance(); log(f"balance: {b0}")
    rem = cooldown()
    if rem <= 0: log("done"); return True
    
    ok_cnt = 0
    for i in range(min(rem, MAX_CLAIMS)):
        log(f"--- #{i+1} ---")
        if earn(): ok_cnt += 1
        else: break
        time.sleep(3)
    
    b1 = balance()
    log(f"done {ok_cnt} ok {b0}→{b1} (+{b1-b0})")
    return True

def main():
    log("🚀 latvi (pure requests)")
    if not PROXY_LIST:
        log("❌ no PROXY_LIST"); return
    log(f"共 {len(PROXY_LIST)} 个代理")
    
    for idx, proxy in enumerate(PROXY_LIST, 1):
        result = try_proxy(proxy, idx, len(PROXY_LIST))
        if result is True:
            log("✅ 完成！"); return
        elif result is False:
            log("⚠️ 换代理..."); continue
        else:
            log("⚠️ 失败，停止"); break
    log("❌ 全失败")

if __name__ == "__main__":
    main()
