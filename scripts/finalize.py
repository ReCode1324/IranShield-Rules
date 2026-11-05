#!/usr/bin/env python3
"""Check compiled artifacts and update manifest hashes after external compilers."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
manifest_file = root / "manifest.json"
manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
for path in sorted((root / "sing-box").glob("*.json")):
    srs = path.with_suffix(".srs")
    if not srs.is_file() or srs.stat().st_size < 8:
        raise SystemExit(f"Missing or invalid compiled SRS: {srs}")
manifest["sha256"] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(root.rglob("*")) if p.is_file() and p != manifest_file}
manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Verified and hashed {len(manifest['sha256'])} generated assets")
