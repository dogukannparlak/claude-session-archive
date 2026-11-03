// Source icons and labels. Which sources exist, their labels and icons come from the server's
// config (/api/config), so users can add, remove or restyle them without touching this file.
import { esc } from './dom.js';
import { S } from './state.js';
import { lang } from './i18n.js';

const A = 'viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';

// Builtin icons that are image files (the real product logos, see NOTICE.md).
const FILES = { claude: 'claude.svg', obsidian: 'obsidian.svg', vscode: 'vscode.svg' };

// Builtin generic glyphs (inline SVG, follow the theme colour).
const GLYPHS = {
  terminal: '<rect x="1.75" y="2.75" width="12.5" height="10.5" rx="2"/><path d="M4.5 6.5l2 1.5-2 1.5M8 10h3"/>',
  sdk: '<path d="M6 2v3M10 2v3M4.5 5h7v2.5a3.5 3.5 0 0 1-7 0zM8 11v3"/>',
  server: '<rect x="2" y="2.5" width="12" height="4.5" rx="1.2"/><rect x="2" y="9" width="12" height="4.5" rx="1.2"/><path d="M4.5 4.75h.01M4.5 11.25h.01"/>',
  folder: '<path d="M2 4.5a1 1 0 0 1 1-1h3l1.5 1.8H13a1 1 0 0 1 1 1V12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z"/>',
  globe: '<circle cx="8" cy="8" r="6"/><path d="M2 8h12M8 2c2 2 2 10 0 12M8 2c-2 2-2 10 0 12"/>',
  cloud: '<path d="M4.5 12.5a3 3 0 0 1-.4-5.97A4 4 0 0 1 11.9 6.6 2.9 2.9 0 0 1 11.5 12.5z"/>',
  code: '<path d="M5.5 4.5L2 8l3.5 3.5M10.5 4.5L14 8l-3.5 3.5M9 3.5l-2 9"/>',
  bolt: '<path d="M9 1.5L3.5 9h4L7 14.5 12.5 7h-4z"/>',
  other: '<circle cx="8" cy="8" r="6"/><path d="M6.3 6.3a1.8 1.8 0 1 1 2.6 1.6c-.6.3-.9.7-.9 1.3M8 11.6v.1"/>',
};

const FALLBACK = { key: 'other', label: 'other', icon: { builtin: 'other' } };

export const sourceDef = (key) =>
  S.config.sources.find((s) => s.key === key) || S.config.sources.find((s) => s.key === 'other') || FALLBACK;

export const sourceKeys = () => S.config.sources.map((s) => s.key);

// label is text or {language: text}: pick the UI language, then English, then anything.
export function sourceLabel(key) {
  const def = sourceDef(key);
  const label = def.label;
  if (typeof label === 'string') return label;
  return label[lang] || label.en || Object.values(label)[0] || def.key;
}

export function icon(key) {
  const spec = sourceDef(key).icon || { builtin: 'other' };
  if (spec.url) return `<img class="src src-${esc(key)}" src="${esc(spec.url)}" width="15" height="15" alt="">`;
  if (FILES[spec.builtin]) return `<img class="src src-${esc(key)}" src="/icons/${FILES[spec.builtin]}" width="15" height="15" alt="">`;
  return `<svg class="src src-${esc(key)}" ${A}>${GLYPHS[spec.builtin] || GLYPHS.other}</svg>`;
}
