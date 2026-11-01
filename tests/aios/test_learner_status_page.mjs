import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { parseSnapshot, createReader, buildView, safeLink, timestamp } = require('../../03_RevOps/site/status/status.js');
const fixtureText = readFileSync(new URL('../../03_RevOps/site/status/example_status.json', import.meta.url), 'utf8');
const now = Date.parse('2026-10-31T23:00:00Z');
const fixture = () => JSON.parse(fixtureText);
const parse = value => parseSnapshot(JSON.stringify(value), now);

test('declared scope preserves omitted work', () => {
  const data = parseSnapshot(fixtureText, now);
  assert.equal(data.units.length, 2);
  assert.deepEqual(data.coverage.omitted_ids, ['PRACTICE-03']);
});
test('missing optional facts stay missing; a missing units array is not zero work', () => {
  const data = fixture(); delete data.units[0].owner;
  assert.equal(buildView(parse(data), now, now).units[0].owner, undefined);
  delete data.units;
  assert.throws(() => parse(data), /explicit units array/);
});
test('duplicate, dropped and undeclared IDs are refused', () => {
  for (const change of [d => d.units.push(d.units[0]), d => d.coverage.omitted_ids.pop(), d => d.units[0].id = 'UNDECLARED']) {
    const data = fixture(); change(data); assert.throws(() => parse(data), /partition/);
  }
});
test('timezone and real calendar dates are required', () => {
  assert.equal(timestamp('2026-02-30T12:00:00Z'), null);
  assert.equal(timestamp('2026-10-31T12:00:00'), null);
  assert.equal(timestamp('2026-10-31T12:00:00-07:00'), Date.parse('2026-10-31T19:00:00Z'));
  for (const value of ['not a date', '2026-10-31T22:00:00', '2026-10-32T22:00:00Z']) {
    const data = fixture(); data.as_of = value; assert.throws(() => parse(data), /valid date/);
  }
});
test('future source times and absent freshness policy are refused', () => {
  const data = fixture(); data.as_of = '2026-11-01T00:00:00Z'; assert.throws(() => parse(data), /future/);
  for (const limit of [null, 0, -1, '1440']) {
    const item = fixture(); item.freshness_minutes = limit; assert.throws(() => parse(item), /positive freshness/);
  }
});
test('rendering and reading again do not refresh source age', () => {
  const reader = createReader(); const first = reader.load(fixtureText, 'example.json', now);
  const later = now + 25 * 3600000;
  const aged = reader.view(later);
  assert.equal(first.freshness, 'Within declared age limit');
  assert.equal(aged.freshness, 'Stale');
  assert.equal(aged.snapshot.as_of, first.snapshot.as_of);
  assert.equal(aged.loadedAt, now);
  assert.equal(reader.load(fixtureText, 'example.json', later).freshness, 'Stale');
});
test('malformed and refused loads retain only a visibly qualified last-good view', () => {
  const reader = createReader(); reader.load(fixtureText, 'good.json', now);
  const failed = reader.load('{broken', 'bad.json', now + 1000);
  assert.equal(failed.retained, true); assert.match(failed.failure, /not valid JSON/);
  assert.equal(failed.filename, 'good.json'); assert.equal(failed.loadedAt, now);
  const refused = reader.load(JSON.stringify({ availability: 'refused', reason: 'No authorized source' }), 'refused.json', now + 2000);
  assert.match(refused.failure, /refused/); assert.equal(refused.attemptedAt, now + 2000);
  assert.equal(refused.units.length, 2);
});
test('failed first load supplies no coverage or work count', () => {
  const view = createReader().load('null', 'empty.json', now);
  assert.equal(view.units, null); assert.equal(view.snapshot, undefined);
});
test('a running claim requires matching execution receipt fields', () => {
  const data = fixture(); const unit = data.units[0]; unit.state = 'running'; unit.execution_revision = 'revision-a';
  let view = buildView(parse(data), now, now).units[0];
  assert.equal(view.executionReceiptSupplied, false); assert.match(view.qualification, /claim or assignment/);
  unit.evidence.push({ kind: 'execution', ref: 'local-receipt', revision: 'revision-a', observed_at: '2026-10-31T22:30:00Z', owner: unit.owner, unit_id: unit.id });
  assert.equal(buildView(parse(data), now, now).units[0].executionReceiptSupplied, true);
  for (const [key, value] of [['owner', 'someone else'], ['unit_id', 'OTHER'], ['revision', 'other-revision'], ['observed_at', '2027-01-01T00:00:00Z']]) {
    const changed = structuredClone(data); changed.units[0].evidence[1][key] = value;
    assert.equal(buildView(parse(changed), now, now).units[0].executionReceiptSupplied, false);
  }
});
test('merge is distinct from installation and accepted use remains unverified', () => {
  const data = fixture(); const unit = data.units[0]; unit.state = 'accepted_in_use'; unit.evidence[0].kind = 'merged';
  const view = buildView(parse(data), now, now).units[0];
  assert.deepEqual(view.evidence.map(r => r.kind), ['merged']);
  assert.match(view.qualification, /cannot award/);
});
test('untrusted text is kept as text and executable or credentialed links are not links', () => {
  const data = fixture(); data.units[0].title = '<img src=x onerror=alert(1)>';
  assert.equal(parse(data).units[0].title, data.units[0].title);
  for (const url of ['javascript:alert(1)', 'data:text/html,test', 'file:///private/source', '//example.com', 'https://user:password@example.com/']) assert.equal(safeLink(url), null);
  assert.equal(safeLink('https://example.com/record'), 'https://example.com/record');
});
test('unsupported states, absent provenance and oversized input are refused explicitly', () => {
  const data = fixture(); data.units[0].state = 'DONE'; assert.throws(() => parse(data), /shared unit vocabulary/);
  const missing = fixture(); missing.sources = []; assert.throws(() => parse(missing), /canonical plan/);
  assert.throws(() => parseSnapshot(' '.repeat(1024 * 1024 + 1), now), /1 MiB/);
});
