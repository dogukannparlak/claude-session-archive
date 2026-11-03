// One small inline icon per session source. currentColor, so they follow the theme.
// Simple generic glyphs on purpose, not the official product logos.
const A = 'viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';

const PATHS = {
  // Claude Code desktop app: filled sparkle
  desktop: '<path fill="currentColor" stroke="none" d="M8 1l1.6 4.9L14.5 8l-4.9 1.6L8 15l-1.6-5.4L1.5 8l4.9-2.1z"/>',
  // terminal prompt:  >_
  terminal: '<rect x="1.75" y="2.75" width="12.5" height="10.5" rx="2"/><path d="M4.5 6.5l2 1.5-2 1.5M8 10h3"/>',
  // Obsidian vault: faceted gem
  obsidian: '<path d="M8 1.5l4.6 2.9 1.1 5L8 14.5 2.3 9.4l1.1-5z"/><path d="M8 1.5L6 8.2l2 6.3M8 1.5L10 8.2l-2 6.3M3.4 4.4L6 8.2M12.6 4.4L10 8.2"/>',
  // editor extension:  </>
  vscode: '<path d="M5.5 4.5L2 8l3.5 3.5M10.5 4.5L14 8l-3.5 3.5M9 3.5l-2 9"/>',
  // programmatic / SDK: plug
  sdk: '<path d="M6 2v3M10 2v3M4.5 5h7v2.5a3.5 3.5 0 0 1-7 0zM8 11v3"/>',
  other: '<circle cx="8" cy="8" r="6"/><path d="M6.3 6.3a1.8 1.8 0 1 1 2.6 1.6c-.6.3-.9.7-.9 1.3M8 11.6v.1"/>',
};

export const SOURCE_KEYS = Object.keys(PATHS);

export function icon(source) {
  const key = PATHS[source] ? source : 'other';
  return `<svg class="src src-${key}" ${A}>${PATHS[key]}</svg>`;
}
