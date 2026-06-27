#!/usr/bin/env python3
"""Quick schema introspection for linkvertise GraphQL"""
import requests, json

LV = "https://publisher.linkvertise.com/graphql"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://linkvertise.com",
    "Referer": "https://linkvertise.com",
    "Content-Type": "application/json",
}

# Introspect all query fields
q = """{
  __schema {
    queryType { fields { name args { name type { name kind ofType { name kind } } } } }
    mutationType { fields { name args { name type { name kind ofType { name kind } } } } }
  }
}"""

r = requests.post(LV, json={"query": q}, headers=H, timeout=15)
print(f"Status: {r.status_code}")
try:
    d = r.json()
    print(json.dumps(d, indent=2)[:3000])
except:
    print(r.text[:1000])
