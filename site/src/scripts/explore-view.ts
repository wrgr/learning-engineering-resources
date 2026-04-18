/** Client-side logic for the Explore page: filter, grid, and graph views. */

import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceX,
  forceY,
  forceCollide,
} from "d3-force";

// ── Types ──────────────────────────────────────────────────────────────────

interface Resource {
  id: string;
  collection: string;
  title: string;
  format: string;
  url?: string;
  authors?: string;
  year?: number;
  venue?: string;
  summary?: string;
  topics: string[];
  keywords: string[];
  hsi_relevant: boolean;
  cluster_id: number;
}

interface Cluster {
  id: number;
  name: string;
  topics: string[];
  description: string;
}

interface ExploreData {
  resources: Resource[];
  clusters: Cluster[];
  topicNames: Record<string, string>;
  topicLayers: Record<string, string>;
  topicUrls: Record<string, string>;
}

interface FilterState {
  topics: Set<string>;
  hsi: boolean;
  formats: Set<string>;
  clusters: Set<number>;
  yearMin?: number;
  yearMax?: number;
  q: string;
  view: "grid" | "graph";
  group: "cluster" | "topic" | "format" | "collection";
}

// ── Bootstrap ─────────────────────────────────────────────────────────────

const data: ExploreData = JSON.parse(
  document.getElementById("explore-data")!.textContent!,
);

const state: FilterState = parseUrl();

const gridEl = document.getElementById("explore-grid")!;
const graphEl = document.getElementById("explore-graph")!;
const emptyEl = document.getElementById("explore-empty")!;
const countEl = document.getElementById("result-count")!;

// ── URL serialization ─────────────────────────────────────────────────────

function parseUrl(): FilterState {
  const p = new URLSearchParams(window.location.search);
  return {
    topics: new Set((p.get("topics") ?? "").split(",").filter(Boolean)),
    hsi: p.get("hsi") === "1",
    formats: new Set((p.get("format") ?? "").split(",").filter(Boolean)),
    clusters: new Set(
      (p.get("cluster") ?? "").split(",").filter(Boolean).map(Number),
    ),
    yearMin: p.has("year_min") ? Number(p.get("year_min")) : undefined,
    yearMax: p.has("year_max") ? Number(p.get("year_max")) : undefined,
    q: p.get("q") ?? "",
    view: (p.get("view") as "grid" | "graph") ?? "grid",
    group: (p.get("group") as FilterState["group"]) ?? "cluster",
  };
}

function pushUrl(s: FilterState) {
  const p = new URLSearchParams();
  if (s.topics.size) p.set("topics", [...s.topics].join(","));
  if (s.hsi) p.set("hsi", "1");
  if (s.formats.size) p.set("format", [...s.formats].join(","));
  if (s.clusters.size) p.set("cluster", [...s.clusters].join(","));
  if (s.yearMin != null) p.set("year_min", String(s.yearMin));
  if (s.yearMax != null) p.set("year_max", String(s.yearMax));
  if (s.q) p.set("q", s.q);
  if (s.view !== "grid") p.set("view", s.view);
  if (s.group !== "cluster") p.set("group", s.group);
  const qs = p.toString();
  window.history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
}

// ── Filter ────────────────────────────────────────────────────────────────

function applyFilter(s: FilterState): Resource[] {
  const ql = s.q.toLowerCase();
  return data.resources.filter((r) => {
    if (s.topics.size && !r.topics.some((t) => s.topics.has(t))) return false;
    if (s.hsi && !r.hsi_relevant) return false;
    if (s.formats.size && !s.formats.has(r.format)) return false;
    if (s.clusters.size && !s.clusters.has(r.cluster_id)) return false;
    if (s.yearMin != null && r.year != null && r.year < s.yearMin) return false;
    if (s.yearMax != null && r.year != null && r.year > s.yearMax) return false;
    if (ql) {
      const blob = [r.title, r.authors, r.venue, r.summary, ...r.keywords, ...r.topics]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!blob.includes(ql)) return false;
    }
    return true;
  });
}

