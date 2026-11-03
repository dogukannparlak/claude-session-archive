// Conversation pane: turns, harness notes, tool cards, header and composer.
import { $, esc } from './dom.js';
import { S } from './state.js';
import { t } from './i18n.js';
import { activeText, dur, fullDate, range } from './format.js';
import { md } from './markdown.js';
import { draw } from './list.js';
import { icon, sourceLabel } from './icons.js';

const NOTE = new Set(['meta', 'system']); // kinds collapsed into "not written by you" notes

function toolSummary(inp) {
  const v = inp.command || inp.file_path || inp.path || inp.pattern || inp.url || inp.query
    || inp.description || inp.prompt || Object.values(inp).find((x) => typeof x === 'string') || '';
  return String(v).replace(/\s+/g, ' ').slice(0, 120);
}

function toolCard(p, res) {
  const dot = res ? (res.err ? 'dot err' : 'dot') : 'dot wait';
  const result = res
    ? `<div class="res"><div class="rs">${esc(res.v.split('\n')[0].slice(0, 140) || '∅')}${res.v.includes('\n') ? ' …' : ''}</div><pre><code>${esc(res.v)}</code></pre></div>`
    : '';
  return `<details class="tool"><summary><span class="${dot}">●</span><span class="tn">${esc(p.name)}</span>`
    + `<span class="ta">(${esc(toolSummary(p.in || {}))})</span></summary>`
    + `<div class="res"><pre><code>${esc(p.v)}</code></pre></div>${result}</details>`;
}

// Merge consecutive assistant records, group consecutive harness notes, drop result-only records.
function buildTurns(messages) {
  const turns = [];
  for (const m of messages) {
    const parts = m.parts.filter((p) => p.k !== 'result');
    if (!parts.length) continue;
    const kind = m.role === 'assistant' ? 'assistant' : m.kind;
    const item = { label: m.label, text: parts.map((p) => p.v).join('\n') };
    const last = turns[turns.length - 1];
    if (last && kind === 'assistant' && last.kind === 'assistant') last.parts.push(...parts);
    else if (last && last.note && NOTE.has(kind)) last.items.push(item);
    else turns.push({ kind, parts: [...parts], note: NOTE.has(kind), items: NOTE.has(kind) ? [item] : null });
  }
  return turns;
}

function renderTurn(turn, results) {
  switch (turn.kind) {
    case 'human': {
      const text = turn.parts.map((p) => p.v).join('\n\n');
      const long = text.length > 700 || text.split('\n').length > 12;
      return `<div class="turn user"><div class="bub${long ? ' clamp' : ''}">${esc(text)}${long ? `<button class="more" data-more>${t('more')}</button>` : ''}</div></div>`;
    }
    case 'shell':
      return `<div class="turn user"><div class="chip">! ${esc(turn.parts[0].v)}</div></div>`;
    case 'command':
      return `<div class="turn user"><div class="chip cmd">${esc(turn.parts[0].v)}</div></div>`;
    case 'interrupt':
      return `<div class="intr">${t('interrupted')}</div>`;
    default:
      if (turn.note) {
        const names = [...new Set(turn.items.map((i) => t('label.' + i.label)))].join(', ');
        const chars = turn.items.reduce((a, i) => a + i.text.length, 0);
        const size = t('note.size', { c: chars > 999 ? (chars / 1000).toFixed(1) + 'k' : chars });
        const bodies = turn.items.map((i) => `<div class="ni"><div class="nl">${esc(t('label.' + i.label))}</div><pre><code>${esc(i.text.slice(0, 6000))}</code></pre></div>`).join('');
        return `<details class="note"><summary><span class="tw">▸</span> ${esc(names)}${turn.items.length > 1 ? ' ×' + turn.items.length : ''} <span class="sz">· ${size}</span></summary>${bodies}</details>`;
      }
      return '<div class="turn asst"><div class="av">✦</div><div class="body">'
        + turn.parts.map((p) => (p.k === 'text' ? md(p.v) : toolCard(p, results[p.id]))).join('') + '</div></div>';
  }
}

export async function view(id) {
  S.cur = id;
  document.body.classList.add('chat');
  draw();
  const chat = $('#chat');
  chat.innerHTML = `<div class="empty">${t('loading')}</div>`;
  const d = await (await fetch('/api/session/' + id)).json();
  if (S.cur !== id) return; // user already opened another session

  const results = {};
  for (const m of d.messages) for (const p of m.parts) if (p.k === 'result') results[p.tid] = p;
  chat.innerHTML = buildTurns(d.messages).map((turn) => renderTurn(turn, results)).join('')
    || `<div class="empty">${t('empty.session')}</div>`;

  const model = (d.messages.find((m) => m.model) || {}).model || '';
  const span = range(d) + ' (' + dur(d.last - d.first) + activeText(d).replace(' · ', ', ') + ')';
  $('#comp').hidden = false;
  $('#ti').innerHTML = `<span class="ico" title="${esc(sourceLabel(d.source))}">${icon(d.source)}</span>${esc(d.title || t('untitled'))}`;
  $('#su').textContent = [d.cwd, model, span, t('messages', { n: d.n })].filter(Boolean).join(' · ');
  $('#dl').hidden = false;
  $('#dl').href = '/api/session/' + id + '?raw=1';
  $('#dl').download = id + '.json';
  S.curCmd = (d.cwd ? `cd "${d.cwd}" && ` : '') + `claude --resume ${id}`;
  $('#cmd').textContent = S.curCmd;
  $('#scroll').scrollTo({ top: 1e9, behavior: 'instant' }); // like a chat: start at the bottom
}

export function route() {
  const id = location.hash.slice(2);
  if (id) { view(id); return; }
  S.cur = null;
  document.body.classList.remove('chat');
  $('#ti').textContent = t('pick.title');
  $('#su').textContent = '';
  $('#dl').hidden = true;
  $('#comp').hidden = true;
  draw();
}
