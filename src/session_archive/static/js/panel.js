// Sidebar: drag to resize, double-click to reset, toggle to hide. Persisted per browser.
import { $, store } from './dom.js';

export function initPanel() {
  const root = document.documentElement, handle = $('#rs'), side = $('#side');
  const setWidth = (w) => root.style.setProperty('--sw', Math.max(220, Math.min(640, w)) + 'px');
  const toggle = () => {
    document.body.classList.toggle('collapsed');
    store.set('collapsed', document.body.classList.contains('collapsed') ? '1' : '0');
  };

  if (store.get('sw')) setWidth(+store.get('sw'));
  if (store.get('collapsed') === '1') document.body.classList.add('collapsed');

  $('#tg').onclick = toggle;
  handle.addEventListener('pointerdown', (e) => {
    handle.setPointerCapture(e.pointerId);
    handle.classList.add('drag');
    document.body.classList.add('dragging');
  });
  handle.addEventListener('pointermove', (e) => { if (handle.hasPointerCapture(e.pointerId)) setWidth(e.clientX); });
  handle.addEventListener('pointerup', () => {
    handle.classList.remove('drag');
    document.body.classList.remove('dragging');
    store.set('sw', parseInt(getComputedStyle(side).width, 10));
  });
  handle.addEventListener('dblclick', () => { root.style.removeProperty('--sw'); store.set('sw', ''); });
  addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') { e.preventDefault(); toggle(); }
  });
}
