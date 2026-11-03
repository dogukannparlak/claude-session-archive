// One small icon per session source.
const A = 'viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';

// Brand sources use the real logos as SVG files (see NOTICE.md); the rest are generic glyphs.
const BRAND = { desktop: 'claude', obsidian: 'obsidian', vscode: 'vscode' };

const PATHS = {
  // terminal prompt:  >_
  terminal: '<rect x="1.75" y="2.75" width="12.5" height="10.5" rx="2"/><path d="M4.5 6.5l2 1.5-2 1.5M8 10h3"/>',
  // programmatic / SDK: plug
  sdk: '<path d="M6 2v3M10 2v3M4.5 5h7v2.5a3.5 3.5 0 0 1-7 0zM8 11v3"/>',
  other: '<circle cx="8" cy="8" r="6"/><path d="M6.3 6.3a1.8 1.8 0 1 1 2.6 1.6c-.6.3-.9.7-.9 1.3M8 11.6v.1"/>',
};

export const SOURCE_KEYS = ['desktop', 'terminal', 'obsidian', 'vscode', 'sdk', 'other'];

export function icon(source) {
  if (BRAND[source]) {
    return `<img class="src src-${source}" src="/icons/${BRAND[source]}.svg" width="15" height="15" alt="">`;
  }
  const key = PATHS[source] ? source : 'other';
  return `<svg class="src src-${key}" ${A}>${PATHS[key]}</svg>`;
}
