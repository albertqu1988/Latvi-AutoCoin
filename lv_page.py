#!/usr/bin/env python3
"""Test - access linkvertise page directly"""
import requests, json, re

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# Test: access linkvertise.com/1151676/262/dynamic page
print("=== linkvertise page ===")
r = requests.get("https://linkvertise.com/1151676/262/dynamic?r=test&o=sharing", headers=H, timeout=10)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

# Extract any useful data from the page
if r.status_code == 200:
    # Look for JSON data in script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
    for i, s in enumerate(scripts):
        if 'campaign' in s.lower() or 'task' in s.lower() or 'content' in s.lower():
            print(f"\nScript {i} (relevant):")
            print(s[:300])
    
    # Look for data attributes
    data_attrs = re.findall(r'data-(\w+)="([^"]*)"', r.text)
    for k, v in data_attrs:
        if k in ['campaign', 'user', 'post', 'url', 'token']:
            print(f"  data-{k}={v[:50]}")

    # Look for __NEXT_DATA__ or similar
    next_data = re.search(r'__NEXT_DATA__\s*=\s*({.*?})</script>', r.text)
    if next_data:
        print(f"\n__NEXT_DATA__:")
        print(next_data.group(1)[:500])
    
    # Look for window.__APOLLO_STATE__ or similar
    apollo = re.search(r'__APOLLO_STATE__\s*=\s*({.*?})</script>', r.text)
    if apollo:
        print(f"\n__APOLLO_STATE__:")
        print(apollo.group(1)[:500])
    
    # Just show part of the page
    print(f"\nPage snippet:")
    # Find the main content area
    body = re.search(r'<body[^>]*>(.*?)</body>', r.text, re.DOTALL)
    if body:
        # Remove script tags
        clean = re.sub(r'<script[^>]*>.*?</script>', '', body.group(1), flags=re.DOTALL)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        print(clean[:500])
