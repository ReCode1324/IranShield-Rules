#!/usr/bin/env python3
"""Install a fixed official sing-box release and verify GitHub's SHA-256 digest."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile
import urllib.request
import io

VERSION = "1.14.4"  # intentionally pinned; update manually after testing
NAME = f"sing-box-{VERSION}-linux-amd64.tar.gz"
TARGET = Path(os.environ.get("HOME", "/tmp")) / ".local/bin/sing-box"


def get(url: str, *, api=False) -> bytes:
    headers = {"User-Agent": "IranShieldRules/1.0"}
    if api and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90) as response:
        return response.read(100 * 1024 * 1024 + 1)


def main() -> None:
    release = json.loads(get(f"https://api.github.com/repos/SagerNet/sing-box/releases/tags/v{VERSION}", api=True))
    asset = next((asset for asset in release["assets"] if asset["name"] == NAME), None)
    if not asset:
        raise SystemExit(f"Missing official artifact {NAME}")
    digest = asset.get("digest", "")
    if not digest.startswith("sha256:"):
        raise SystemExit("No official SHA256 digest; refusing download")
    archive = get(asset["browser_download_url"])
    if len(archive) > 100 * 1024 * 1024:
        raise SystemExit("Oversized archive")
    actual = hashlib.sha256(archive).hexdigest()
    if actual != digest.split(":", 1)[1]:
        raise SystemExit(f"Checksum mismatch for {NAME}")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        binary = next((m for m in tar.getmembers() if m.isfile() and m.name.endswith("/sing-box")), None)
        if binary is None:
            raise SystemExit("sing-box executable absent")
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        with tar.extractfile(binary) as source, TARGET.open("wb") as output:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    TARGET.chmod(0o755)
    print(f"Verified sing-box {VERSION}: {TARGET}")


if __name__ == "__main__":
    main()
