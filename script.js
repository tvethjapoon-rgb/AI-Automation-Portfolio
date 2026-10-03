/* Portfolio interactions: mobile nav, active section highlight, copy-email,
   schematic boot-up animation, footer year. */
(function () {
  "use strict";

  /* ---- Mobile navigation ---- */
  var toggle = document.querySelector(".nav-toggle");
  var navList = document.getElementById("nav-list");

  if (toggle && navList) {
    var setMenu = function (open) {
      navList.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };

    toggle.addEventListener("click", function () {
      setMenu(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Close the menu when a link is chosen
    navList.addEventListener("click", function (event) {
      if (event.target.closest("a")) { setMenu(false); }
    });

    // Close on Escape
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && navList.classList.contains("open")) {
        setMenu(false);
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

    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { setActive(entry.target.id); }
      });
    }, { rootMargin: "-40% 0px -55% 0px" });

    sections.forEach(function (section) { navObserver.observe(section); });
  }

  /* ---- Copy email ---- */
  var copyButton = document.getElementById("copy-email");
  var copyLabel = document.getElementById("copy-label");
  var EMAIL = "tvet.hjapoon@gmail.com";

  if (copyButton && copyLabel) {
    copyButton.addEventListener("click", function () {
      var done = function (ok) {
        copyLabel.textContent = ok ? "copied \u2713" : EMAIL;
        window.setTimeout(function () { copyLabel.textContent = "copy email"; }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(EMAIL).then(function () { done(true); }, function () { done(false); });
      } else { done(false); }
    });
  }

  /* ---- Schematic boot-up line draw ---- */
  var schematic = document.querySelector(".schematic");
  var boot = function () { if (schematic) { schematic.classList.add("boot"); } };

  if (schematic && "IntersectionObserver" in window) {
    var bootObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { boot(); bootObserver.disconnect(); }
      });
    }, { threshold: 0.25 });
    bootObserver.observe(schematic);
  } else { boot(); }

  /* ---- Footer year ---- */
  var year = document.getElementById("year");
  if (year) { year.textContent = String(new Date().getFullYear()); }
})();
