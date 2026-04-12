// citation_tree.js — Force-directed D3 citation graph for MSKB.
//
// Adapts the approach from learning-engineering-resources/app/components/GraphCanvas.js:
// * SVG height is set by CSS (not by JS pixel values), so browser zoom and
//   media queries work correctly on mobile.
// * D3 zoom/pan with scaleExtent so pinch-zoom and scroll-zoom work at any
//   device zoom level without breaking layout.
// * Phase-1 / Phase-2 split: the force simulation only restarts when the
//   underlying data changes; search/select/hover only trigger a visual update.
// * Touch-tap fallback: on coarse-pointer devices a tap near a node selects it.
// * Auto-fit-to-view: after the simulation settles the camera zooms to show
//   the entire graph with breathing room. "Reset view" repeats the fit.
(() => {
  "use strict";

  const DATA_URL = "../assets/lineage_data.json";
  const d3 = window.d3;

  if (typeof d3 === "undefined") {
    console.error("citation_tree.js: D3 not available on window.d3");
    return;
  }

  // ── Category metadata ─────────────────────────────────────────────────────
  const CAT_COLORS = {
    pathogenesis_and_immunology:        "#1f77b4",
    imaging_and_biomarkers:             "#17a2b8",
    clinical_trials_and_therapeutics:   "#d62728",
    clinical_care_and_management:       "#2ca02c",
    epidemiology_and_population_health: "#9467bd",
    unknown:                            "#aaaaaa",
  };

  const CAT_LABELS = {
    pathogenesis_and_immunology:        "Pathogenesis & Immunology",
    imaging_and_biomarkers:             "Imaging & Biomarkers",
    clinical_trials_and_therapeutics:   "Therapeutics",
    clinical_care_and_management:       "Clinical Care",
    epidemiology_and_population_health: "Epidemiology",
    unknown:                            "Other",
  };

  // ── Mutable state ─────────────────────────────────────────────────────────
  let rawData = null;
  let activeCategories = new Set(Object.keys(CAT_COLORS));
  let importanceThreshold = 5.2;

  // Stable refs shared across phases without restarting the simulation.
  const stateRef = { search: "", selectedId: null, hoveredId: null };

  // D3 selection refs — set in Phase 1, read in Phase 2.
  let linkSelRef  = null;
  let nodeSelRef  = null;
  let labelSelRef = null;
  let neighborRef = null; // Map<id, Set<id>>
  let applyRef    = null; // () => void
  let fitRef      = null; // () => void  — fit-to-view function

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const svgEl          = document.getElementById("ct-graph-canvas");
  const countEl        = document.getElementById("ct-count");
  const thresholdEl    = document.getElementById("ct-threshold");
  const thresholdValEl = document.getElementById("ct-threshold-val");
  const searchEl       = document.getElementById("ct-search");
  const resetBtn       = document.getElementById("ct-reset");
  const pillsEl        = document.getElementById("ct-category-pills");
  const detailEl       = document.getElementById("ct-detail");

  // ── Pure helpers ──────────────────────────────────────────────────────────

  function esc(text) {
    return String(text || "").replace(/[&<>"']/g, (ch) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch])
    );
  }

  /** Log-scaled radius: 4–13 px based on cited_by_count. */
  function nodeRadius(n) {
    return 4 + Math.min(9, Math.log2(1 + (n.cited_by_count || 0)) * 1.1);
  }

  function nodeColor(n) {
    return CAT_COLORS[n.category] ?? "#aaaaaa";
  }

  /** Short label: surname + year, shown only for the most important papers. */
  function nodeLabel(n) {
    if (n.first_author) {
      const surname = n.first_author.trim().split(/\s+/).pop();
      return n.year ? `${surname} ${n.year}` : surname;
    }
    const t = String(n.title || "");
    return t.length > 22 ? t.slice(0, 21) + "\u2026" : t;
  }

  // ── Category pills ────────────────────────────────────────────────────────

  function buildPills() {
    if (!pillsEl) return;
    pillsEl.innerHTML = "";

    function makeBtn(cat, label, color) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ct-pill is-active";
      btn.dataset.cat = cat;
      if (color) btn.style.setProperty("--ct-pill-color", color);
      btn.textContent = label;
      btn.addEventListener("click", () => {
        if (cat === "all") {
          activeCategories = new Set(Object.keys(CAT_COLORS));
        } else if (activeCategories.has(cat)) {
          activeCategories.delete(cat);
        } else {
          activeCategories.add(cat);
        }
        syncPills();
        rebuildGraph();
      });
      pillsEl.appendChild(btn);
    }

    makeBtn("all", "All", null);
    Object.entries(CAT_LABELS).forEach(([cat, label]) =>
      makeBtn(cat, label, CAT_COLORS[cat])
    );
  }

  function syncPills() {
    if (!pillsEl) return;
    const allActive = activeCategories.size === Object.keys(CAT_COLORS).length;
    pillsEl.querySelectorAll("[data-cat]").forEach((btn) => {
      const cat = btn.dataset.cat;
      btn.classList.toggle(
        "is-active",
        cat === "all" ? allActive : activeCategories.has(cat)
      );
    });
  }

  // ── Data filtering ────────────────────────────────────────────────────────

  function filteredData() {
    if (!rawData) return { nodes: [], links: [] };
    const nodes = rawData.nodes.filter(
      (n) =>
        activeCategories.has(n.category || "unknown") &&
        (n.importance_score || 0) >= importanceThreshold
    );
    const ids = new Set(nodes.map((n) => n.id));
    const links = rawData.links.filter(
      (l) => ids.has(l.source) && ids.has(l.target)
    );
    return { nodes, links };
  }

  // ── Phase 1: build force simulation ──────────────────────────────────────
  // Re-runs only when data topology changes (filter, threshold, category).

  function rebuildGraph() {
    if (!svgEl || !rawData) return;

    const { nodes, links } = filteredData();

    if (countEl) {
      countEl.textContent = `${nodes.length} papers \u00b7 ${links.length} links`;
    }

    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();
    applyRef = fitRef = null;
    linkSelRef = nodeSelRef = labelSelRef = neighborRef = null;

    if (!nodes.length) {
      svg
        .append("text")
        .attr("x", "50%").attr("y", "50%")
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("fill", "#6b7280").attr("font-size", 13)
        .text(
          "No papers match the filters \u2014 try lowering the threshold or enabling more categories."
        );
      return;
    }

    // Read height/width from CSS — no hardcoded SVG attributes.
    const rect   = svgEl.getBoundingClientRect();
    const width  = rect.width  || 900;
    const height = rect.height || 600;

    const zoomGroup = svg.append("g").attr("class", "ct-zoom-root");

    // Spread nodes across the canvas initially so the simulation
    // doesn't start as a collapsed hairball at (width/2, height/2).
    // Use a Fibonacci-spiral to give each node a unique starting position.
    const phi = Math.PI * (3 - Math.sqrt(5));
    const simNodes = nodes.map((n, i) => {
      const r   = Math.sqrt(i / nodes.length) * Math.min(width, height) * 0.42;
      const ang = i * phi;
      return {
        ...n,
        x: width  / 2 + r * Math.cos(ang),
        y: height / 2 + r * Math.sin(ang),
      };
    });

    const simLinks = links.map((e) => ({
      source: String(e.source),
      target: String(e.target),
    }));

    // Build adjacency index before D3 replaces string ids with objects.
    const neighborSet = new Map(simNodes.map((n) => [n.id, new Set()]));
    for (const edge of simLinks) {
      const src = String(edge.source);
      const tgt = String(edge.target);
      if (neighborSet.has(src)) neighborSet.get(src).add(tgt);
      if (neighborSet.has(tgt)) neighborSet.get(tgt).add(src);
    }
    neighborRef = neighborSet;

    // ── Link layer ────────────────────────────────────────────────────────
    const linkSel = zoomGroup
      .append("g").attr("class", "ct-links")
      .selectAll("line")
      .data(simLinks)
      .join("line")
      .attr("stroke-width", 0.9);
    linkSelRef = linkSel;

    // ── Node layer ────────────────────────────────────────────────────────
    const nodeSel = zoomGroup
      .append("g").attr("class", "ct-nodes")
      .selectAll("circle")
      .data(simNodes)
      .join("circle")
      .attr("r", nodeRadius)
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.4)
      .attr("cursor", "pointer")
      .on("click", (_evt, n) => {
        stateRef.selectedId = stateRef.selectedId === n.id ? null : n.id;
        applyRef?.();
        renderDetail(stateRef.selectedId ? n : null);
      })
      .on("mouseenter", (_evt, n) => {
        stateRef.hoveredId = n.id;
        applyRef?.();
      })
      .on("mouseleave", () => {
        stateRef.hoveredId = null;
        applyRef?.();
      });

    nodeSel.append("title").text((n) => n.title);
    nodeSelRef = nodeSel;

    // ── Label layer — only the most important papers, to stay readable ─────
    const labelSel = zoomGroup
      .append("g").attr("class", "ct-labels")
      .selectAll("text")
      .data(simNodes.filter((n) => n.importance_score >= 5.5 || n.generation === 0))
      .join("text")
      .attr("font-size", 9)
      .attr("fill", "#0f172a")
      .attr("paint-order", "stroke")
      .attr("stroke", "rgba(255,255,255,0.82)")
      .attr("stroke-width", 2)
      .attr("pointer-events", "none")
      .text(nodeLabel);
    labelSelRef = labelSel;

    // ── Fit-to-view helper ────────────────────────────────────────────────
    // Computes the bounding box of all settled node positions and applies a
    // zoom transform so the whole graph fills the canvas with padding.
    let zoomBehavior; // assigned after zoom is set up below

    function fitToView(animated) {
      if (!simNodes.length) return;
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (const n of simNodes) {
        const r = nodeRadius(n);
        x0 = Math.min(x0, n.x - r);
        x1 = Math.max(x1, n.x + r);
        y0 = Math.min(y0, n.y - r);
        y1 = Math.max(y1, n.y + r);
      }
      const PAD = 40;
      const dx = x1 - x0 + PAD * 2;
      const dy = y1 - y0 + PAD * 2;
      // Scale so the graph fits; cap at 1 so we never zoom in beyond native size.
      const scale = Math.min(width / dx, height / dy, 1);
      const tx = width  / 2 - scale * ((x0 + x1) / 2);
      const ty = height / 2 - scale * ((y0 + y1) / 2);
      const t  = d3.zoomIdentity.translate(tx, ty).scale(scale);
      if (animated) {
        svg.transition().duration(500).call(zoomBehavior.transform, t);
      } else {
        svg.call(zoomBehavior.transform, t);
      }
    }

    fitRef = () => fitToView(true);

    // ── Force simulation ──────────────────────────────────────────────────
    // Charge strength of -280 gives plenty of breathing room between papers.
    // Link distance of 85 keeps connected clusters visible but not tangled.
    // alphaDecay 0.025 lets the simulation run long enough to spread out fully.
    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3.forceLink(simLinks).id((n) => n.id).distance(85)
      )
      .force("charge", d3.forceManyBody().strength(-280))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.08))
      .force(
        "collision",
        d3.forceCollide().radius((n) => nodeRadius(n) + 6)
      )
      .alphaDecay(0.025)
      .on("tick", () => {
        linkSel
          .attr("x1", (e) => e.source.x).attr("y1", (e) => e.source.y)
          .attr("x2", (e) => e.target.x).attr("y2", (e) => e.target.y);
        nodeSel.attr("cx", (n) => n.x).attr("cy", (n) => n.y);
        labelSel.attr("x", (n) => n.x + 9).attr("y", (n) => n.y + 4);
      })
      .on("end", () => {
        // Auto-fit once the physics settle so the whole graph is visible.
        fitToView(false);
      });

    // ── Drag ─────────────────────────────────────────────────────────────
    const drag = d3
      .drag()
      .on("start", (evt) => {
        if (!evt.active) simulation.alphaTarget(0.3).restart();
        evt.subject.fx = evt.subject.x;
        evt.subject.fy = evt.subject.y;
      })
      .on("drag", (evt) => {
        evt.subject.fx = evt.x;
        evt.subject.fy = evt.y;
      })
      .on("end", (evt) => {
        if (!evt.active) simulation.alphaTarget(0);
        evt.subject.fx = null;
        evt.subject.fy = null;
      });
    nodeSel.call(drag);

    // ── Zoom / pan ───────────────────────────────────────────────────────
    // scaleExtent: can zoom out far enough to see dense graphs, up to 8× in.
    const zoom = d3
      .zoom()
      .scaleExtent([0.03, 8])
      .on("zoom", (evt) => zoomGroup.attr("transform", evt.transform));
    svg.call(zoom).on("dblclick.zoom", null);
    zoomBehavior = zoom;

    if (resetBtn) {
      resetBtn.onclick = () => fitToView(true);
    }

    // ── Touch tap-to-select (coarse-pointer / mobile) ─────────────────────
    svg.on("click.coarse", (evt) => {
      if (evt.target.tagName === "circle") return;
      if (!window.matchMedia("(pointer: coarse)").matches) return;
      const [mx, my] = d3.pointer(evt);
      const transform = d3.zoomTransform(svgEl);
      const [gx, gy]  = transform.invert([mx, my]);
      const tapRadius = 44 / (transform.k || 1);
      let nearest = null;
      let nearestDist = tapRadius;
      for (const n of simNodes) {
        const dx = (n.x ?? 0) - gx;
        const dy = (n.y ?? 0) - gy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < nearestDist) { nearestDist = dist; nearest = n; }
      }
      if (nearest) {
        stateRef.selectedId = nearest.id;
        applyRef?.();
        renderDetail(nearest);
      }
    });

    // ── applyVisualState (Phase 2) ────────────────────────────────────────
    // Reads stateRef directly so it never goes stale between calls without
    // triggering a simulation restart.
    function applyVisualState() {
      if (!nodeSelRef) return;
      const { selectedId: selId, hoveredId: hovId, search: query } = stateRef;
      const focusId = selId || hovId;
      const focusNeighbors = focusId
        ? (neighborRef?.get(focusId) ?? new Set())
        : new Set();

      const q = query.toLowerCase().trim();
      function isVisible(n) {
        if (!q) return true;
        return `${n.title} ${n.first_author || ""} ${n.year || ""}`.toLowerCase().includes(q);
      }

      nodeSelRef
        .attr("fill", (n) => {
          if (!isVisible(n)) return "#e2e8f0";
          if (focusId && n.id !== focusId && !focusNeighbors.has(n.id)) return "#cbd5e1";
          return nodeColor(n);
        })
        .attr("stroke", (n) =>
          n.id === selId || n.id === hovId ? "#f97316" : "#ffffff"
        )
        .attr("stroke-width", (n) =>
          n.id === selId || n.id === hovId ? 2.6 : 1.4
        )
        .attr("opacity", (n) => {
          if (!isVisible(n)) return 0.15;
          if (focusId && n.id !== focusId && !focusNeighbors.has(n.id)) return 0.25;
          return 1;
        });

      linkSelRef
        .attr("stroke", (e) => {
          const src = e.source.id ?? e.source;
          const tgt = e.target.id ?? e.target;
          if (focusId) {
            if (src === focusId) return "#ea580c";
            if (tgt === focusId) return "#0f766e";
            return "#e2e8f0";
          }
          return "#94a3b8";
        })
        .attr("stroke-opacity", (e) => {
          const src = e.source.id ?? e.source;
          const tgt = e.target.id ?? e.target;
          if (focusId) return src === focusId || tgt === focusId ? 0.85 : 0.06;
          return 0.4;
        });

      labelSelRef.attr("opacity", (n) => {
        if (!isVisible(n)) return 0;
        if (focusId && n.id !== focusId && !focusNeighbors.has(n.id)) return 0.25;
        return 1;
      });
    }

    applyRef = applyVisualState;
    applyVisualState();
  }

  // ── Phase 2: visual-only updates (no simulation restart) ─────────────────

  function triggerVisualUpdate() {
    stateRef.search = searchEl ? searchEl.value : "";
    applyRef?.();
  }

  // ── Detail panel ──────────────────────────────────────────────────────────

  function renderDetail(n) {
    if (!detailEl) return;
    if (!n) {
      detailEl.innerHTML = '<p class="ct-detail-hint">Click any node to view paper details.</p>';
      return;
    }
    const color = nodeColor(n);
    const gen   = n.generation === 0 ? "Gen 0 \u2014 foundational" : `Generation ${n.generation}`;
    const cat   = CAT_LABELS[n.category] || "Other";
    detailEl.innerHTML = `
      <div class="ct-detail-head">
        <span class="ct-detail-chip" style="background:${esc(color)}1a;color:${esc(color)};border-color:${esc(color)}55">${esc(cat)}</span>
        <span class="ct-detail-chip" style="background:var(--sl-color-bg-sidebar);color:var(--sl-color-gray-3);border-color:var(--sl-color-hairline)">${esc(gen)}</span>
      </div>
      <p class="ct-detail-title">${esc(n.title)}</p>
      <div class="ct-detail-meta">
        ${n.first_author ? `<span>${esc(n.first_author)}</span>` : ""}
        ${n.year         ? `<span>${esc(String(n.year))}</span>` : ""}
        <span>${(n.cited_by_count || 0).toLocaleString()} citations</span>
        <span>importance\u00a0${(n.importance_score || 0).toFixed(2)}</span>
      </div>`;
  }

  // ── Event wiring ──────────────────────────────────────────────────────────

  buildPills();

  if (thresholdEl) {
    thresholdEl.addEventListener("input", () => {
      importanceThreshold = parseFloat(thresholdEl.value);
      if (thresholdValEl) thresholdValEl.textContent = importanceThreshold.toFixed(1);
      rebuildGraph();
    });
  }

  if (searchEl) {
    searchEl.addEventListener("input", triggerVisualUpdate);
  }

  // ── Init (async data load) ────────────────────────────────────────────────

  async function init() {
    try {
      const resp = await fetch(DATA_URL);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      rawData = await resp.json();

      // Normalise: ensure category is a known key.
      for (const n of rawData.nodes) {
        if (!CAT_COLORS[n.category]) n.category = "unknown";
      }

      rebuildGraph();
    } catch (err) {
      console.error("Citation graph init error:", err);
      if (svgEl) {
        d3.select(svgEl)
          .append("text")
          .attr("x", "50%").attr("y", "50%")
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "middle")
          .attr("fill", "#dc2626").attr("font-size", 13)
          .text(
            `Could not load citation data. Run the pipeline first. (${err.message})`
          );
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
