#!/usr/bin/env python3
"""latvi.space Auto Coin — pure requests + proxy"""
import re, os, sys, json, time, base64, requests, urllib.parse
from datetime import datetime

BASE = "https://dash.latvi.space"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
EMAIL = os.environ.get("LATVI_EMAIL", "btpp03@gmail.com")
PASSWORD = os.environ.get("LATVI_PASSWORD", "Hlm@0649")
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "20"))
COOLDOWN_SEC = int(os.environ.get("COOLDOWN_SEC", "30"))
PROXY = os.environ.get("PROXY", "")  # socks5:// or http://

sess = requests.Session()
sess.headers.update({"User-Agent": UA})

if PROXY:
    if PROXY.startswith("socks5"):
        # Add a gap before @ to avoid parsing issues
        sess.proxies = {"http": PROXY, "https": PROXY}
    else:
        sess.proxies = {"http": PROXY, "https": PROXY}
    log(f"[proxy] {PROXY}")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ─── auth ─────────────────────────────────────────
def login():
    r = sess.get(f"{BASE}/login")
    m = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("No CSRF token")
    r2 = sess.post(f"{BASE}/login", data={
        "_token": m.group(1), "email": EMAIL, "password": PASSWORD, "remember": "on"
    }, allow_redirects=False)
    if "/home" not in (r2.headers.get("Location", "")):
        raise RuntimeError(f"Login failed -> {r2.headers.get('Location','?')}")
    # Follow redirect to finalize session
    sess.get(f"{BASE}/home")
    log("login OK")

# ─── daily reward ─────────────────────────────────
def daily():
    r = sess.get(f"{BASE}/daily-rewards")
    m = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
    token = m.group(1) if m else ""
    r2 = sess.post(f"{BASE}/daily-rewards/claim", data={"_token": token},
                    headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    try:
        d = r2.json()
        if d.get("success"):
            log(f"daily ✅  {d.get('message','')}  streak={d.get('new_streak')}  bal={d.get('new_balance')}")
            return True
    except:
        pass
    if "already" in r2.text.lower():
        log("daily ⏰  already claimed")
        return True
    log(f"daily ❌  {r2.text[:80]}")
    return False

# ─── cooldown ─────────────────────────────────────
def cooldown():
    r = sess.get(f"{BASE}/linkvertise")
    m = re.search(r'Claims Today:\s*(\d+)\s*/\s*(\d+)', r.text)
    if m:
        done, max_ = int(m.group(1)), int(m.group(2))
        rem = max_ - done
        log(f"progress  {done}/{max_}  ({rem} left)")
        return rem
    log("progress  ?/? (check raw)")
    return MAX_CLAIMS

# ─── generate ─────────────────────────────────────
def generate():
    r = sess.get(f"{BASE}/linkvertise/generate")
    m = re.search(r'https://link-to\.net[^"\']*', r.text)
    if not m:
        if "limit" in r.text.lower() or "already" in r.text.lower():
            return "LIMIT", None
        log(f"gen no link: {r.text[:100]}")
        return None, None
    link_url = m.group(0).replace("';", "")
    # decode the verify URL from b64
    rm = re.search(r'[?&]r=([^&\s]+)', link_url)
    if rm:
        rp = urllib.parse.unquote(rm.group(1)).replace("-","+").replace("_","/")
        pad = (4 - len(rp) % 4) % 4
        try:
            vu = base64.b64decode(rp + "=" * pad).decode()
            return link_url, vu
        except:
            pass
    return link_url, None

# ─── earn ─────────────────────────────────────────
def earn(link_url, verify_url):
    """Visit link-url → follow redirects → verify = earn credits"""
    # Step 1: visit link-to.net, follow redirect (allow_redirects=True)
    # This goes through proxy → linkvertise → back to latvi.space
    try:
        hdrs = {"Referer": f"{BASE}/linkvertise/generate"}
        r = sess.get(link_url, headers=hdrs, allow_redirects=True, timeout=30)
        final = r.url
        log(f"follow: {final[:70]}...")

        if verify_url and not final.startswith(verify_url):
            # Didn't land on verify naturally, try direct verify visit
            hdrs2 = {"Referer": "https://linkvertise.com/"}
            r2 = sess.get(verify_url, headers=hdrs2, allow_redirects=True, timeout=15)
            if r2.status_code == 403:
                log(f"verify 403 ❌")
                return False
            if r2.status_code == 200:
                # Check for success message
                if "success" in r2.text.lower():
                    log(f"verify OK ✅")
                    return True
        elif final.startswith(verify_url):
            log(f"verify OK ✅")
            return True
        elif "linkvertise" in r.url:
            log(f"stuck on linkvertise (proxy blocked?)")
            return False
        else:
            log(f"unknown final url, trying direct verify")
            r3 = sess.get(verify_url, allow_redirects=True, timeout=15)
            if r3.status_code == 200:
                log(f"verify OK ✅")
                return True
            return False
    except Exception as e:
        log(f"earn error: {e}")
        return False

# ─── balance ──────────────────────────────────────
def balance():
    r = sess.get(f"{BASE}/home")
    m = re.search(r'([\d.]+)\s*(?:credit|coin)', r.text, re.I)
    return float(m.group(1)) if m else 0.0

# ─── main ─────────────────────────────────────────
def main():
    log("🚀 Latvi.space Auto Coin")
    login()

    daily()

    rem = cooldown()
    if rem <= 0:
        log("🎉 Done for today")
        return

    b0 = balance()
    log(f"balance  {b0}")

    ok_cnt = 0
    for i in range(min(rem, MAX_CLAIMS)):
        log(f"--- #{i+1}/{rem} ---")
        link_url, verify_url = generate()
        if link_url == "LIMIT" or link_url is None:
            log("LIMIT reached")
            break

        if earn(link_url, verify_url):
            ok_cnt += 1
        else:
            log("earn failed, stopping")
            break

        time.sleep(COOLDOWN_SEC)

    b1 = balance()
    log(f"done  {ok_cnt} ok  {b0} → {b1}  (+{b1-b0})")

if __name__ == "__main__":
    main()
