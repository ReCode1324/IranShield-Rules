#!/usr/bin/env python3
"""Fail closed on malformed outputs, then rebuild the SHA-256 manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from catalog import ALIASES, make_index


def finalize(root: Path) -> dict:
    root = root.resolve()
    manifest_file = root / 'manifest.json'
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    expected = make_index(manifest['repository'], manifest.get('branch', 'main'))
    srs_root = root / 'sing-box'
    for tag in sorted(set(ALIASES.values())):
        source = srs_root / (tag + '.json')
        binary = srs_root / (tag + '.srs')
        if not source.is_file() or not binary.is_file() or binary.stat().st_size < 9:
            raise ValueError(f'Missing required compiled source or binary: {tag}')
        if binary.read_bytes()[:3] != b'SRS':
            raise ValueError(f'Corrupt SRS header: {tag}')
        payload = json.loads(source.read_text(encoding='utf-8'))
        if not payload.get('rules'):
            raise ValueError(f'Empty SRS source: {tag}')
    for path in (root / 'srslist.json', root / 'nekobox/srslist.json'):
        actual = json.loads(path.read_text(encoding='utf-8'))
        if actual != expected:
            raise ValueError(f'Mismatched NekoBox mapping: {path}')
    manifest['sha256'] = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob('*')) if p.is_file() and p != manifest_file
    }
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Verified {len(set(ALIASES.values()))} SRS binaries and {len(manifest['sha256'])} files")
    return manifest


if __name__ == '__main__':
    try:
        finalize(Path(sys.argv[1] if len(sys.argv) > 1 else 'dist'))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f'ERROR: {exc}') from exc
