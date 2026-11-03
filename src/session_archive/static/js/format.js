// Number, date and duration formatting.
import { locale, t } from './i18n.js';

export const dur = (sec) => {
  sec = Math.max(0, Math.round(sec));
  const d = Math.floor(sec / 86400), h = Math.floor((sec % 86400) / 3600), m = Math.floor((sec % 3600) / 60);
  if (d) return d + t('dur.d') + (h ? ' ' + h + t('dur.h') : '');
  if (h) return h + t('dur.h') + (m ? ' ' + m + t('dur.m') : '');
  return m ? m + t('dur.m') : t('dur.lt1');
};

const dm = (ts) => new Date(ts * 1000).toLocaleString(locale, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
const hm = (ts) => new Date(ts * 1000).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
const sameDay = (a, b) => new Date(a * 1000).toDateString() === new Date(b * 1000).toDateString();

// "3 Nov 21:22 → 21:23" within a day, "3 Nov 21:22 → 5 Nov 09:10" across days.
export const range = (s) => (sameDay(s.first, s.last) ? `${dm(s.first)} → ${hm(s.last)}` : `${dm(s.first)} → ${dm(s.last)}`);

export const fsz = (b) => (b >= 1e6 ? (b / 1e6).toFixed(1) + 'MB' : Math.round(b / 1e3) + 'KB');
export const base = (p) => (p || '').split('/').filter(Boolean).pop() || '—';
export const activeText = (s) => (s.active >= 60 ? ' · ' + t('active', { d: dur(s.active) }) : '');
export const fullDate = (iso) => (iso ? new Date(iso).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' }) : '');

export function bucket(ts) {
  const day = 86400000, now = new Date(), d = new Date(ts * 1000);
  const sod = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diff = (sod(now) - sod(d)) / day;
  return t(diff <= 0 ? 'bucket.today' : diff <= 1 ? 'bucket.yesterday' : diff <= 7 ? 'bucket.week' : diff <= 30 ? 'bucket.month' : 'bucket.older');
}