// ── Grid view ─────────────────────────────────────────────────────────────

const FORMAT_LABELS: Record<string, string> = {
  diagram: "Diagram", framework: "Framework", method: "Method", template: "Template",
  toolkit: "Toolkit", tool: "Tool", platform: "Platform", paper: "Paper", book: "Book",
  article: "Article", report: "Report", post: "Post", essay: "Essay",
  conference: "Conference", workshop: "Workshop", series: "Series", convening: "Convening",
  video: "Video", podcast: "Podcast", keynote: "Keynote", webinar: "Webinar",
  "conference-talk": "Talk", org: "Organization", program: "Program", degree: "Degree",
  person: "Person", institution: "Institution", "study-group": "Study group",
};

function groupKey(r: Resource, group: FilterState["group"]): string {
  if (group === "cluster") return String(r.cluster_id);
  if (group === "topic") return r.topics[0] ?? "__none";
  if (group === "format") return r.format;
  return r.collection;
}

function groupLabel(key: string, group: FilterState["group"]): string {
  if (group === "cluster") {
    const c = data.clusters.find((cl) => String(cl.id) === key);
    return c ? c.name : key;
  }
  if (group === "topic") {
    return key === "__none" ? "No topic" : (data.topicNames[key] ?? key);
  }
  if (group === "format") return FORMAT_LABELS[key] ?? key;
  const labels: Record<string, string> = {
    practice: "Practice", tools: "Tools", "reading-list": "Reading List",
    events: "Events", community: "Community",
  };
  return labels[key] ?? key;
}

function cardHTML(r: Resource): string {
  const fmt = FORMAT_LABELS[r.format] ?? r.format;
  const metaParts = [r.authors, r.venue, r.year].filter(Boolean).join(" · ");
  const titleHTML = r.url
    ? `<a href="${escHtml(r.url)}" target="_blank" rel="noopener" class="xcard-link">${escHtml(r.title)}</a>`
    : escHtml(r.title);
  const summaryHTML = r.summary
    ? `<p class="xcard-summary">${escHtml(truncate(r.summary, 180))}</p>`
    : "";
  const topicChips = r.topics
    .map((t) => {
      const layer = data.topicLayers[t] ?? "";
      const url = data.topicUrls[t] ?? "#";
      return `<a href="${url}" class="chip chip--${layer.toLowerCase()}">${escHtml(data.topicNames[t] ?? t)}</a>`;
    })
    .join("");
  const hsiChip = r.hsi_relevant
    ? `<span class="chip chip--hsi">HSI</span>`
    : "";
  return `<article class="xcard">
  <div class="xcard-format">${escHtml(fmt)}</div>
  <h3 class="xcard-title">${titleHTML}</h3>
  ${metaParts ? `<div class="xcard-meta">${escHtml(metaParts)}</div>` : ""}
  ${summaryHTML}
  <div class="xcard-chips">${topicChips}${hsiChip}</div>
</article>`;
}

function renderGrid(filtered: Resource[], s: FilterState) {
  const groups = new Map<string, Resource[]>();
  for (const r of filtered) {
    const key = groupKey(r, s.group);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(r);
  }

  // Sort groups: clusters by id, topics by layer+code, else alphabetical
  const sortedKeys = [...groups.keys()].sort((a, b) => {
    if (s.group === "cluster") return Number(a) - Number(b);
    return groupLabel(a, s.group).localeCompare(groupLabel(b, s.group));
  });

  let html = "";
  for (const key of sortedKeys) {
    const items = groups.get(key)!;
    const label = groupLabel(key, s.group);
    const clusterDesc = s.group === "cluster"
      ? (data.clusters.find((c) => String(c.id) === key)?.description ?? "")
      : "";
    html += `<section class="xgroup">
  <h2 class="xgroup-heading">${escHtml(label)}
    <span class="xgroup-count">${items.length}</span>
  </h2>
  ${clusterDesc ? `<p class="xgroup-desc">${escHtml(clusterDesc)}</p>` : ""}
  <div class="xcard-grid">${items.map(cardHTML).join("")}</div>
</section>`;
  }
  gridEl.innerHTML = html;
}

