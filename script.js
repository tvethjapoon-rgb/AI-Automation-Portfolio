/* Portfolio interactions: mobile nav, active section highlight, copy-email, reveal. */
(function () {
  "use strict";

  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- Mobile navigation ---- */
  var toggle = document.querySelector(".nav-toggle");
  var navList = document.getElementById("nav-list");

  if (toggle && navList) {
    toggle.addEventListener("click", function () {
      var open = navList.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    // Close the menu when a link is chosen
    navList.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        navList.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      }
    });

    // Close on Escape
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && navList.classList.contains("is-open")) {
        navList.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
        toggle.focus();
      }
    });
  }

  /* ---- Active nav link on scroll ---- */
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav-link[href^='#']"));
  var sections = links
    .map(function (link) { return document.querySelector(link.getAttribute("href")); })
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    var setActive = function (id) {
      links.forEach(function (link) {
        var isActive = link.getAttribute("href") === "#" + id;
        link.classList.toggle("is-active", isActive);
        if (isActive) { link.setAttribute("aria-current", "true"); }
        else { link.removeAttribute("aria-current"); }
      });
    };

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { setActive(entry.target.id); }
      });
    }, { rootMargin: "-40% 0px -55% 0px" });

    sections.forEach(function (section) { observer.observe(section); });
  }

  /* ---- Reveal on scroll ---- */
  var revealTargets = document.querySelectorAll(".case-study, .pipeline-card, .stack-group");
  if (!prefersReducedMotion && "IntersectionObserver" in window && revealTargets.length) {
    revealTargets.forEach(function (el) { el.classList.add("reveal"); });
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealTargets.forEach(function (el) { revealObserver.observe(el); });
  }

  /* ---- Copy email ---- */
  var copyButton = document.getElementById("copy-email");
  var copyLabel = document.getElementById("copy-label");
  var EMAIL = "tvet.hjapoon@gmail.com";

  if (copyButton && copyLabel && navigator.clipboard) {
    copyButton.addEventListener("click", function () {
      navigator.clipboard.writeText(EMAIL).then(function () {
        copyLabel.textContent = "Copied!";
        copyButton.setAttribute("aria-live", "polite");
        window.setTimeout(function () { copyLabel.textContent = "Copy email"; }, 2000);
      }).catch(function () {
        copyLabel.textContent = "Copy failed";
        window.setTimeout(function () { copyLabel.textContent = "Copy email"; }, 2000);
      });
    });
  } else if (copyButton) {
    // No clipboard API: hide the button so it never dead-ends
    copyButton.style.display = "none";
  }

  /* ---- Footer year ---- */
  var year = document.getElementById("year");
  if (year) { year.textContent = String(new Date().getFullYear()); }
})();
