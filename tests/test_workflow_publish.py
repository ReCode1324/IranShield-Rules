"""Exercise production publication code, not brittle YAML command extraction."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import build
from catalog import ALIASES, make_index
from finalize import finalize
from publish import publish

WORKFLOW = ROOT / '.github/workflows/update-rules.yml'
TAGS = sorted(set(ALIASES.values()))


def compiled_fixtures(path: Path):
    """Fake binaries with correct header for isolated publisher tests only.

    These are NOT claimed to be genuine compiled SRS files; GitHub Actions
    compiles and decompiles real binaries with the official sing-box tool.
    """
    for name in TAGS:
        (path / 'sing-box' / f'{name}.srs').write_bytes(b'SRS\x02fixture-payload')


class NekoBoxPublisherTests(unittest.TestCase):
    def test_twice_monthly_schedule(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("cron: '17 3 1,15 * *'", workflow)
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('contents: write', workflow)
        self.assertIn('python scripts/publish.py --out dist', workflow)
        self.assertIn('python -m unittest discover -s tests -v', workflow)
        self.assertIn('rule-set decompile', workflow)
        self.assertIn('git push origin', workflow)

    def test_publish_then_finalize_exact_reused_indexes(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            output = home / 'dist'
            build(output, ROOT / 'tests/fixtures', 'ReCode1324/IranShield-Rules', False)
            compiled_fixtures(output)
            # Purposely delete all previously generated indexes and their folders.
            for path in [output / 'srslist.json', output / 'nekobox/srslist.json']:
                path.unlink()
            (output / 'nekobox').rmdir()
            index = publish(output, 'ReCode1324/IranShield-Rules', 'main', root=home)
            expected = make_index('ReCode1324/IranShield-Rules', 'main')
            self.assertEqual(index, expected)
            self.assertEqual(len(index), 12)
            self.assertEqual(len(set(ALIASES.values())), 6)
            paths = [home / x for x in (
                'srslist.json', 'nekobox/srslist.json',
                'dist/srslist.json', 'dist/nekobox/srslist.json',
            )]
            self.assertEqual(len({p.read_bytes() for p in paths}), 1)
            self.assertEqual(json.loads(paths[0].read_text()), expected)
            manifest = finalize(output)
            for name in TAGS:
                self.assertIn(f'sing-box/{name}.srs', manifest['sha256'])
            self.assertIn('srslist.json', manifest['sha256'])
            self.assertIn('nekobox/srslist.json', manifest['sha256'])
            self.assertEqual(index['geoip-ir'],
                'https://raw.githubusercontent.com/ReCode1324/IranShield-Rules/main/dist/sing-box/direct-iran-ips.srs')

    def test_broken_or_missing_binary_fails_without_overwriting_existing_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            output = home / 'dist'
            build(output, ROOT / 'tests/fixtures', 'user/repo', False)
            compiled_fixtures(output)
            publish(output, 'user/repo', 'main', root=home)
            previous = (home / 'srslist.json').read_bytes()
            file = output / 'sing-box/direct-iran-ips.srs'
            file.unlink()
            with self.assertRaisesRegex(RuntimeError, 'direct-iran-ips.srs'):
                publish(output, 'user/repo', 'main', root=home)
            self.assertEqual(previous, (home / 'srslist.json').read_bytes())
            file.write_bytes(b'NOT_SRS-file-bad')
            with self.assertRaisesRegex(RuntimeError, 'Invalid SRS magic'):
                publish(output, 'user/repo', 'main', root=home)
            self.assertEqual(previous, (home / 'srslist.json').read_bytes())

    def test_invalid_source_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            output = home / 'dist'
            build(output, ROOT / 'tests/fixtures', 'user/repo', False)
            compiled_fixtures(output)
            source = output / 'sing-box/block-ads.json'
            source.write_text('{"version": 2, "rules": []}\n')
            with self.assertRaisesRegex(RuntimeError, 'Invalid/empty source JSON'):
                publish(output, 'user/repo', 'main', root=home)
            self.assertFalse((home / 'srslist.json').exists())

    def test_repository_and_branch_validation(self):
        with self.assertRaises(ValueError):
            make_index('invalid-owner-repo', 'main')
        with self.assertRaises(ValueError):
            make_index('user/repo', '../../bad')
        self.assertIn('/ReCode1324/IranShield-Rules/main/',
            make_index('ReCode1324/IranShield-Rules', 'main')['block-ads'])

    def test_cli_publisher_executes_real_production_script(self):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            app = home / 'project'
            (app / 'scripts').mkdir(parents=True)
            for filename in ('publish.py', 'catalog.py'):
                shutil.copyfile(ROOT / 'scripts' / filename, app / 'scripts' / filename)
            output = home / 'dist'
            build(output, ROOT / 'tests/fixtures', 'user/repo', False)
            compiled_fixtures(output)
            process = subprocess.run(
                [sys.executable, str(app / 'scripts/publish.py'),
                 '--out', str(output), '--repository', 'ReCode1324/IranShield-Rules', '--branch', 'main'],
                cwd=home, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn('Published 12 NekoBox names', process.stdout)
            self.assertTrue((app / 'srslist.json').is_file())
            self.assertEqual(json.loads((app / 'srslist.json').read_text()),
                make_index('ReCode1324/IranShield-Rules', 'main'))


if __name__ == '__main__':
    unittest.main()
