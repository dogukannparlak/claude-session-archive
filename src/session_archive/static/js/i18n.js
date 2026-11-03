// Two languages, no framework. Add a language by adding a dictionary below.
import { store } from './dom.js';

const DICT = {
  tr: {
    'app.title': 'Oturum Arşivi',
    'search.ph': 'Başlık ve mesajlarda ara…  ( / )',
    'folder.all': 'Tüm klasörler ({n})',
    'count': '{a} / {b} oturum',
    'searching': ' · mesajlar aranıyor…',
    'noresult': 'Sonuç yok',
    'bucket.today': 'Bugün', 'bucket.yesterday': 'Dün', 'bucket.week': 'Son 7 gün',
    'bucket.month': 'Son 30 gün', 'bucket.older': 'Daha eski',
    'pick.title': 'Oturum seç',
    'empty.pick': 'Soldan bir oturum seç.',
    'empty.session': 'Bu oturumda gösterilecek mesaj yok.',
    'loading': 'Yükleniyor…',
    'untitled': '(başlıksız)',
    'messages': '{n} mesaj',
    'matches': '({n} eşleşme)',
    'active': 'aktif {d}',
    'dur.d': 'g', 'dur.h': 'sa', 'dur.m': 'dk', 'dur.lt1': '<1dk',
    'copy': 'Kopyala', 'copied': 'Kopyalandı',
    'more': 'Devamını göster', 'less': 'Daralt',
    'interrupted': '— yarıda kesildi —',
    'note.size': '{c} karakter, sen yazmadın',
    'comp.ph': 'Salt okunur arşiv. Devam etmek için terminalde:',
    'tip.toggle': 'Paneli gizle/göster (Ctrl/⌘+B)',
    'tip.resize': 'Sürükle: genişlik · Çift tık: sıfırla · Ctrl/⌘+B: gizle',
    'tip.lang': 'Language: English',
    'label.task_notification': 'Görev bildirimi',
    'label.peer_message': 'Başka oturum / alt ajan mesajı',
    'label.auto_continue': 'Otomatik devam',
    'label.session_summary': 'Önceki konuşmanın özeti',
    'label.shell_output': 'Kabuk çıktısı (!)',
    'label.local_command_output': 'Yerel komut çıktısı',
    'label.image_info': 'Görsel bilgisi',
    'label.skill_context': 'Skill / ek bağlam (harness ekledi)',
    'label.system_context': 'Sistem / IDE bağlamı',
  },
  en: {
    'app.title': 'Session Archive',
    'search.ph': 'Search titles and messages…  ( / )',
    'folder.all': 'All folders ({n})',
    'count': '{a} / {b} sessions',
    'searching': ' · searching messages…',
    'noresult': 'No results',
    'bucket.today': 'Today', 'bucket.yesterday': 'Yesterday', 'bucket.week': 'Last 7 days',
    'bucket.month': 'Last 30 days', 'bucket.older': 'Older',
    'pick.title': 'Select a session',
    'empty.pick': 'Pick a session on the left.',
    'empty.session': 'No messages to show in this session.',
    'loading': 'Loading…',
    'untitled': '(untitled)',
    'messages': '{n} messages',
    'matches': '({n} matches)',
    'active': 'active {d}',
    'dur.d': 'd', 'dur.h': 'h', 'dur.m': 'm', 'dur.lt1': '<1m',
    'copy': 'Copy', 'copied': 'Copied',
    'more': 'Show more', 'less': 'Show less',
    'interrupted': '— interrupted —',
    'note.size': '{c} characters, not written by you',
    'comp.ph': 'Read-only archive. To continue, run in a terminal:',
    'tip.toggle': 'Hide/show panel (Ctrl/⌘+B)',
    'tip.resize': 'Drag: width · Double-click: reset · Ctrl/⌘+B: hide',
    'tip.lang': 'Dil: Türkçe',
    'label.task_notification': 'Task notification',
    'label.peer_message': 'Message from another session / sub-agent',
    'label.auto_continue': 'Auto-continue',
    'label.session_summary': 'Summary of the previous conversation',
    'label.shell_output': 'Shell output (!)',
    'label.local_command_output': 'Local command output',
    'label.image_info': 'Image info',
    'label.skill_context': 'Skill / extra context (added by the harness)',
    'label.system_context': 'System / IDE context',
  },
};

export const lang = (() => {
  const saved = store.get('lang');
  if (saved && DICT[saved]) return saved;
  return (navigator.language || 'en').toLowerCase().startsWith('tr') ? 'tr' : 'en';
})();

export const locale = lang === 'tr' ? 'tr-TR' : undefined;

export function t(key, vars) {
  let s = (DICT[lang] && DICT[lang][key]) || DICT.en[key] || key;
  for (const k in vars || {}) s = s.split('{' + k + '}').join(vars[k]);
  return s;
}

export function toggleLang() {
  store.set('lang', lang === 'tr' ? 'en' : 'tr');
  location.reload();
}

// Translate static markup: data-i18n (text), data-i18n-ph (placeholder), data-i18n-title (tooltip).
export function applyStatic() {
  document.documentElement.lang = lang;
  document.title = t('app.title');
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  for (const el of document.querySelectorAll('[data-i18n-ph]')) el.placeholder = t(el.dataset.i18nPh);
  for (const el of document.querySelectorAll('[data-i18n-title]')) el.title = t(el.dataset.i18nTitle);
}
