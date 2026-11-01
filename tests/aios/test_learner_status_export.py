"""The selected tracker really exports to the unchanged reader; refusals preserve last good."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / 'scripts/aios/learner_status_export.py'
READER = ROOT / '03_RevOps/site/status/status.js'
SPEC = importlib.util.spec_from_file_location('learner_status_export', SCRIPT)
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)
TEMPLATE = (ROOT / EXPORTER.TRACKER).read_text()
FIXED_TIME = dt.datetime(2026, 10, 31, 22, tzinfo=dt.timezone.utc).timestamp()


def tracker_text():
    return TEMPLATE.replace(
        '| | Founder / VA | In Progress / Blocked / In Review | | |',
        '| Prepare the practice guide | Practice builder | In Progress | Next week | <script>plain text</script> |'
    ).replace('| | | High / Medium / Low | |',
              '| Review the practice guide | Practice reviewer | High | Prepare the practice guide |'
    ).replace('| | | | |',
              '| Open the practice workspace | 2026-10-31 | Practice operator | Self-reported only |')


class LearnerStatusExport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.source = self.workspace / EXPORTER.TRACKER
        os.makedirs(self.source.parent, exist_ok=True)
        self.output = self.workspace / 'practice_status.json'
        self.write_source(tracker_text())

    def write_source(self, text):
        self.source.write_text(text)
        os.utime(self.source, (FIXED_TIME, FIXED_TIME))

    def command(self):
        return subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.workspace),
                               '--output', str(self.output), '--freshness-minutes', '1440', '--fictional'],
                              capture_output=True, text=True)

    def export_ok(self):
        result = self.command()
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(self.output.read_bytes())

    def test_actual_exported_bytes_load_unchanged_in_the_actual_reader(self):
        source_before = self.source.read_bytes()
        modified_before = self.source.stat().st_mtime_ns
        snapshot = self.export_ok()
        emitted = self.output.read_bytes()
        program = r'''
const fs = require('node:fs');
const api = require(process.argv[1]);
const bytes = fs.readFileSync(process.argv[2], 'utf8');
const view = api.createReader().load(bytes, 'actual-export.json');
if (view.failure) throw new Error(view.failure);
console.log(JSON.stringify({snapshot: view.snapshot, units: view.units}));
'''
        result = subprocess.run(['node', '-e', program, str(READER), str(self.output)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        rendered = json.loads(result.stdout)
        self.assertEqual(rendered['snapshot'], snapshot)
        self.assertEqual(len(rendered['units']), 3)
        self.assertEqual(snapshot['sources'][0]['revision'], 'sha256:' + hashlib.sha256(source_before).hexdigest())
        self.assertEqual(snapshot['as_of'], '2026-10-31T22:00:00Z')
        self.assertEqual([u['reported_status'] for u in snapshot['units']], ['In Progress', 'Up Next', 'Completed'])
        self.assertEqual([u['state'] for u in rendered['units']], [None, None, None])
        self.assertEqual([u['evidence'] for u in rendered['units']], [[], [], []])
        self.assertIn('<script>plain text</script>', rendered['units'][0]['outcome'])
        self.assertEqual(snapshot['units'][2]['owner'], None)  # "By" is a completer, not a current owner.
        self.assertEqual(snapshot['coverage']['declared_ids'], [u['id'] for u in snapshot['units']])
        self.assertEqual(snapshot['coverage']['omitted_ids'], [])
        self.assertTrue(snapshot['fictional'])
        self.assertEqual(self.output.read_bytes(), emitted)
        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertEqual(self.source.stat().st_mtime_ns, modified_before)
        if os.name != 'nt':
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_retry_is_deterministic_and_does_not_refresh_source_time(self):
        self.export_ok()
        first = self.output.read_bytes()
        self.export_ok()
        self.assertEqual(self.output.read_bytes(), first)

    def test_display_identity_survives_status_owner_and_section_changes(self):
        first = self.export_ok()['units'][0]['id']
        self.write_source(tracker_text().replace('Practice builder | In Progress', 'Another practice role | Blocked'))
        self.assertEqual(self.export_ok()['units'][0]['id'], first)
        self.write_source(TEMPLATE.replace('| | | | |',
                          '| Prepare the practice guide | Date not supplied | Practice operator | Done by report |'))
        unit = self.export_ok()['units'][0]
        self.assertEqual((unit['id'], unit['reported_status'], unit['state']), (first, 'Completed', None))
        self.assertIsNone(unit['entered_at'])

    def test_placeholder_only_template_has_explicit_empty_file_scope(self):
        self.write_source(TEMPLATE)
        snapshot = self.export_ok()
        self.assertEqual(snapshot['units'], [])
        self.assertEqual(snapshot['coverage']['declared_ids'], [])
        self.assertIn('not all business work', snapshot['coverage']['note'])

    def test_unsupported_missing_duplicate_and_truncated_rows_refuse_without_overwriting(self):
        self.export_ok()
        good = self.output.read_bytes()
        duplicate = tracker_text().replace('Review the practice guide', 'PREPARE THE PRACTICE GUIDE')
        cases = {
            'unknown status': tracker_text().replace('| In Progress |', '| Certified |'),
            'missing status': tracker_text().replace('| In Progress |', '| |'),
            'unknown section': tracker_text().replace('## Active', '## Other work'),
            'unknown columns': tracker_text().replace('| Task | Owner | Status | Due | Notes |',
                                                     '| Task | Owner | Grade | Due | Notes |'),
            'truncated row': tracker_text().replace('| In Progress | Next week |', '| In Progress |'),
            'missing table': tracker_text().split('## Completed')[0],
            'missing separator': tracker_text().replace('|---|---|---|---|---|', '| not a separator | | | | |'),
            'duplicate across sections': duplicate,
            'fields without task': tracker_text().replace('| Prepare the practice guide |', '| |'),
        }
        for label, text in cases.items():
            with self.subTest(case=label):
                self.write_source(text)
                result = self.command()
                self.assertEqual(result.returncode, 2)
                self.assertIn('REFUSED:', result.stderr)
                self.assertEqual(self.output.read_bytes(), good)

    def test_missing_source_and_invalid_utf8_do_not_create_a_successful_empty_view(self):
        self.source.unlink()
        result = self.command()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.output.exists())
        self.source.write_bytes(b'\xff')
        os.utime(self.source, (FIXED_TIME, FIXED_TIME))
        result = self.command()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.output.exists())

    def test_future_time_and_invalid_age_policy_preserve_last_good(self):
        self.export_ok()
        good = self.output.read_bytes()
        future = dt.datetime.now(dt.timezone.utc).timestamp() + 3600
        os.utime(self.source, (future, future))
        self.assertEqual(self.command().returncode, 2)
        self.assertEqual(self.output.read_bytes(), good)
        self.write_source(tracker_text())
        for value in (0, -1, float('nan'), float('inf'), True):
            with self.subTest(policy=str(value)), self.assertRaises(EXPORTER.Refused):
                EXPORTER.export(self.workspace, self.output, value)
            self.assertEqual(self.output.read_bytes(), good)

    def test_atomic_replace_failure_keeps_previous_output_and_source(self):
        self.export_ok()
        good, source = self.output.read_bytes(), self.source.read_bytes()
        self.write_source(tracker_text().replace('Next week', 'A later self-reported date'))
        changed_source = self.source.read_bytes()
        with mock.patch.object(EXPORTER.os, 'replace', side_effect=OSError('simulated interrupted replace')):
            with self.assertRaisesRegex(OSError, 'interrupted replace'):
                EXPORTER.export(self.workspace, self.output, 1440)
        self.assertEqual(self.output.read_bytes(), good)
        self.assertEqual(self.source.read_bytes(), changed_source)
        self.assertNotEqual(changed_source, source)
        self.assertEqual(list(self.workspace.glob('.practice_status.json.*.tmp')), [])

    def test_source_overwrite_and_symlinks_are_refused(self):
        before = self.source.read_bytes()
        with self.assertRaises(EXPORTER.Refused):
            EXPORTER.export(self.workspace, self.source, 1440)
        self.assertEqual(self.source.read_bytes(), before)
        if hasattr(os, 'symlink') and os.name != 'nt':
            self.output.symlink_to(self.source)
            self.assertEqual(self.command().returncode, 2)
            self.assertEqual(self.source.read_bytes(), before)
            self.output.unlink()
            copy = self.source.with_name('synthetic_tracker.md')
            self.source.rename(copy)
            self.source.symlink_to(copy)
            self.assertEqual(self.command().returncode, 2)
            self.assertFalse(self.output.exists())

    def test_reader_size_and_row_limits_refuse_without_partial_output(self):
        self.export_ok()
        good = self.output.read_bytes()
        self.source.write_bytes(b'x' * (EXPORTER.MAX_BYTES + 1))
        self.assertEqual(self.command().returncode, 2)
        self.assertEqual(self.output.read_bytes(), good)
        many = '\n'.join(f'| Task {n} | Practice role | In Progress | | |' for n in range(2001))
        text = TEMPLATE.replace('| | Founder / VA | In Progress / Blocked / In Review | | |', many)
        with self.assertRaisesRegex(EXPORTER.Refused, '2000'):
            EXPORTER.parse_tracker(text)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO refusal applies on platforms with named pipes')
    def test_actual_cli_fifo_refuses_promptly_and_preserves_last_good(self):
        self.export_ok()
        good = self.output.read_bytes()
        self.source.unlink()
        os.mkfifo(self.source, 0o600)
        result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.workspace),
                                 '--output', str(self.output), '--freshness-minutes', '1440'],
                                capture_output=True, text=True, timeout=2)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('regular file', result.stderr)
        self.assertEqual(self.output.read_bytes(), good)
        self.assertEqual(list(self.workspace.glob('.practice_status.json.*.tmp')), [])

    @unittest.skipUnless(hasattr(os, 'mkfifo') and hasattr(os, 'O_NONBLOCK'),
                         'nonblocking FIFO race control applies on supported platforms')
    def test_file_to_fifo_race_after_precheck_is_refused_without_hanging(self):
        self.export_ok()
        good = self.output.read_bytes()
        # A disposable subprocess simulates the source changing immediately before the real open.
        # It invokes the actual CLI entry and actual os.open, with a timeout that reaps any hung child.
        program = r'''
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('exporter_race', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = Path(sys.argv[2]).resolve() / module.TRACKER
real_open = os.open
def race(path, flags, *args, **kwargs):
    if Path(path) == source:
        source.unlink()
        os.mkfifo(source, 0o600)
    return real_open(path, flags, *args, **kwargs)
module.os.open = race
raise SystemExit(module.main(['--repo', sys.argv[2], '--output', sys.argv[3], '--freshness-minutes', '1440']))
'''
        result = subprocess.run([sys.executable, '-c', program, str(SCRIPT), str(self.workspace), str(self.output)],
                                capture_output=True, text=True, timeout=2)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('regular file', result.stderr)
        self.assertEqual(self.output.read_bytes(), good)
        self.assertEqual(list(self.workspace.glob('.practice_status.json.*.tmp')), [])


if __name__ == '__main__':
    unittest.main()
