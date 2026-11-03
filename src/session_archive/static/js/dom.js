// Tiny DOM/string helpers shared by every module.
export const $ = (sel) => document.querySelector(sel);

export const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// localStorage can throw (private mode, blocked site data): never rely on it.
export const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
};
