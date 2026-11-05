#!/usr/bin/env python3
"""Discover actively maintained public adblock repos for HUMAN review only.

Never automatically execute or import GitHub-search results as data: unknown licensing,
malicious rules and wrong source formats can disrupt users' connectivity.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/discovered-sources.json")
    since = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
    queries = [f"topic:adblock stars:>=40 pushed:>={since} archived:false",
               f"topic:iran topic:adblock pushed:>={since} archived:false"]
    seen = {}
    errors = []
    for q in queries:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": q, "sort": "updated", "order": "desc", "per_page": 30})
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "IranShieldRules-discovery"}
        if os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=40) as response:
                result = json.load(response)
            for item in result.get("items", []):
                full = item.get("full_name")
                license_ = (item.get("license") or {}).get("spdx_id")
                if full and license_ and license_ != "NOASSERTION":
                    seen[full] = {"repo": full, "homepage": item.get("html_url"),
                                  "stars": item.get("stargazers_count"), "pushed_at": item.get("pushed_at"),
                                  "license": license_, "review_required": True}
        except Exception as exc:
            errors.append(str(exc)[:200])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"scanned_at": datetime.now(timezone.utc).isoformat(),
                                "queries": queries, "candidates": sorted(seen.values(), key=lambda x: -(x["stars"] or 0)),
                                "errors": errors, "important": "Candidate listing only; automatic importing is disabled until a human checks rules, parser and license."},
                               indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Discovered {len(seen)} candidate repos ({len(errors)} errors)")


if __name__ == "__main__":
    main()
