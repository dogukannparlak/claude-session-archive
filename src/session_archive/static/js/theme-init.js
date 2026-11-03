// Classic (non-module) script loaded in <head>: applies the saved theme before first paint,
// so a forced light/dark choice does not flash the OS theme. Must stay in sync with theme.js.
(function () {
  try {
    var t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
  } catch (e) { /* storage blocked: follow the OS theme */ }
})();
