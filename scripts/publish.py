#!/usr/bin/env python3
"""Validate compiled SRS binaries, then publish all four identical NekoBox indexes.

Unlike a workflow-embedded heredoc, this script can be tested in isolation and
is used unchanged in GitHub Actions. Refuse to publish dangling/invalid URLs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

from catalog import ALIASES, make_index

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATHS = (
    'srslist.json',
    'nekobox/srslist.json',
    'dist/srslist.json',
    'dist/nekobox/srslist.json',
)


def publish(out: Path, repository: str, branch: str, root: Path | None = None) -> dict[str, str]:
    """Generate index only if every referenced binary was successfully compiled."""
    root = root or ROOT
    out = out.resolve()
    index = make_index(repository, branch)
    binary_dir = out / 'sing-box'
    for name in sorted(set(ALIASES.values())):
        file = binary_dir / f'{name}.srs'
        if not file.is_file() or file.stat().st_size < 9:
            raise RuntimeError(f'Missing/empty compiled SRS: {file}')
        with file.open('rb') as stream:
            if stream.read(3) != b'SRS':
                raise RuntimeError(f'Invalid SRS magic header: {file}')
    # Make sure the original source lists and compiled lists agree.
    for name in sorted(set(ALIASES.values())):
        source = binary_dir / f'{name}.json'
        if not source.is_file():
            raise RuntimeError(f'Missing source JSON for {name}: {source}')
        payload = json.loads(source.read_text(encoding='utf-8'))
        if not isinstance(payload, dict) or not isinstance(payload.get('rules'), list) or not payload['rules']:
            raise RuntimeError(f'Invalid/empty source JSON: {source}')

    files = [root / 'srslist.json', root / 'nekobox/srslist.json',
             out / 'srslist.json', out / 'nekobox/srslist.json']
    text = json.dumps(index, indent=2, ensure_ascii=False) + '\n'
    # Only write AFTER all validations have completed.
    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix='.srslist-', suffix='.tmp', dir=str(file.parent))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as temp:
                temp.write(text)
            os.replace(temp_name, file)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    print(f'Published {len(index)} NekoBox names -> {len(set(ALIASES.values()))} compiled SRS files')
    for file in files:
        print(f'  {file}')
    return index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', ''))
    parser.add_argument('--branch', default=os.environ.get('GITHUB_REF_NAME', 'main'))
    args = parser.parse_args()
    if not args.repository:
        parser.error('GITHUB_REPOSITORY or --repository is required')
    try:
        publish(args.out, args.repository, args.branch)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        parser.exit(1, f'ERROR: {error}\n')


if __name__ == '__main__':
    main()
