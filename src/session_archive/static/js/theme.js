// Theme button: cycles auto (follow the OS) -> light -> dark -> auto. Saved per browser.
import { $, store } from './dom.js';
import { t } from './i18n.js';

const ORDER = ['auto', 'light', 'dark'];
const A = 'viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';
const ICONS = {
  // half-filled circle: follow the system
  auto: `<svg ${A}><circle cx="8" cy="8" r="5.5"/><path d="M8 2.5v11a5.5 5.5 0 0 0 0-11z" fill="currentColor" stroke="none"/></svg>`,
  sun: `<svg ${A}><circle cx="8" cy="8" r="2.8"/><path d="M8 1.5v1.6M8 12.9v1.6M1.5 8h1.6M12.9 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1"/></svg>`,
  moon: `<svg ${A}><path d="M13.2 9.6A5.7 5.7 0 0 1 6.4 2.8a5.7 5.7 0 1 0 6.8 6.8z"/></svg>`,
};

const current = () => { const v = store.get('theme'); return ORDER.includes(v) ? v : 'auto'; };

function apply(mode) {
  if (mode === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', mode);
  const button = $('#theme');
  button.innerHTML = mode === 'auto' ? ICONS.auto : mode === 'light' ? ICONS.sun : ICONS.moon;
  button.title = t('tip.theme') + ': ' + t('theme.' + mode);
}

export function initTheme() {
  apply(current());
  $('#theme').onclick = () => {
    const next = ORDER[(ORDER.indexOf(current()) + 1) % ORDER.length];
    store.set('theme', next);
    apply(next);
  };
}
