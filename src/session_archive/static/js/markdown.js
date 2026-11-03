// A deliberately small Markdown renderer: headings, lists, quotes, tables, fenced code,
// bold/italic/inline code and http(s) links. Everything is HTML-escaped first.
import { esc } from './dom.js';
import { t } from './i18n.js';

const FENCE = '`'.repeat(3);

function inline(s) {
  return s.split(/(`[^`\n]+`)/).map((p, i) => {
    if (i % 2) return '<code>' + esc(p.slice(1, -1)) + '</code>';
    p = esc(p);
    p = p.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    p = p.replace(/(^|[^*\w])\*([^*\n]+)\*(?!\w)/g, '$1<em>$2</em>');
    p = p.replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    return p;
  }).join('');
}

function blocks(text) {
  const L = text.split('\n'), out = [];
  let i = 0;
  const isTable = (a, b) => a && b && a.includes('|') && /^\s*\|?[\s:|-]+\|?\s*$/.test(b) && b.includes('-');
  const listRe = /^\s*([-*]|\d+\.)\s+/;
  while (i < L.length) {
    const l = L[i];
    if (!l.trim()) { i++; continue; }
    let m;
    if ((m = l.match(/^(#{1,4})\s+(.*)$/))) { out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); i++; continue; }
    if (/^\s*([-*_])\1\1+\s*$/.test(l)) { out.push('<hr>'); i++; continue; }
    if (isTable(l, L[i + 1])) {
      const row = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
      let h = '<table><thead><tr>' + row(l).map((c) => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>';
      i += 2;
      while (i < L.length && L[i].includes('|') && L[i].trim()) { h += '<tr>' + row(L[i]).map((c) => `<td>${inline(c)}</td>`).join('') + '</tr>'; i++; }
      out.push(h + '</tbody></table>');
      continue;
    }
    if (/^\s*>/.test(l)) {
      const q = [];
      while (i < L.length && /^\s*>/.test(L[i])) q.push(L[i++].replace(/^\s*>\s?/, ''));
      out.push('<blockquote>' + blocks(q.join('\n')) + '</blockquote>');
      continue;
    }
    if (listRe.test(l)) {
      const ordered = /^\s*\d+\./.test(l), items = [];
      while (i < L.length && listRe.test(L[i])) items.push(L[i++].replace(listRe, ''));
      const tag = ordered ? 'ol' : 'ul';
      out.push(`<${tag}>` + items.map((x) => `<li>${inline(x)}</li>`).join('') + `</${tag}>`);
      continue;
    }
    const para = [];
    while (i < L.length && L[i].trim() && !/^(#{1,4}\s|\s*>|\s*([-*]|\d+\.)\s+)/.test(L[i]) && !isTable(L[i], L[i + 1])) para.push(L[i++]);
    out.push('<p>' + para.map(inline).join('<br>') + '</p>');
  }
  return out.join('');
}

export function codeBlock(lang, code) {
  return `<pre><div class="ch"><span>${esc(lang || 'text')}</span><button data-copy>${t('copy')}</button></div><code>${esc(code.replace(/\n$/, ''))}</code></pre>`;
}

export function md(src) {
  let out = '', pos = 0, m;
  const re = new RegExp(FENCE + '([\\w+-]*)\\n([\\s\\S]*?)(?:' + FENCE + '|$)', 'g');
  while ((m = re.exec(src))) {
    out += blocks(src.slice(pos, m.index)) + codeBlock(m[1], m[2]);
    pos = re.lastIndex;
    if (m[0].length === 0) re.lastIndex++;
  }
  return out + blocks(src.slice(pos));
}
