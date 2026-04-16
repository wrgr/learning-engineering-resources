/**
 * Sticky landmark navigation so readers can jump between major workspace areas without scanning long pages.
 * Scroll position updates which link is highlighted (aria-current).
 */
import { html, useEffect, useRef, useState } from "../lib.js";

const NAV_LINKS = [
  { id: "overview", label: "Overview" },
  { id: "graph", label: "Graph" },
  { id: "resources", label: "Resources" },
  { id: "papers", label: "Papers" },
  { id: "signals", label: "Signals" },
  { id: "docs", label: "Docs" },
  { id: "maintain", label: "Maintain" },
];

const SECTION_IDS = NAV_LINKS.map((item) => item.id);

/**
 * Picks the section id that should read as “current” based on scroll position and sticky nav height.
 * @param {number} navOffsetPx
 * @returns {string}
 */
function computeActiveSectionId(navOffsetPx) {
  const threshold = navOffsetPx + 12;
  const docEl = document.documentElement;
  const docH = docEl.scrollHeight;
  const canScroll = docH > window.innerHeight + 48;
  if (canScroll && window.scrollY + window.innerHeight >= docH - 8) {
    for (let i = SECTION_IDS.length - 1; i >= 0; i -= 1) {
      const id = SECTION_IDS[i];
      if (document.getElementById(id)) return id;
    }
  }
  let active = SECTION_IDS[0];
  for (const id of SECTION_IDS) {
    const el = document.getElementById(id);
    if (!el) continue;
    if (el.getBoundingClientRect().top <= threshold) active = id;
  }
  return active;
}

export function SiteNav() {
  const navRef = useRef(null);
  const [activeId, setActiveId] = useState(SECTION_IDS[0]);

  useEffect(() => {
    let scheduledRaf = 0;

    function navOffset() {
      return navRef.current?.offsetHeight ?? 68;
    }

    function compute() {
      setActiveId(computeActiveSectionId(navOffset()));
    }

    function schedule() {
      if (scheduledRaf) cancelAnimationFrame(scheduledRaf);
      scheduledRaf = requestAnimationFrame(() => {
        scheduledRaf = 0;
        compute();
      });
    }

    function onHashChange() {
      const raw = window.location.hash.replace(/^#/, "");
      if (raw && SECTION_IDS.includes(raw)) setActiveId(raw);
    }

    compute();
    requestAnimationFrame(() => {
      compute();
    });

    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    window.addEventListener("hashchange", onHashChange);

    let resizeObserver = null;
    const el = navRef.current;
    if (el && typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(schedule);
      resizeObserver.observe(el);
    }

    return () => {
      if (scheduledRaf) cancelAnimationFrame(scheduledRaf);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      window.removeEventListener("hashchange", onHashChange);
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, []);

  return html`
    <nav ref=${navRef} className="site-nav" aria-label="Workspace sections">
      <div className="site-nav-inner wrap">
        <a className=${"site-nav-brand" + (activeId === "overview" ? " is-active" : "")} href="#overview">
          Learning Engineering Resources
        </a>
        <ul className="site-nav-links">
          ${NAV_LINKS.map(
            (item) => html`
              <li key=${item.id}>
                <a
                  href=${`#${item.id}`}
                  className=${activeId === item.id ? "is-active" : ""}
                  aria-current=${activeId === item.id ? "location" : undefined}
                >
                  ${item.label}
                </a>
              </li>
            `
          )}
        </ul>
      </div>
    </nav>
  `;
}
