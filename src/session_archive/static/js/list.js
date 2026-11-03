// Sidebar: session list, folder filter and full-text search.
import { $, esc, reEsc } from './dom.js';
import { S } from './state.js';
import { t } from './i18n.js';
import { activeText, base, bucket, dur, fsz, range } from './format.js';
import { SOURCE_KEYS, icon } from './icons.js';

export function draw() {
  const q = $('#q').value.toLowerCase().trim(), folder = $('#fold').value, source = $('#srcf').value;
  const matches = (s) => (s.title + ' ' + s.cwd + ' ' + s.id + ' ' + s.branch).toLowerCase().includes(q);
  const list = S.all.filter((s) => (!folder || s.cwd === folder) && (!source || s.source === source) && (!q || matches(s) || (S.hitsQ === q && S.hits[s.id])));
  $('#count').textContent = t('count', { a: list.length, b: S.all.length }) + (q.length >= 2 && S.hitsQ !== q ? t('searching') : '');

  let html = '', lastBucket = '';
  for (const s of list) {
    const b = bucket(s.last);
    if (b !== lastBucket) { lastBucket = b; html += `<div class="grp">${esc(b)}</div>`; }
    let snippet = '';
    const hit = q && S.hitsQ === q && S.hits[s.id];
    if (hit) {
      const marked = esc(hit.snippet).replace(new RegExp(reEsc(esc(q)), 'gi'), (m) => '<mark>' + m + '</mark>');
      snippet = `<div class="snip">…${marked}…${hit.count > 1 ? ' ' + t('matches', { n: hit.count }) : ''}</div>`;
    }
    const long = s.last - s.first > 86400 ? ' long' : '';
    html += `<a class="item${s.id === S.cur ? ' on' : ''}" href="#/${s.id}" data-id="${s.id}">`
      + `<div class="t"><span class="ico" title="${esc(t('src.' + s.source))}">${icon(s.source)}</span>${esc(s.title || t('untitled'))}</div>`
      + `<div class="s">${range(s)} · <b class="sp${long}">${dur(s.last - s.first)}</b>${activeText(s)}</div>`
      + `<div class="s">${esc(s.branch || '—')} · ${fsz(s.size)} · ${esc(base(s.cwd))} · ${t('messages', { n: s.n })}</div>${snippet}</a>`;
  }
  $('#list').innerHTML = html || `<div class="grp">${t('noresult')}</div>`;
}

export function buildFolders() {
  const counts = {};
  for (const s of S.all) counts[s.cwd] = (counts[s.cwd] || 0) + 1;
  const options = Object.entries(counts).sort((a, b) => b[1] - a[1])
    .map(([cwd, n]) => `<option value="${esc(cwd)}">${esc(base(cwd))} (${n})</option>`).join('');
  $('#fold').innerHTML = `<option value="">${t('folder.all', { n: S.all.length })}</option>` + options;
}

export function buildSources() {
  const counts = {};
  for (const s of S.all) counts[s.source] = (counts[s.source] || 0) + 1;
  const options = SOURCE_KEYS.filter((k) => counts[k])
    .map((k) => `<option value="${k}">${esc(t('src.' + k))} (${counts[k]})</option>`).join('');
  $('#srcf').innerHTML = `<option value="">${t('src.all')}</option>` + options;
}

let timer;
export function onSearch() {
  draw();
  const q = $('#q').value.toLowerCase().trim();
  clearTimeout(timer);
  if (q.length < 2) { S.hits = {}; S.hitsQ = ''; return; }
  timer = setTimeout(async () => {
    const res = await (await fetch('/api/search?q=' + encodeURIComponent(q))).json();
    if ($('#q').value.toLowerCase().trim() !== q) return; // a newer query superseded this one
    S.hits = {};
    for (const x of res) S.hits[x.id] = x;
    S.hitsQ = q;
    draw();
  }, 250);
}
