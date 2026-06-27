#!/usr/bin/env python3
"""Schema v6 - try linkByIdentifier + getContent with fragments"""
import requests, json

LV = "https://publisher.linkvertise.com/graphql"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://linkvertise.com",
    "Referer": "https://linkvertise.com",
    "Content-Type": "application/json",
}

# Try linkByIdentifier first
q1 = """query {
  linkByIdentifier(linkIdentificationInput: {userIdAndUrl: {user_id: "1151676", url: "262"}}) {
    __typename
    id
  }
}"""

# Try getContent with inline fragments
q2 = """query {
  getContent(input: {userIdAndUrl: {user_id: "1151676", url: "262"}}, origin: "sharing") {
    __typename
    ... on ContentAccessTaskSet {
      tasks {
        __typename
      }
    }
    ... on DetailPageTargetData {
      type
      url
      paste
    }
  }
}"""

# Try with userIdAndHash
q3 = """query {
  getContent(input: {userIdAndUrl: {user_id: "1151676", url: "dynamic"}}, origin: "sharing") {
    __typename
    ... on ContentAccessTaskSet { tasks { __typename } }
    ... on DetailPageTargetData { url }
  }
}"""

# Try different user_id formats
q4 = """query {
  c1: getContent(input: {userIdAndUrl: {user_id: "1151676", url: "262"}}, origin: "sharing") { __typename }
}"""

for i, q in enumerate([q1, q2, q3, q4], 1):
    r = requests.post(LV, json={"query": q}, headers=H, timeout=15)
    try:
        d = r.json()
        print(f"\n=== q{i} ({r.status_code}) ===")
        print(json.dumps(d, indent=2)[:800])
    except:
        print(f"\n=== q{i} ({r.status_code}) ===")
        print(r.text[:300])
