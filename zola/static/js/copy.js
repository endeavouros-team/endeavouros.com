// Progressive enhancement for the checksum and fingerprint fields.
(function () {
  if (!navigator.clipboard) return;
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.hidden = false;
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-copy"));
      if (!target) return;
      navigator.clipboard.writeText(target.textContent.trim()).then(function () {
        var live = btn.parentNode.querySelector("[data-copy-status]");
        if (live) { live.textContent = "Copied"; setTimeout(function () { live.textContent = ""; }, 2000); }
      });
    });
  });
})();
