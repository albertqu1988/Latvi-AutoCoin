#!/usr/bin/env python3
"""
latvi.space Auto Coin
直连 latvi (无需代理) → SOCKS5 走 linkvertise API
"""
import time, re, json, os, requests
from datetime import datetime, timezone

BASE = "https://dash.latvi.space"
EMAIL = os.environ.get("LATVI_EMAIL", "btpp03@gmail.com")
PASSWORD = os.environ.get("LATVI_PASSWORD", "Hlm@0649")
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "20"))
PROXY_URL = os.environ.get("PROXY_URL", "socks5://127.0.0.1:1080")

sess = requests.Session()
proxy_dict = {"http": PROXY_URL, "https": PROXY_URL}

def log(m): print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {m}", flush=True)

def direct_get(path, **kw):
    # 先直连，超时则走代理
    try:
        return sess.get(f"{BASE}{path}", timeout=10, **kw)
    except:
        return sess.get(f"{BASE}{path}", timeout=15, proxies=proxy_dict, **kw)

def proxy_get(url, **kw):
    return sess.get(url, proxies=proxy_dict, timeout=20, **kw)

def check_proxy():
    try:
        r = requests.get("https://api.ipify.org", proxies=proxy_dict, timeout=10)
        ip = r.text.strip()
        log(f"✅ Proxy IP: {ip}")
        return ip
    except Exception as e:
        log(f"❌ Proxy: {e}")
        return None

def login():
    """Direct login (latvi has no CF)"""
    r = direct_get("/login")
    m = re.search(r'name="_token"[^>]*value="([^"]*)"', r.text)
    token = m.group(1) if m else None
    
    data = {"email": EMAIL, "password": PASSWORD}
    if token:
        data["_token"] = token
    r2 = sess.post(f"{BASE}/login", data=data, timeout=15)
    
    if "/home" in r2.url or "logout" in r2.text.lower():
        log("✅ login")
        return True
    log(f"❌ login: {r2.status_code}")
    return False

def balance():
    r = direct_get("/home")
    m = re.search(r'([\d.]+)\s*(?:credit|coin)', r.text, re.I)
    return float(m.group(1)) if m else 0.0

def cooldown():
    r = direct_get("/linkvertise")
    m = re.search(r'Claims Today:\s*(\d+)\s*/\s*(\d+)', r.text)
    if m:
        rem = int(m.group(2)) - int(m.group(1))
        log(f"{m.group(1)}/{m.group(2)} ({rem} left)")
        return rem
    return MAX_CLAIMS

def get_campaign():
    """Get linkvertise campaign + verify URL from latvi /linkvertise/generate"""
    r = direct_get("/linkvertise/generate")
    
    # Extract link-to.net or linkvertise URL
    m = re.search(r'(?:link-to\.net|linkvertise\.com)/(\d+)', r.text)
    cid = m.group(1) if m else None
    
    # Extract verify URL from base64 r= parameter
    verify_url = None
    m2 = re.search(r'r=([A-Za-z0-9+/=]+)', r.text)
    if m2:
        import base64
        try:
            decoded = base64.b64decode(m2.group(1)).decode()
            if decoded.startswith("http"):
                verify_url = decoded
        except:
            pass
    
    # Fallback: look for verify URL in href
    if not verify_url:
        m3 = re.search(r'href="(https?://[^"]*linkvertise/verify[^"]*)"', r.text)
        if m3:
            verify_url = m3.group(1)
    
    if cid:
        log(f"campaign: {cid}, verify: {verify_url[:60] if verify_url else 'none'}...")
    
    return cid, verify_url

def earn(cid, verify_url):
    """Try linkvertise API through proxy, fallback to direct verify"""
    
    # If we already have the verify URL, just hit it directly
    if verify_url:
        log(f"direct verify: {verify_url[:60]}...")
        try:
            rv = direct_get(verify_url.replace(BASE, ""))
            log(f"verify [{rv.status_code}] ✅")
            return True
        except:
            try:
                rv = sess.get(verify_url, timeout=15)
                log(f"verify (full) [{rv.status_code}] ✅")
                return True
            except Exception as e:
                log(f"verify failed: {str(e)[:60]}")
    
    # Fallback: linkvertise API through proxy
    api_url = f"https://linkvertise.com/api/v1/getContent?campaign={cid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://linkvertise.com/",
    }
    
    for attempt in range(3):
        try:
            rapi = proxy_get(api_url, headers=headers)
            log(f"getContent [{rapi.status_code}]: {rapi.text[:150]}")
            
            if rapi.status_code != 200:
                time.sleep(5)
                continue
            
            try:
                data = rapi.json()
            except:
                log(f"  not JSON, retry...")
                time.sleep(5)
                continue
            
            tasks = data.get("data", {}).get("tasks", [])
            
            has_wait = any(t.get("type") == "WaitTask" for t in tasks)
            if has_wait:
                log("WaitTask, waiting 14s...")
                time.sleep(14)
                rapi2 = proxy_get(api_url, headers=headers)
                try:
                    data = rapi2.json()
                except:
                    time.sleep(5)
                    continue
            
            has_ad = any(t.get("type") == "AdTask" for t in tasks)
            if has_ad:
                log("AdTask, waiting 10s...")
                time.sleep(10)
                rapi3 = proxy_get(api_url, headers=headers)
                try:
                    data = rapi3.json()
                except:
                    pass
            
            target = data.get("data", {}).get("link", "")
            if not target:
                target = data.get("data", {}).get("DetailPageTargetData", {}).get("link", "")
            
            if target:
                log(f"API verify: {target[:60]}...")
                if target.startswith("/"):
                    rv = direct_get(target)
                elif BASE in target:
                    rv = direct_get(target.replace(BASE, ""))
                else:
                    rv = direct_get(target)
                log(f"verify [{rv.status_code}] ✅")
                return True
            else:
                log("  no verify URL in API response")
                
        except Exception as e:
            log(f"  attempt {attempt+1}: {str(e)[:60]}")
            time.sleep(5)
    
    return False

def main():
    log("🚀 latvi (direct + sing-box proxy)")
    
    ip = check_proxy()
    if not ip:
        log("❌ proxy failed, exiting")
        return
    
    if not login():
        log("❌ login failed, exiting")
        return
    
    b0 = balance()
    log(f"balance: {b0}")
    
    rem = cooldown()
    if rem <= 0:
        log("no claims left today")
        return
    
    ok = 0
    for i in range(min(rem, MAX_CLAIMS)):
        log(f"--- #{i+1} ---")
        cid, verify_url = get_campaign()
        if not cid:
            log("❌ no campaign found")
            break
        
        if earn(cid, verify_url):
            ok += 1
        else:
            log("❌ earn failed, try next")
        time.sleep(3)
    
    b1 = balance()
    log(f"done: {ok} ok, {b0}→{b1} (+{b1-b0})")

if __name__ == "__main__":
    main()