// ── Graph view ────────────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  label: string;
  kind: "hub" | "resource";
  color: string;
  r: number;
  resource?: Resource;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: GraphNode | string;
  target: GraphNode | string;
}

const CLUSTER_COLORS = [
  "#7a4e22", "#2c5f6f", "#5a6b4a", "#6b4a7a", "#4a6b5a", "#7a6b4a", "#4a4a7a",
];

const TOPIC_LAYER_COLORS: Record<string, string> = {
  Foundation: "#7a4e22",
  Practice: "#2c5f6f",
  Context: "#5a6b4a",
};

function hubColor(key: string, group: FilterState["group"]): string {
  if (group === "cluster") return CLUSTER_COLORS[Number(key)] ?? "#888";
  if (group === "topic") return TOPIC_LAYER_COLORS[data.topicLayers[key] ?? ""] ?? "#888";
  return "#888";
}

let simActive: ReturnType<typeof forceSimulation> | null = null;

function renderGraph(filtered: Resource[], s: FilterState) {
  if (simActive) { simActive.stop(); simActive = null; }

  const svgEl = graphEl.querySelector("svg") as SVGSVGElement;
  const W = svgEl.clientWidth || 800;
  const H = svgEl.clientHeight || 560;

  // Build hub nodes from groups present in the filtered set
  const groupKeys = new Set(filtered.map((r) => groupKey(r, s.group)));
  const hubs: GraphNode[] = [...groupKeys].map((key) => ({
    id: `hub:${key}`,
    label: groupLabel(key, s.group),
    kind: "hub",
    color: hubColor(key, s.group),
    r: 22,
    x: W / 2 + (Math.random() - 0.5) * 200,
    y: H / 2 + (Math.random() - 0.5) * 100,
  }));

  const hubById = new Map(hubs.map((h) => [h.id, h]));

  // Only show up to 200 resources to keep graph legible; prioritize featured
  const displayed = filtered.slice(0, 200);
  const resNodes: GraphNode[] = displayed.map((r) => ({
    id: r.id,
    label: r.title,
    kind: "resource",
    color: hubColor(groupKey(r, s.group), s.group) + "99",
    r: 5,
    resource: r,
  }));

  const nodes: GraphNode[] = [...hubs, ...resNodes];
  const links: GraphLink[] = resNodes.map((n) => ({
    source: n,
    target: hubById.get(`hub:${groupKey(n.resource!, s.group)}`)!,
  }));

  const sim = forceSimulation<GraphNode>(nodes)
    .force("link", forceLink<GraphNode, GraphLink>(links).id((d) => d.id).distance(60).strength(0.3))
    .force("charge", forceManyBody<GraphNode>().strength((d) => (d.kind === "hub" ? -400 : -30)))
    .force("x", forceX<GraphNode>(W / 2).strength(0.06))
    .force("y", forceY<GraphNode>(H / 2).strength(0.06))
    .force("collide", forceCollide<GraphNode>((d) => d.r + 3));

  sim.tick(200);
  sim.stop();
  simActive = null;

  // Render SVG
  const nodeById = new Map(nodes.map((n) => [n.id, n]));

  let edgeSvg = "";
  for (const lk of links) {
    const src = typeof lk.source === "string" ? nodeById.get(lk.source) : lk.source as GraphNode;
    const tgt = typeof lk.target === "string" ? nodeById.get(lk.target) : lk.target as GraphNode;
    if (!src || !tgt) continue;
    edgeSvg += `<line class="xedge" x1="${src.x!.toFixed(1)}" y1="${src.y!.toFixed(1)}" x2="${tgt.x!.toFixed(1)}" y2="${tgt.y!.toFixed(1)}"/>`;
  }

  let nodeSvg = "";
  for (const n of nodes) {
    const cx = n.x!.toFixed(1);
    const cy = n.y!.toFixed(1);
    if (n.kind === "hub") {
      const labelY = (n.y! + n.r + 14).toFixed(1);
      nodeSvg += `<g class="xhub" data-id="${escAttr(n.id)}" role="button" tabindex="0">
  <circle cx="${cx}" cy="${cy}" r="${n.r}" fill="${n.color}" stroke="${n.color}" stroke-width="2"/>
  <text x="${cx}" y="${labelY}" text-anchor="middle" class="xhub-label">${escHtml(n.label)}</text>
</g>`;
    } else {
      nodeSvg += `<circle class="xresnode" cx="${cx}" cy="${cy}" r="${n.r}"
  fill="${n.color}" stroke="none"
  data-id="${escAttr(n.id)}"
  tabindex="0" role="button"
  aria-label="${escAttr(n.label)}"><title>${escHtml(n.label)}</title></circle>`;
    }
  }

  svgEl.innerHTML = `<g class="xedges">${edgeSvg}</g><g class="xnodes">${nodeSvg}</g>`;

  // Interactions
  const popup = document.getElementById("node-popup")!;

  function hidePopup() { popup.hidden = true; }

  svgEl.querySelectorAll(".xresnode").forEach((el) => {
    el.addEventListener("click", (e) => {
      const id = (el as SVGElement).getAttribute("data-id")!;
      const res = data.resources.find((r) => r.id === id);
      if (!res) return;
      const fmt = FORMAT_LABELS[res.format] ?? res.format;
      const meta = [res.authors, res.venue, res.year].filter(Boolean).join(" · ");
      const titleHTML = res.url
        ? `<a href="${escHtml(res.url)}" target="_blank" rel="noopener">${escHtml(res.title)}</a>`
        : escHtml(res.title);
      popup.innerHTML = `
        <button class="popup-close" aria-label="Close">&times;</button>
        <span class="popup-format">${escHtml(fmt)}</span>
        <h3 class="popup-title">${titleHTML}</h3>
        ${meta ? `<div class="popup-meta">${escHtml(meta)}</div>` : ""}
        ${res.summary ? `<p class="popup-summary">${escHtml(truncate(res.summary, 200))}</p>` : ""}
      `;
      popup.hidden = false;
      popup.querySelector(".popup-close")!.addEventListener("click", hidePopup);
      e.stopPropagation();
    });
  });

  svgEl.querySelector(".xnodes")!.addEventListener("click", (e) => {
    if ((e.target as Element).classList.contains("xresnode")) return;
    hidePopup();
  });
}

