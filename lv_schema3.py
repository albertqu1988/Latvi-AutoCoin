#!/usr/bin/env python3
"""Deep schema introspection v3"""
import requests, json

LV = "https://publisher.linkvertise.com/graphql"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://linkvertise.com",
    "Referer": "https://linkvertise.com",
    "Content-Type": "application/json",
}

queries = {
    "PublicLinkIdentificationInput": '{ __type(name: "PublicLinkIdentificationInput") { inputFields { name type { name kind ofType { name kind } } } } }',
    "TaskArgument": '{ __type(name: "TaskArgument") { inputFields { name type { name kind ofType { name kind } } } } }',
    "getContent": '{ __type(name: "getContentPayload") { fields { name type { name kind ofType { name kind } } } } }',
    "ContentNode": '{ __type(name: "ContentNode") { fields { name type { name kind ofType { name kind } } } } }',
    "mutations": '{ __schema { mutationType { fields { name args { name type { name kind ofType { name kind } } } } } } }',
    "completePayload": '{ __type(name: "completeContentPayload") { fields { name type { name kind ofType { name kind } } } } }',
    "allTypes": '{ __type(name: "Query") { fields { name type { name kind ofType { name kind } } } } }',
}

for name, q in queries.items():
    r = requests.post(LV, json={"query": q}, headers=H, timeout=15)
    try:
        d = r.json()
        print(f"\n=== {name} ({r.status_code}) ===")
        if "data" in d:
            print(json.dumps(d["data"], indent=2)[:800])
        elif "errors" in d:
            for e in d["errors"]:
                print(f"  error: {e.get('message','')}")
    except:
        print(f"\n=== {name} ({r.status_code}) ===")
        print(r.text[:300])

# Also try calling getContent directly
print("\n=== CALL getContent ===")
q = '{ getContent(input: {userIdAndUrl: {user_id: "1151676", url: "782"}}, origin: "sharing") { access_token } }'
r = requests.post(LV, json={"query": q}, headers=H, timeout=15)
print(f"Status: {r.status_code}")
print(r.text[:500])
