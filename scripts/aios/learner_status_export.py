#!/usr/bin/env python3
"""Read the existing task tracker into a local, self-reported learner projection.

No network, record writes, inferred execution/assessment state or receipt verification.
The output's source time is the input file's modification time, not the export time.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import unicodedata

TRACKER = Path('03_RevOps/customer_journey/task_tracker.md')
MAX_BYTES = 1024 * 1024
MAX_UNITS = 2000
TABLES = {
    'Active': ('Task', 'Owner', 'Status', 'Due', 'Notes'),
    'Up Next': ('Task', 'Owner', 'Priority', 'Depends On'),
    'Completed': ('Task', 'Completed', 'By', 'Notes'),
}
PLACEHOLDERS = {
    'Active': ('', 'Founder / VA', 'In Progress / Blocked / In Review', '', ''),
    'Up Next': ('', '', 'High / Medium / Low', ''),
    'Completed': ('', '', '', ''),
}


class Refused(ValueError):
    """Unsupported or incomplete input; the previous output must stay intact."""


def cells(line, number):
    line = line.strip()
    if not (line.startswith('|') and line.endswith('|')) or '\\|' in line:
        raise Refused(f'line {number}: expected a complete table row; escaped pipes are unsupported')
    return tuple(value.strip() for value in line[1:-1].split('|'))


def parse_tracker(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '# Task Tracker':
        raise Refused('expected the existing Task Tracker header')
    seen, phase, section, rows, identities = set(), {}, None, [], set()
    for number, raw in enumerate(lines[1:], 2):
        line = raw.strip()
        if line.startswith('## '):
            if section and phase[section] != 'rows':
                raise Refused(f'{section}: incomplete table header or separator')
            name = line[3:].strip()
            if name == 'How to Use This':
                section = None
                continue
            if name not in TABLES or name in seen:
                raise Refused(f'line {number}: unsupported or repeated task section')
            section = name
            seen.add(name)
            phase[name] = 'header'
            continue
        if not line or line == '---':
            continue
        if line.startswith('#'):
            raise Refused(f'line {number}: unsupported heading')
        if section is None:
            if line.startswith('|'):
                raise Refused(f'line {number}: table outside the supported task sections')
            continue
        values = cells(line, number)
        expected = TABLES[section]
        if len(values) != len(expected):
            raise Refused(f'line {number}: wrong column count for {section}')
        if phase[section] == 'header':
            if values != expected:
                raise Refused(f'line {number}: unsupported {section} column names')
            phase[section] = 'separator'
            continue
        if phase[section] == 'separator':
            if not all(re.fullmatch(r':?-{3,}:?', value) for value in values):
                raise Refused(f'line {number}: missing table separator')
            phase[section] = 'rows'
            continue
        if values == expected:
            raise Refused(f'line {number}: repeated table header')
        if not values[0]:
            if values == PLACEHOLDERS[section] or not any(values):
                continue
            raise Refused(f'line {number}: fields supplied without a task')
        fields = dict(zip(expected, values))
        if section == 'Active' and fields['Status'] not in ('In Progress', 'Blocked', 'In Review'):
            raise Refused(f'line {number}: unsupported or missing Active status')
        if section == 'Up Next' and fields['Priority'] not in ('', 'High', 'Medium', 'Low'):
            raise Refused(f'line {number}: unsupported priority')
        identity = unicodedata.normalize('NFC', fields['Task']).casefold()
        if identity in identities:
            raise Refused(f'line {number}: duplicate task label; disambiguate the existing source rows')
        identities.add(identity)
        rows.append((number, section, fields, identity))
        if len(rows) > MAX_UNITS:
            raise Refused('more than 2000 task rows; no partial projection was produced')
    if seen != set(TABLES) or any(value != 'rows' for value in phase.values()):
        raise Refused('all three supported task tables and their headers are required')
    return rows


def read_source(repo, now):
    root = Path(repo).resolve(strict=True)
    source = root
    for part in TRACKER.parts:
        source = source / part
        if source.is_symlink():
            raise Refused('the selected tracker path must not contain symlinks')
    initial = source.lstat()
    if not stat.S_ISREG(initial.st_mode) or initial.st_size > MAX_BYTES:
        raise Refused('the selected tracker must be a regular file of at most 1 MiB')
    # Nonblocking open also bounds a regular-file-to-FIFO race after the precheck.
    descriptor = os.open(str(source), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) |
                         getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise Refused('the selected tracker must be a regular file of at most 1 MiB')
        data = stream.read(MAX_BYTES + 1)
        after = os.fstat(stream.fileno())
    if len(data) > MAX_BYTES:
        raise Refused('the selected tracker exceeds 1 MiB')
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise Refused('the source changed during its read; retry after its writer finishes')
    if not math.isfinite(after.st_mtime) or after.st_mtime > now.timestamp():
        raise Refused('source modification time is invalid or in the future')
    modified = dt.datetime.fromtimestamp(after.st_mtime, dt.timezone.utc).isoformat(timespec='seconds')
    return source, data, modified.replace('+00:00', 'Z')


def projection(repo, freshness_minutes, fictional=False, now=None):
    if isinstance(freshness_minutes, bool) or not isinstance(freshness_minutes, (int, float)) \
            or not math.isfinite(freshness_minutes) or freshness_minutes <= 0:
        raise Refused('freshness_minutes must be an explicitly supplied positive number')
    now = now or dt.datetime.now(dt.timezone.utc)
    source, data, modified = read_source(repo, now)
    try:
        rows = parse_tracker(data.decode('utf-8'))
    except UnicodeDecodeError as error:
        raise Refused('the selected tracker must be UTF-8') from error
    units = []
    for number, section, fields, identity in rows:
        reported = fields.get('Status') or section
        detail = '. '.join(f'{key}: {value or "Unknown"}' for key, value in fields.items() if key != 'Task')
        units.append({
            'id': 'tracker-' + hashlib.sha256(identity.encode()).hexdigest(),
            'title': fields['Task'],
            'outcome': f'Self-reported tracker progress: {reported}. {detail}',
            'state': None,
            'owner': fields.get('Owner') or None,
            'reviewer': None,
            'next_actor': None,
            'entered_at': None,
            'ref': TRACKER.as_posix() + f'#L{number}',
            'evidence': [],
            'reported_status': reported,
            'tracker_section': section,
            'tracker_fields': fields,
        })
    snapshot = {
        'schema': 'learner-status/1',
        'writer': 'learner_status_export.py (local exporter)',
        'self_reported': True,
        'as_of': modified,
        'source_timestamp_kind': 'local filesystem modification time, not independently verified evidence time',
        'freshness_minutes': freshness_minutes,
        'sources': [{
            'label': 'Instance-owned task tracker',
            'ref': TRACKER.as_posix(),
            'revision': 'sha256:' + hashlib.sha256(data).hexdigest(),
            'verification': 'Local file bytes and modification time only. Task progress is self-reported; '
                            'notes and dates are not verified execution, review, acceptance or assessment receipts.',
        }],
        'coverage': {
            'declared_ids': [unit['id'] for unit in units],
            'omitted_ids': [],
            'note': 'Scope is every nonempty task row in the three selected tracker tables, not all business work. '
                    'IDs are derived display identifiers from normalized task labels; renaming a task changes its ID. '
                    'Lifecycle, execution and assessment state remain unknown; reported source fields are shown in text.',
        },
        'units': units,
    }
    if fictional:
        snapshot['fictional'] = True
    encoded = (json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(encoded) > MAX_BYTES:
        raise Refused('projection exceeds the reader\'s 1 MiB limit; no partial output was produced')
    return source, snapshot, encoded


def export(repo, output, freshness_minutes, fictional=False, now=None):
    source, snapshot, encoded = projection(repo, freshness_minutes, fictional, now)
    destination = Path(output).absolute()
    if destination.is_symlink() or destination.resolve() == source.resolve():
        raise Refused('output must be a separate regular file, never the tracker or a symlink')
    if destination.exists() and not destination.is_file():
        raise Refused('output must be a regular file')
    if not destination.parent.is_dir():
        raise Refused('output directory must already exist')
    descriptor, temporary = tempfile.mkstemp(prefix='.' + destination.name + '.', suffix='.tmp',
                                              dir=str(destination.parent))
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.is_symlink():
            raise Refused('output changed to a symlink; previous output retained')
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.', help='instance root; reads only the selected tracker path')
    parser.add_argument('--output', required=True, help='local JSON output in an existing directory')
    parser.add_argument('--freshness-minutes', type=float, required=True,
                        help='explicit source-age policy; the tool supplies no operating default')
    parser.add_argument('--fictional', action='store_true', help='mark explicitly invented practice input')
    args = parser.parse_args(argv)
    try:
        snapshot = export(args.repo, args.output, args.freshness_minutes, args.fictional)
    except (Refused, OSError, ValueError) as error:
        print(f'REFUSED: {error}', file=sys.stderr)
        return 2
    print(f'Exported {len(snapshot["units"])} self-reported rows; source {snapshot["sources"][0]["revision"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
