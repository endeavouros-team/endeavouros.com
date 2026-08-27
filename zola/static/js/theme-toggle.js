// Deferred. The button ships with `hidden` so a visitor without JavaScript
// never sees a control that cannot work.
(function () {
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;

  function apply(t) {
    document.documentElement.dataset.theme = t;
    btn.setAttribute("aria-label", "Switch to " + (t === "dark" ? "light" : "dark") + " theme");
    btn.setAttribute("aria-pressed", String(t === "light"));
    try { localStorage.setItem("eos-theme", t); } catch (e) {}
  }

  function current() {
    return document.documentElement.dataset.theme ||
      (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  }

  btn.hidden = false;
  apply(current());
  btn.addEventListener("click", function () {
    apply(current() === "dark" ? "light" : "dark");
  });
})();