// ── Render dispatch ───────────────────────────────────────────────────────

function render(s: FilterState) {
  const filtered = applyFilter(s);
  countEl.textContent = `${filtered.length} of ${data.resources.length} resources`;
  const isEmpty = filtered.length === 0;
  emptyEl.hidden = !isEmpty;

  if (s.view === "graph") {
    gridEl.hidden = true;
    graphEl.hidden = isEmpty;
    if (!isEmpty) renderGraph(filtered, s);
  } else {
    graphEl.hidden = true;
    gridEl.hidden = isEmpty;
    if (!isEmpty) renderGrid(filtered, s);
  }
}

// ── UI wiring ─────────────────────────────────────────────────────────────

function wireControls(s: FilterState) {
  // View toggle
  document.querySelectorAll("[data-view]").forEach((btn) => {
    const v = (btn as HTMLElement).dataset.view as "grid" | "graph";
    btn.classList.toggle("active", s.view === v);
    btn.addEventListener("click", () => {
      s.view = v;
      document.querySelectorAll("[data-view]").forEach((b) =>
        b.classList.toggle("active", (b as HTMLElement).dataset.view === v),
      );
      pushUrl(s);
      render(s);
    });
  });

  // Group-by select
  const groupSel = document.getElementById("group-by") as HTMLSelectElement;
  groupSel.value = s.group;
  groupSel.addEventListener("change", () => {
    s.group = groupSel.value as FilterState["group"];
    pushUrl(s);
    render(s);
  });

  // Topic chips
  document.querySelectorAll("[data-topic]").forEach((chip) => {
    const t = (chip as HTMLElement).dataset.topic!;
    chip.classList.toggle("selected", s.topics.has(t));
    chip.addEventListener("click", () => {
      s.topics.has(t) ? s.topics.delete(t) : s.topics.add(t);
      chip.classList.toggle("selected", s.topics.has(t));
      pushUrl(s);
      render(s);
    });
  });

  // HSI toggle
  const hsiCb = document.getElementById("hsi-toggle") as HTMLInputElement;
  hsiCb.checked = s.hsi;
  hsiCb.addEventListener("change", () => {
    s.hsi = hsiCb.checked;
    pushUrl(s);
    render(s);
  });

  // Format checkboxes
  document.querySelectorAll("[data-format-cb]").forEach((cb) => {
    const fmt = (cb as HTMLInputElement).dataset.formatCb!;
    (cb as HTMLInputElement).checked = s.formats.has(fmt);
    cb.addEventListener("change", () => {
      if ((cb as HTMLInputElement).checked) s.formats.add(fmt);
      else s.formats.delete(fmt);
      pushUrl(s);
      render(s);
    });
  });

  // Year inputs
  const yearMinEl = document.getElementById("year-min") as HTMLInputElement;
  const yearMaxEl = document.getElementById("year-max") as HTMLInputElement;
  if (s.yearMin != null) yearMinEl.value = String(s.yearMin);
  if (s.yearMax != null) yearMaxEl.value = String(s.yearMax);
  function onYear() {
    s.yearMin = yearMinEl.value ? Number(yearMinEl.value) : undefined;
    s.yearMax = yearMaxEl.value ? Number(yearMaxEl.value) : undefined;
    pushUrl(s);
    render(s);
  }
  yearMinEl.addEventListener("change", onYear);
  yearMaxEl.addEventListener("change", onYear);

  // Keyword search
  const qEl = document.getElementById("keyword-search") as HTMLInputElement;
  qEl.value = s.q;
  let debounce: ReturnType<typeof setTimeout>;
  qEl.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      s.q = qEl.value.trim();
      pushUrl(s);
      render(s);
    }, 250);
  });

  // Clear all
  document.getElementById("clear-filters")!.addEventListener("click", () => {
    s.topics.clear();
    s.formats.clear();
    s.clusters.clear();
    s.hsi = false;
    s.yearMin = undefined;
    s.yearMax = undefined;
    s.q = "";
    qEl.value = "";
    yearMinEl.value = "";
    yearMaxEl.value = "";
    hsiCb.checked = false;
    document.querySelectorAll("[data-topic]").forEach((c) => c.classList.remove("selected"));
    document.querySelectorAll("[data-format-cb]").forEach((c) => { (c as HTMLInputElement).checked = false; });
    pushUrl(s);
    render(s);
  });

  // Copy link
  document.getElementById("copy-link")!.addEventListener("click", () => {
    navigator.clipboard.writeText(window.location.href).catch(() => {});
    const btn = document.getElementById("copy-link")!;
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy link"; }, 1500);
  });
}

// ── Helpers ────────────────────────────────────────────────────────────────

function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escAttr(s: string): string {
  return escHtml(s);
}

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max - 1) + "\u2026" : s;
}

// ── Init ───────────────────────────────────────────────────────────────────

wireControls(state);
render(state);
