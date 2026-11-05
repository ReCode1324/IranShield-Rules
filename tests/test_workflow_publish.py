"""Prevent regressions in the self-contained GitHub Actions NekoBox publisher."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/update-rules.yml'
SRS_NAMES = [
    'block-ads', 'block-ads-ir', 'block-ads-global',
    'direct-iran-domains', 'direct-iran-ips', 'direct-iran-all',
]


def publisher_command():
    """Extract the actual command from the Workflow, without needing PyYAML."""
    workflow = WORKFLOW.read_text(encoding='utf-8')
    marker = "          python - <<'PY'\n"
    if marker not in workflow:
        raise AssertionError('No self-contained NekoBox publisher in Workflow')
    block = workflow.split(marker, 1)[1].split('\n          PY\n', 1)[0]
    return "python - <<'PY'\n" + '\n'.join(line[10:] for line in block.splitlines()) + '\nPY\n'


class NekoBoxPublisherTests(unittest.TestCase):
    def test_twice_monthly_schedule(self):
        self.assertIn("cron: '17 3 1,15 * *'", WORKFLOW.read_text())

    def test_publish_from_compiled_binaries_with_missing_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'dist/sing-box').mkdir(parents=True)
            for name in SRS_NAMES:
                (work / 'dist/sing-box' / (name + '.srs')).write_bytes(b'SRS\x00simulated-data')
            env = os.environ.copy()
            env.update(GITHUB_REPOSITORY='ReCode1324/IranShield-Rules', GITHUB_REF_NAME='main')
            result = subprocess.run(['bash', '-e', '-c', publisher_command()],
                                    cwd=work, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = [work / name for name in (
                'srslist.json', 'nekobox/srslist.json',
                'dist/srslist.json', 'dist/nekobox/srslist.json',
            )]
            self.assertTrue(all(p.exists() for p in paths))
            self.assertEqual(len({p.read_bytes() for p in paths}), 1)
            index = json.loads(paths[0].read_text())
            self.assertEqual(len(index), 12)
            self.assertEqual(index['block-ads'],
                'https://raw.githubusercontent.com/ReCode1324/IranShield-Rules/main/dist/sing-box/block-ads.srs')

            (work / 'dist/sing-box/direct-iran-ips.srs').unlink()
            missing = subprocess.run(['bash', '-e', '-c', publisher_command()],
                                     cwd=work, env=env, text=True, capture_output=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn('direct-iran-ips.srs', missing.stderr)


if __name__ == '__main__':
    unittest.main()
