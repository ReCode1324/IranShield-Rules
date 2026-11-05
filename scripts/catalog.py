#!/usr/bin/env python3
"""Single source of truth for NekoBox SRS aliases and canonical download URLs."""
from __future__ import annotations

import re
from urllib.parse import quote

# Keep these stable: users may have configured these tag names in NekoBox.
ALIASES: dict[str, str] = {
    "geosite-category-ads-all": "block-ads",
    "geosite-ads": "block-ads",
    "geosite-ads-ir": "block-ads-ir",
    "geosite-ads-global": "block-ads-global",
    "geosite-ir": "direct-iran-domains",
    "geoip-ir": "direct-iran-ips",
    "block-ads": "block-ads",
    "block-ads-ir": "block-ads-ir",
    "block-ads-global": "block-ads-global",
    "direct-iran-domains": "direct-iran-domains",
    "direct-iran-ips": "direct-iran-ips",
    "direct-iran-all": "direct-iran-all",
}


def make_index(repository: str, branch: str) -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be GitHub OWNER/REPO")
    if (not re.fullmatch(r"[A-Za-z0-9_.\/-]+", branch)
            or branch.startswith("/") or branch.endswith("/")
            or ".." in branch or "//" in branch):
        raise ValueError("unsafe GitHub branch name")
    # For the default branch (main), this is exactly the standard raw GitHub URL.
    root = f"https://raw.githubusercontent.com/{repository}/{quote(branch, safe='/')}/dist/sing-box/"
    return {alias: f"{root}{filename}.srs" for alias, filename in ALIASES.items()}
