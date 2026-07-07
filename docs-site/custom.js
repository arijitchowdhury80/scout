// Keep navigation to the main Scout site in the SAME tab (Mintlify opens
// external links in a new tab by default, which fragments the experience).
(function () {
  function sameTab() {
    document.querySelectorAll('a[href^="https://scout.chowmes.com"]').forEach(function (a) {
      a.setAttribute("target", "_self");
      a.removeAttribute("rel");
    });
  }
  sameTab();
  // Re-apply on client-side navigation (Mintlify is a SPA).
  new MutationObserver(sameTab).observe(document.body, { childList: true, subtree: true });
})();
