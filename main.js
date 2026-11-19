document.documentElement.classList.add("js");

// Live Sydney time in the hero
(function sydneyClock() {
  const el = document.getElementById("sydney-time");
  if (!el) return;
  const fmt = new Intl.DateTimeFormat("en-AU", {
    timeZone: "Australia/Sydney",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
  const tick = () => {
    const now = new Date();
    el.textContent = fmt.format(now).replace(/\s?([ap])\.?m\.?/i, " $1m").toLowerCase();
    el.setAttribute("datetime", now.toISOString());
  };
  tick();
  setInterval(tick, 15000);
})();

// Person waves when someone arrives, and again on hover or tap
(function waveGreeter() {
  const bot = document.querySelector(".greeter");
  if (!bot) return;
  const wave = () => {
    if (bot.classList.contains("is-waving")) return;
    bot.classList.add("is-waving");
  };
  bot.addEventListener("animationend", (e) => {
    if (e.animationName === "bubble") bot.classList.remove("is-waving");
  });
  bot.addEventListener("mouseenter", wave);
  bot.addEventListener("click", wave);
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    setTimeout(wave, 1150);
  }
})();

// Eyes follow the cursor (or a finger on touch screens)
(function followCursor() {
  const whites = document.querySelectorAll(".greeter__white");
  const pupils = document.querySelectorAll(".greeter__pupil");
  if (!whites.length || whites.length !== pupils.length) return;

  const MAX_X = 4; // how far the iris can travel, in SVG units
  const MAX_Y = 2.2;
  let pointer = null;
  let frame = 0;

  const update = () => {
    frame = 0;
    whites.forEach((white, i) => {
      let dx = 0;
      let dy = 0;
      if (pointer) {
        const r = white.getBoundingClientRect();
        const vx = pointer.x - (r.left + r.width / 2);
        const vy = pointer.y - (r.top + r.height / 2);
        const dist = Math.hypot(vx, vy);
        if (dist > 0) {
          // full travel once the cursor is ~150px away; eased in closer to the face
          const reach = Math.min(1, dist / 150);
          dx = (vx / dist) * MAX_X * reach;
          dy = (vy / dist) * MAX_Y * reach;
        }
      }
      pupils[i].style.transform = `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)`;
    });
  };
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(update);
  };

  window.addEventListener("pointermove", (e) => {
    pointer = { x: e.clientX, y: e.clientY };
    schedule();
  }, { passive: true });
  window.addEventListener("pointerdown", (e) => {
    pointer = { x: e.clientX, y: e.clientY };
    schedule();
  }, { passive: true });
  // keep tracking while the page scrolls under a still cursor
  window.addEventListener("scroll", schedule, { passive: true });
  // look straight ahead again when the cursor leaves the window
  document.documentElement.addEventListener("mouseleave", () => {
    pointer = null;
    schedule();
  });
})();

// Footer year
const year = document.getElementById("year");
if (year) year.textContent = new Date().getFullYear();

// Save as PDF uses the print stylesheet
document.querySelectorAll("[data-print]").forEach((btn) =>
  btn.addEventListener("click", () => window.print())
);

// Top bar border once scrolled
const topbar = document.querySelector(".topbar");
const onScroll = () => topbar && topbar.classList.toggle("is-scrolled", window.scrollY > 8);
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();

// Highlight the nav link for the section in view
const links = new Map(
  [...document.querySelectorAll(".nav a")].map((a) => [a.getAttribute("href").slice(1), a])
);
if ("IntersectionObserver" in window && links.size) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((a) => a.classList.remove("is-active"));
        const link = links.get(entry.target.id);
        if (link) link.classList.add("is-active");
      });
    },
    { rootMargin: "-45% 0px -50% 0px" }
  );
  links.forEach((_, id) => {
    const section = document.getElementById(id);
    if (section) io.observe(section);
  });
}
