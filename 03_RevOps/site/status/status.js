(function () {
  'use strict';
  const STATES = ['ready', 'assigned', 'running', 'review', 'reviewed', 'source_complete', 'merged', 'deployed', 'accepted_in_use', 'blocked', 'parked'];
  const KINDS = ['execution', 'source_complete', 'reviewed', 'merged', 'installed', 'deployed', 'accepted_in_use'];
  const MAX_BYTES = 1024 * 1024;
  const text = value => typeof value === 'string' && value.trim() ? value.trim() : 'Unknown';
  const known = value => text(value) !== 'Unknown';
  function timestamp(value) {
    if (typeof value !== 'string') return null;
    const m = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d{1,3})?(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
    if (!m || (m[4] && (+m[4] > 23 || +m[5] > 59))) return null;
    const ms = Date.parse(value);
    const offset = m[2] === 'Z' ? 0 : (m[3] === '+' ? 1 : -1) * (+m[4] * 60 + +m[5]);
    return Number.isFinite(ms) && new Date(ms + offset * 60000).toISOString().slice(0, 19) === m[1] ? ms : null;
  }
  function safeLink(value) {
    if (typeof value !== 'string') return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
    } catch { return null; }
  }
  function stringList(value, name) {
    if (!Array.isArray(value) || value.some(x => typeof x !== 'string' || !x.trim())) throw new Error(`${name} must list stable IDs.`);
    if (new Set(value).size !== value.length) throw new Error(`${name} contains duplicate IDs.`);
    return value;
  }
  function parseSnapshot(raw, now = Date.now()) {
    if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > MAX_BYTES) throw new Error('Select a JSON file no larger than 1 MiB.');
    let data;
    try { data = JSON.parse(raw); } catch { throw new Error('The selected file is not valid JSON.'); }
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('The snapshot must be a JSON object.');
    if (data.availability === 'refused' || data.availability === 'unavailable') throw new Error(`Source ${data.availability}: ${text(data.reason)}`);
    if (data.schema !== 'learner-status/1') throw new Error('Expected schema learner-status/1.');
    const asOf = timestamp(data.as_of);
    if (asOf === null) throw new Error('Source as_of needs a valid date and time with timezone.');
    if (asOf > now) throw new Error('The source is dated in the future; its time needs verification.');
    if (typeof data.freshness_minutes !== 'number' || !Number.isFinite(data.freshness_minutes) || data.freshness_minutes <= 0) throw new Error('The projection must declare a positive freshness_minutes limit.');
    if (!Array.isArray(data.sources) || !data.sources.length || data.sources.some(s => !s || !known(s.ref) || !known(s.revision))) throw new Error('Name the canonical plan/work sources and their exact revisions.');
    if (!Array.isArray(data.units) || data.units.length > 2000) throw new Error('Supply an explicit units array with no more than 2000 items.');
    const coverage = data.coverage;
    if (!coverage || typeof coverage !== 'object') throw new Error('Declare coverage, including omitted work.');
    const declared = stringList(coverage.declared_ids, 'coverage.declared_ids');
    const omitted = stringList(coverage.omitted_ids, 'coverage.omitted_ids');
    const ids = [];
    for (const unit of data.units) {
      if (!unit || typeof unit !== 'object' || !known(unit.id)) throw new Error('Every displayed unit needs a stable ID.');
      ids.push(unit.id);
      if (unit.state !== undefined && unit.state !== null && !STATES.includes(unit.state)) throw new Error(`Unknown state for ${unit.id}; use the shared unit vocabulary or omit it.`);
      if (unit.evidence !== undefined && !Array.isArray(unit.evidence)) throw new Error(`Evidence for ${unit.id} must be an array.`);
      if ((unit.evidence || []).some(r => !r || typeof r !== 'object' || !KINDS.includes(r.kind))) throw new Error(`Unknown evidence kind for ${unit.id}.`);
    }
    const represented = [...ids, ...omitted];
    if (new Set(represented).size !== represented.length || represented.length !== declared.length || represented.some(id => !declared.includes(id))) throw new Error('Displayed and omitted IDs must partition the declared scope, without duplicates.');
    return data;
  }
  function receiptComplete(receipt, now) {
    const observed = timestamp(receipt.observed_at);
    return known(receipt.ref) && known(receipt.revision) && observed !== null && observed <= now;
  }
  function unitView(unit, now) {
    const evidence = (unit.evidence || []).map(r => ({ ...r, complete: receiptComplete(r, now) }));
    const execution = evidence.some(r => r.kind === 'execution' && r.complete && known(unit.owner) && known(unit.execution_revision) && r.owner === unit.owner && r.unit_id === unit.id && r.revision === unit.execution_revision);
    let qualification = 'Reported state; evidence has not been independently verified.';
    if (unit.state === 'running') qualification = execution ? 'Matching execution receipt supplied; not independently verified.' : 'Execution unknown: a claim or assignment does not establish running.';
    if (unit.state === 'accepted_in_use') qualification = 'Owner acceptance must be verified in the linked owning decision; this page cannot award it.';
    return { ...unit, evidence, executionReceiptSupplied: execution, qualification };
  }
  function buildView(snapshot, loadedAt, now = Date.now(), failure = null, attemptedAt = loadedAt, filename = 'Selected file') {
    const asOf = timestamp(snapshot.as_of);
    return {
      snapshot, filename, loadedAt, renderedAt: now, attemptedAt, failure,
      retained: Boolean(failure), ageMinutes: (now - asOf) / 60000,
      freshness: now < asOf ? 'Time unverified' : now - asOf > snapshot.freshness_minutes * 60000 ? 'Stale' : 'Within declared age limit',
      units: snapshot.units.map(unit => unitView(unit, now))
    };
  }
  function createReader() {
    let lastGood = null, loadedAt = null, filename = null, failure = null, attemptedAt = null;
    return {
      load(raw, name, now = Date.now()) {
        attemptedAt = now;
        try { lastGood = parseSnapshot(raw, now); loadedAt = now; filename = name; failure = null; }
        catch (error) { failure = error.message; }
        return this.view(now);
      },
      fail(reason, now = Date.now()) { failure = reason; attemptedAt = now; return this.view(now); },
      view(now = Date.now()) { return lastGood ? buildView(lastGood, loadedAt, now, failure, attemptedAt, filename) : { failure, attemptedAt, renderedAt: now, units: null }; }
    };
  }
  const api = { STATES, MAX_BYTES, timestamp, safeLink, parseSnapshot, buildView, createReader };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.LearnerStatus = api;
  if (typeof document === 'undefined') return;

  const reader = createReader();
  const $ = id => document.getElementById(id);
  const time = value => typeof value === 'number' ? new Date(value).toISOString() : timestamp(value) === null ? 'Unknown' : value;
  function node(tag, content, className) {
    const element = document.createElement(tag);
    if (content !== undefined) element.textContent = text(content);
    if (className) element.className = className;
    return element;
  }
  function reference(value) {
    const url = safeLink(value);
    const element = node(url ? 'a' : 'span', value);
    if (url) { element.href = url; element.target = '_blank'; element.rel = 'noopener noreferrer'; }
    return element;
  }
  function pair(list, label, value) {
    list.append(node('dt', label));
    const dd = node('dd');
    dd.append(value instanceof Node ? value : node('span', text(value)));
    list.append(dd);
  }
  function render() {
    const view = reader.view();
    $('rendered').textContent = time(view.renderedAt);
    $('attempted').textContent = time(view.attemptedAt);
    $('load-outcome').textContent = view.failure ? `Load refused: ${view.failure}${view.units ? ' Last-good view retained below; this is not a successful refresh.' : ' No snapshot is available.'}` : view.units ? 'File read successfully. Evidence remains supplied and unverified.' : 'No file selected. Coverage and work state are unknown.';
    $('load-outcome').className = view.failure ? 'notice error' : 'notice';
    const region = $('snapshot');
    region.replaceChildren();
    if (!view.units) return;
    const data = view.snapshot;
    const header = node('section', undefined, 'panel provenance');
    const line = node('div', undefined, 'section-heading');
    line.append(node('h2', view.retained ? 'Last-good snapshot' : 'Supplied snapshot'), node('span', view.freshness, view.freshness === 'Within declared age limit' ? 'badge' : 'badge warning'));
    header.append(line);
    if (data.fictional === true) header.append(node('p', 'Fictional practice data. These are not real work records.', 'fictional'));
    header.append(node('p', 'This reader displays supplied records. It does not verify the linked evidence or execute work.', 'muted'));
    const facts = node('dl');
    pair(facts, 'Source as of', time(data.as_of));
    pair(facts, 'Source age / declared limit', `${Math.max(0, Math.floor(view.ageMinutes))} / ${data.freshness_minutes} minutes${view.ageMinutes < 0 ? ' (source time is unverified)' : ''}`);
    pair(facts, 'Coordinator / writer', data.writer);
    pair(facts, 'Selected file', view.filename);
    pair(facts, 'Last successful local read', time(view.loadedAt));
    pair(facts, 'Covered scope', `${data.units.length} displayed; ${data.coverage.omitted_ids.length} omitted; ${data.coverage.declared_ids.length} declared IDs`);
    pair(facts, 'Omitted IDs', data.coverage.omitted_ids.length ? data.coverage.omitted_ids.join(', ') : 'None explicitly declared');
    pair(facts, 'Coverage note', data.coverage.note);
    header.append(facts, node('h3', 'Canonical sources'));
    const sources = node('ul');
    for (const source of data.sources) {
      const item = node('li');
      item.append(node('strong', text(source.label)), document.createTextNode(' · '), reference(source.ref), node('small', `Revision: ${source.revision} · Verification: ${text(source.verification)}`));
      sources.append(item);
    }
    header.append(sources);
    region.append(header);
    const grid = node('div', undefined, 'work-grid');
    for (const unit of view.units) {
      const card = node('article', undefined, 'panel work');
      const heading = node('div', undefined, 'section-heading');
      heading.append(node('span', unit.id, 'unit-id'), node('span', unit.state || 'Unknown', 'badge'));
      card.append(heading, node('h2', text(unit.title)), node('p', text(unit.outcome)), node('p', unit.qualification, 'muted'));
      const info = node('dl');
      for (const [label, value] of [['Pocket', unit.pocket], ['Project', unit.project], ['Round', unit.round], ['Owner', unit.owner], ['Reviewer', unit.reviewer], ['Next actor', unit.next_actor], ['State entered', time(unit.entered_at)], ['Agent effort', unit.agent_effort], ['Human effort', unit.human_effort]]) pair(info, label, value);
      pair(info, 'Owning work record', reference(unit.ref));
      card.append(info);
      if (unit.state === 'blocked' || unit.state === 'parked' || unit.blocker) {
        const hold = unit.blocker || {};
        card.append(node('h3', 'Specific dependency or hold'));
        const detail = node('dl');
        for (const [label, value] of [['Affected stage', hold.stage], ['Dependency / lock', hold.dependency], ['Next actor', hold.next_actor], ['Clears with', hold.clearing_evidence], ['Next look', hold.next_look]]) pair(detail, label, value);
        card.append(detail);
      }
      card.append(node('h3', 'Separate evidence'));
      if (!unit.evidence.length) card.append(node('p', 'No receipts supplied. Source, review, merge, installation, deployment and acceptance are unknown.', 'muted'));
      for (const receipt of unit.evidence) {
        const item = node('div', undefined, 'receipt');
        item.append(node('strong', receipt.kind), node('p', receipt.complete ? 'Receipt fields supplied; linked evidence unverified.' : 'Incomplete or unverified receipt fields.', 'muted'), reference(receipt.ref), node('small', `Revision: ${text(receipt.revision)} · Observed: ${time(receipt.observed_at)}`));
        card.append(item);
      }
      grid.append(card);
    }
    if (!view.units.length) grid.append(node('p', 'The supplied projection explicitly declares no displayed work. Read the coverage and omissions above.'));
    region.append(grid);
  }
  let request = 0;
  $('projection').addEventListener('change', async event => {
    const current = ++request;
    const file = event.target.files[0];
    if (!file) return;
    event.target.value = ''; // Selecting the same file again is another explicit read.
    try {
      if (file.size > MAX_BYTES) throw new Error('Select a JSON file no larger than 1 MiB.');
      const raw = await file.text();
      if (current === request) reader.load(raw, file.name);
    } catch (error) { if (current === request) reader.fail(error.message); }
    if (current === request) render();
  });
  render();
  setInterval(render, 60000); // Recheck age; never change source as_of or read time.
}());
