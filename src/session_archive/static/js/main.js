// Entry point: wires modules together.
import { $ } from './dom.js';
import { S } from './state.js';
import { applyStatic, t, toggleLang } from './i18n.js';
import { buildFolders, buildSources, draw, onSearch } from './list.js';
import { route } from './chat.js';
import { initPanel } from './panel.js';
import { initTheme } from './theme.js';

applyStatic();
initTheme();
initPanel();

function flash(button, key, ms) {
  button.textContent = t('copied');
  setTimeout(() => { button.textContent = t(key); }, ms);
}

document.addEventListener('click', (e) => {
  const more = e.target.closest('[data-more]');
  if (more) {
    const bubble = more.closest('.bub');
    bubble.classList.toggle('open');
    more.textContent = t(bubble.classList.contains('open') ? 'less' : 'more');
    return;
  }
  const copy = e.target.closest('[data-copy]');
  if (copy) {
    navigator.clipboard.writeText(copy.closest('pre').querySelector('code').textContent);
    flash(copy, 'copy', 1200);
  }
});

$('#copy').onclick = (e) => { navigator.clipboard.writeText(S.curCmd); flash(e.target, 'copy', 1400); };
$('#lang').onclick = toggleLang;
$('#q').oninput = onSearch;
$('#fold').onchange = draw;
$('#srcf').onchange = draw;

addEventListener('keydown', (e) => {
  const q = $('#q');
  if (e.key === '/' && document.activeElement !== q) {
    e.preventDefault();
    document.body.classList.remove('chat');
    q.focus();
  } else if (e.key === 'Escape') {
    q.blur();
  } else if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && document.activeElement === q) {
    e.preventDefault();
    const items = [...document.querySelectorAll('.item')];
    if (!items.length) return;
    let i = items.findIndex((x) => x.dataset.id === S.cur);
    i = Math.max(0, Math.min(items.length - 1, i + (e.key === 'ArrowDown' ? 1 : -1)));
    location.hash = '#/' + items[i].dataset.id;
    items[i].scrollIntoView({ block: 'nearest' });
  }
});

addEventListener('hashchange', route);
Promise.all([
  fetch('/api/config').then((r) => r.json()).catch(() => ({ sources: [] })), // icons fall back to "other"
  fetch('/api/sessions').then((r) => r.json()),
]).then(([config, sessions]) => {
  S.config = config;
  S.all = sessions;
  buildFolders();
  buildSources();
  route();
});
