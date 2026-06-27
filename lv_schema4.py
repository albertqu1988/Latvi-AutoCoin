#!/usr/bin/env python3
"""Schema v4 - find ContentAccessResponse fields"""
import requests, json

LV = "https://publisher.linkvertise.com/graphql"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://linkvertise.com",
    "Referer": "https://linkvertise.com",
    "Content-Type": "application/json",
}

queries = {
    "ContentAccessResponse": '{ __type(name: "ContentAccessResponse") { kind possibleTypes { name } } }',
    "ContentAccess": '{ __type(name: "ContentAccess") { fields { name type { name kind ofType { name kind } } } } }',
    "ContentTask": '{ __type(name: "ContentTask") { fields { name type { name kind ofType { name kind } } } } }',
    "ContentResult": '{ __type(name: "ContentResult") { fields { name type { name kind ofType { name kind } } } } }',
    "UrlByUserIdAndUrl": '{ __type(name: "PublicLinkIdentificationByUserIdAndUrlInput") { inputFields { name type { name kind ofType { name kind } } } } }',
    "tryGetContent": """{ getContent(input: {userIdAndUrl: {user_id: "1151676", url: "782"}}, origin: "sharing") { __typename } }""",
}

for name, q in queries.items():
    r = requests.post(LV, json={"query": q}, headers=H, timeout=15)
    try:
        d = r.json()
        print(f"\n=== {name} ({r.status_code}) ===")
        print(json.dumps(d, indent=2)[:1200])
    except:
        print(f"\n=== {name} ({r.status_code}) ===")
        print(r.text[:500])
