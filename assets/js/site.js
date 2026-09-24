// Theme toggle, BibTeX panels and publication filters.
(function () {
  var root = document.documentElement;

  // ----- Theme -----
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var current = root.dataset.theme ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  }

  // ----- BibTeX show/hide and copy -----
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-bibtex]");
    if (btn) {
      var panel = btn.closest(".pub-body").querySelector(".bibtex");
      var open = panel.hidden;
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
      return;
    }
    var copy = e.target.closest("[data-copy]");
    if (copy) {
      var text = copy.parentNode.querySelector("pre").textContent.trim();
      var done = function () { copy.textContent = "Copied"; setTimeout(function () { copy.textContent = "Copy"; }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () {});
    }
  });

  // ----- Publication filters -----
  var filters = document.querySelector("[data-filters]");
  if (!filters) return;
  var pubs = Array.prototype.slice.call(document.querySelectorAll(".year-group .pub"));
  var groups = Array.prototype.slice.call(document.querySelectorAll(".year-group"));
  var empty = document.querySelector(".filter-empty");
  var search = filters.querySelector("[data-search]");
  var state = { type: "all", topic: null, q: "" };

  var params = new URLSearchParams(location.search);
  if (params.get("topic")) state.topic = params.get("topic");
  if (params.get("type")) state.type = params.get("type");

  function apply() {
    filters.querySelectorAll("[data-filter-type]").forEach(function (b) {
      b.classList.toggle("is-on", b.dataset.filterType === state.type);
    });
    filters.querySelectorAll("[data-filter-topic]").forEach(function (b) {
      b.classList.toggle("is-on", b.dataset.filterTopic === state.topic);
    });
    var q = state.q.toLowerCase(), shown = 0;
    pubs.forEach(function (p) {
      var ok = (state.type === "all" ||
                (state.type === "selected" ? p.dataset.selected === "true" : p.dataset.type === state.type)) &&
               (!state.topic || (" " + p.dataset.topics + " ").indexOf(" " + state.topic + " ") > -1) &&
               (!q || p.textContent.toLowerCase().indexOf(q) > -1);
      p.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector(".pub:not([hidden])"); });
    if (empty) empty.hidden = shown > 0;
  }

  filters.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.filterType) state.type = b.dataset.filterType;
    if (b.dataset.filterTopic) state.topic = state.topic === b.dataset.filterTopic ? null : b.dataset.filterTopic;
    apply();
  });
  search.addEventListener("input", function () { state.q = search.value.trim(); apply(); });
  apply();
})();
