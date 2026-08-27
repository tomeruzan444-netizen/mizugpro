/* מיזוג פרו — site behaviour. No dependencies.
   init() is idempotent so a client-side route swap can re-run it. */
(function () {
  "use strict";

  var d = document;
  var scrollBound = false;

  function headerOffset() {
    return parseInt(getComputedStyle(d.documentElement)
      .getPropertyValue("--header-h"), 10) || 76;
  }

  /* window-level listeners are registered once and always read the live DOM */
  function bindScroll() {
    if (scrollBound) return;
    scrollBound = true;

    var spyState = { heads: [], links: [] };
    window.__mizugSpy = spyState;

    window.addEventListener("scroll", function () {
      var header = d.querySelector(".header");
      if (header) header.classList.toggle("is-stuck", window.scrollY > 8);

      var toTop = d.querySelector(".totop");
      if (toTop) toTop.classList.toggle("is-visible", window.scrollY > 700);

      if (spyState.heads.length) {
        var top = window.scrollY + headerOffset() + 40;
        var active = 0;
        spyState.heads.forEach(function (h, i) { if (h.offsetTop <= top) active = i; });
        spyState.links.forEach(function (a, i) { a.classList.toggle("is-active", i === active); });
      }
    }, { passive: true });

    d.addEventListener("keydown", function (e) {
      var drawer = d.querySelector(".drawer.is-open");
      if (e.key === "Escape" && drawer) closeDrawer(drawer);
    });
  }

  function closeDrawer(drawer) {
    drawer.classList.remove("is-open");
    var burger = d.querySelector(".burger");
    if (burger) { burger.setAttribute("aria-expanded", "false"); burger.focus(); }
    d.documentElement.style.overflow = "";
  }

  function once(el, event, handler) {
    if (!el || el.dataset.bound === event) return;
    el.dataset.bound = event;
    el.addEventListener(event, handler);
  }

  function init() {
    bindScroll();
    initA11y();
    initConsent();

    /* ---- mobile drawer ------------------------------------------------- */
    var burger = d.querySelector(".burger");
    var drawer = d.querySelector(".drawer");
    if (burger && drawer) {
      once(burger, "click", function () {
        var open = !drawer.classList.contains("is-open");
        drawer.classList.toggle("is-open", open);
        burger.setAttribute("aria-expanded", open ? "true" : "false");
        d.documentElement.style.overflow = open ? "hidden" : "";
        if (open) {
          var first = drawer.querySelector("a, button");
          if (first) first.focus();
        }
      });
      once(drawer, "click", function (e) {
        if (e.target === drawer || e.target.closest(".drawer__close") || e.target.closest("a")) {
          closeDrawer(drawer);
        }
      });
    }

    /* ---- table of contents: build + scroll spy -------------------------- */
    var toc = d.querySelector("[data-toc]");
    var prose = d.querySelector(".prose");
    var spyState = window.__mizugSpy || {};
    spyState.heads = [];
    spyState.links = [];

    if (toc && prose) {
      var heads = [].slice.call(prose.querySelectorAll(":scope > h2"));
      if (heads.length < 2) {
        var shell = toc.closest(".toc");
        if (shell) shell.remove();
      } else {
        var list = toc.tagName === "OL" ? toc : toc.querySelector("ol");
        list.innerHTML = "";
        heads.forEach(function (h, i) {
          if (!h.id) h.id = "sec-" + (i + 1);
          var li = d.createElement("li");
          var a = d.createElement("a");
          a.href = "#" + h.id;
          a.textContent = h.textContent.trim();
          li.appendChild(a);
          list.appendChild(li);
        });
        spyState.heads = heads;
        spyState.links = [].slice.call(list.querySelectorAll("a"));
      }
    }

    /* ---- FAQ: one open at a time inside the same group ------------------ */
    d.querySelectorAll(".faq").forEach(function (group) {
      group.querySelectorAll("details").forEach(function (item) {
        once(item, "toggle", function () {
          if (!item.open) return;
          group.querySelectorAll("details[open]").forEach(function (other) {
            if (other !== item) other.open = false;
          });
        });
      });
    });

    /* ---- back to top ---------------------------------------------------- */
    once(d.querySelector(".totop"), "click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    /* ---- lead form: light client-side phone check ------------------------ */
    d.querySelectorAll("[data-started]").forEach(function (input) {
      if (!input.value) input.value = Math.floor(Date.now() / 1000);
    });
    d.querySelectorAll("form[data-lead]").forEach(function (form) {
      once(form, "submit", function (e) {
        var phone = form.querySelector('[name="phone"]');
        if (phone && !/^0\d[\d\-\s]{7,}$/.test(phone.value.trim())) {
          e.preventDefault();
          phone.setCustomValidity("נא להזין מספר טלפון תקין");
          phone.reportValidity();
          setTimeout(function () { phone.setCustomValidity(""); }, 2500);
        }
      });
    });
  }

  /* ---- accessibility toolbar ------------------------------------------- */
  var A11Y_KEY = "mizugpro:a11y";
  var TOGGLES = ["keyboard", "noanim", "contrast", "readable", "marktitles", "underline"];
  var MIN_STEP = -2, MAX_STEP = 4;

  function readState() {
    try {
      return JSON.parse(localStorage.getItem(A11Y_KEY)) || { on: [], step: 0 };
    } catch (e) {
      return { on: [], step: 0 };
    }
  }

  function saveState(state) {
    try { localStorage.setItem(A11Y_KEY, JSON.stringify(state)); } catch (e) {}
  }

  function applyState(state) {
    var root = d.documentElement;
    TOGGLES.forEach(function (name) {
      root.classList.toggle("a11y-" + name, state.on.indexOf(name) !== -1);
    });
    root.style.fontSize = state.step ? (100 + state.step * 10) + "%" : "";
    d.querySelectorAll("[data-a11y]").forEach(function (btn) {
      var key = btn.getAttribute("data-a11y");
      if (TOGGLES.indexOf(key) !== -1) {
        btn.setAttribute("aria-pressed", state.on.indexOf(key) !== -1 ? "true" : "false");
      }
    });
    var label = d.getElementById("a11y-scale-value");
    if (label) label.textContent = (100 + state.step * 10) + "%";
  }

  function initA11y() {
    var state = readState();
    applyState(state);

    var openBtn = d.getElementById("a11y-open");
    var panel = d.getElementById("a11y-panel");
    var closeBtn = d.getElementById("a11y-close");
    if (!openBtn || !panel) return;

    var setOpen = function (open) {
      panel.hidden = !open;
      openBtn.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) {
        var first = panel.querySelector("button");
        if (first) first.focus();
      } else {
        openBtn.focus();
      }
    };

    once(openBtn, "click", function () { setOpen(panel.hidden); });
    once(closeBtn, "click", function () { setOpen(false); });

    once(panel, "click", function (e) {
      var btn = e.target.closest("[data-a11y]");
      if (!btn) return;
      var key = btn.getAttribute("data-a11y");

      if (key === "reset") {
        state = { on: [], step: 0 };
      } else if (key === "font-up") {
        state.step = Math.min(MAX_STEP, state.step + 1);
      } else if (key === "font-down") {
        state.step = Math.max(MIN_STEP, state.step - 1);
      } else {
        var at = state.on.indexOf(key);
        if (at === -1) state.on.push(key); else state.on.splice(at, 1);
      }
      saveState(state);
      applyState(state);
    });

    d.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) setOpen(false);
    });
    d.addEventListener("click", function (e) {
      if (panel.hidden) return;
      if (!panel.contains(e.target) && !openBtn.contains(e.target)) setOpen(false);
    });
  }

  /* ---- cookie notice ---------------------------------------------------- */
  function initConsent() {
    var bar = d.getElementById("consent");
    if (!bar) return;
    var KEY = "mizugpro:consent";
    var stored = null;
    try { stored = localStorage.getItem(KEY); } catch (e) {}

    if (!stored) bar.hidden = false;

    once(bar, "click", function (e) {
      var btn = e.target.closest("[data-consent]");
      if (!btn) return;
      var choice = btn.getAttribute("data-consent");
      if (choice !== "close") {
        try { localStorage.setItem(KEY, choice); } catch (err) {}
        // let Tag Manager decide what may fire, rather than deciding here
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({ event: "cookie_consent", cookie_consent: choice });
      }
      bar.hidden = true;
    });
  }

  window.MizugPro = { init: init };
  if (d.readyState === "loading") d.addEventListener("DOMContentLoaded", init);
  else init();
})();
