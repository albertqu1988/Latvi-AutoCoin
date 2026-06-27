#!/usr/bin/env python3
"""
latvi.space Auto Coin — Pure browser mode
Everything in SeleniumBase UC: login, bypass CF on linkvertise, task interaction
"""
import os, sys, time, re
from datetime import datetime, timezone
from seleniumbase import Driver

BASE = "https://dash.latvi.space"
EMAIL = os.environ.get("LATVI_EMAIL", "btpp03@gmail.com")
PASSWORD = os.environ.get("LATVI_PASSWORD", "Hlm@0649")
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "20"))

def log(m): print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {m}", flush=True)
def ok(m): log(f"✅ {m}")
def er(m): log(f"❌ {m}")

def init_driver():
    d = Driver(uc=True, headless=True, browser="chrome")
    return d

def login(d):
    d.get(f"{BASE}/login"); time.sleep(2)
    d.type('input[name="email"]', EMAIL)
    d.type('input[name="password"]', PASSWORD)
    d.click('button[type="submit"]'); time.sleep(2)
    if "/home" in d.current_url: ok("login"); return True
    er(f"login: {d.current_url}"); return False

def daily(d):
    d.get(f"{BASE}/daily-rewards")
    try:
        d.click('button:contains("Claim")')
        time.sleep(2); ok("daily")
    except: log("daily skip")

def cooldown(d):
    d.get(f"{BASE}/linkvertise"); time.sleep(1)
    m = re.search(r'Claims Today:\s*(\d+)\s*/\s*(\d+)', d.get_page_source())
    if m:
        rem = int(m.group(2)) - int(m.group(1))
        log(f"{m.group(1)}/{m.group(2)} ({rem} left)"); return rem
    return MAX_CLAIMS

def balance(d):
    d.get(f"{BASE}/home"); time.sleep(1)
    m = re.search(r'([\d.]+)\s*(?:credit|coin)', d.get_page_source(), re.I)
    return float(m.group(1)) if m else 0.0

def earn(d):
    d.get(f"{BASE}/linkvertise"); time.sleep(2)
    try: d.click('a:contains("Start Now")')
    except:
        try: d.click('button:contains("Start")')
        except: er("no start btn"); return False
    
    log("loading linkvertise..."); time.sleep(5)
    
    # Wait for the page to load (browser follows redirect, UC passes CF)
    start = time.time()
    while time.time() - start < 30:
        time.sleep(2)
        current = d.current_url
        log(f"  url: {current[:65]}...")
        
        # Check if we returned to latvi.space with verify
        if "latvi.space" in current and "verify" in current:
            ok(f"verify reached! {current[:70]}")
            return True
        if "latvi.space" in current:
            body = d.get_page_source()
            if "success" in body.lower() or "credited" in body.lower():
                ok("credited!"); return True
        
        # Still on linkvertise - interact with the page
        if "linkvertise" in current:
            try:
                # Check for interactive elements
                btns = d.find_elements("button, a, .btn, [class*=button], [class*=btn]")
                for btn in btns:
                    txt = btn.text.lower()
                    if any(x in txt for x in ["continue", "proceed", "claim", "start", "next", "watch", "get link"]):
                        log(f"  clicking: {btn.text[:30]}")
                        btn.click(); time.sleep(2)
                        break
            except: pass
    
    log(f"  timeout, final url: {d.current_url[:60]}")
    return False

def main():
    log("🚀 latvi browser")
    d = init_driver()
    try:
        login(d)
        daily(d)
        rem = cooldown(d)
        if rem <= 0: ok("done for today"); return
        
        b0 = balance(d); ok(f"balance {b0}")
        ok_cnt = 0
        for i in range(min(rem, MAX_CLAIMS)):
            log(f"--- #{i+1} ---")
            if earn(d): ok_cnt += 1
            else: break
            time.sleep(5)
        
        b1 = balance(d)
        ok(f"done {ok_cnt} ok {b0} → {b1} (+{b1-b0})")
    finally:
        try: d.quit()
        except: pass

if __name__ == "__main__":
    main()
