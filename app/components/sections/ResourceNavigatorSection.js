/**
 * Resource Navigator section. Groups resources by content type rather than topic
 * so users can browse by "what kind of resource" before "what subject area".
 */
import { html, useMemo, useState } from "../../lib.js";
import { CONTENT_TYPE_META } from "../../constants.js";
import { prettyDomain } from "../../text.js";

const TYPE_ORDER = Object.entries(CONTENT_TYPE_META)
  .sort((a, b) => a[1].order - b[1].order)
  .map(([code]) => code);

/** Small-count types get richer cards; large-count types get a compact list. */
const RICH_TYPES = new Set(["PP", "CE", "CO", "PC", "TP"]);

function TopicBadge({ code }) {
  return html`<span className="topic-badge">${code}</span>`;
}

/** A single rich card used for PP, CE, CO, PC, TP. */
function ResourceCard({ row }) {
  const domain = prettyDomain(row.url);
  const snippet = row.context ? row.context.slice(0, 120) + (row.context.length > 120 ? "…" : "") : "";

  return html`
    <div className="resource-card">
      <div className="resource-card-title">
        ${row.url
          ? html`<a href=${row.url} target="_blank" rel="noreferrer">${row.title}</a>`
          : html`<span>${row.title}</span>`}
      </div>
      ${domain ? html`<div className="resource-card-domain">${domain}</div>` : ""}
      ${snippet ? html`<p className="resource-card-context">${snippet}</p>` : ""}
      <div className="resource-card-tags">
        ${(row.topic_codes || []).map((code) => html`<${TopicBadge} key=${code} code=${code} />`)}
      </div>
    </div>
  `;
}

/**
 * Compact list for GL and AP, sub-grouped by section (topic).
 * Each sub-group is collapsible after the first 10 items.
 */
function CompactTypeSection({ rows }) {
  const bySection = useMemo(() => {
    const map = new Map();
    for (const row of rows) {
      const key = row.section || "Other";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(row);
    }
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [rows]);

  return html`
    <div className="resource-compact-sections">
      ${bySection.map(([section, items]) => html`
        <${CompactSubSection} key=${section} section=${section} items=${items} />
      `)}
    </div>
  `;
}

const COMPACT_INITIAL = 8;

function CompactSubSection({ section, items }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, COMPACT_INITIAL);
  const overflow = items.length - COMPACT_INITIAL;

  return html`
    <div className="resource-compact-group">
      <h4 className="resource-compact-head">
        ${section}
        <span className="count-pill">${items.length}</span>
      </h4>
      <ul className="flat-list compact">
        ${visible.map((row) => {
          const domain = prettyDomain(row.url);
          return html`
            <li key=${row.key}>
              ${row.url
                ? html`<a href=${row.url} target="_blank" rel="noreferrer">${row.title}</a>`
                : html`<span>${row.title}</span>`}
              ${domain ? html`<span className="resource-meta"> · ${domain}</span>` : ""}
            </li>
          `;
        })}
      </ul>
      ${!expanded && overflow > 0
        ? html`<button className="ghost-btn" onClick=${() => setExpanded(true)}>Show ${overflow} more</button>`
        : ""}
    </div>
  `;
}

export function ResourceNavigatorSection({
  filteredResourceRows,
  resourceQuery,
  setResourceQuery,
}) {
  const [activeType, setActiveType] = useState("all");

  /** Group all rows by content_type, preserving TYPE_ORDER. */
  const typeGroups = useMemo(() => {
    const map = new Map(TYPE_ORDER.map((code) => [code, []]));
    for (const row of filteredResourceRows) {
      const code = row.content_type || "GL";
      if (!map.has(code)) map.set(code, []);
      map.get(code).push(row);
    }
    return Array.from(map.entries()).filter(([, rows]) => rows.length > 0);
  }, [filteredResourceRows]);

  const visibleGroups = useMemo(
    () => (activeType === "all" ? typeGroups : typeGroups.filter(([code]) => code === activeType)),
    [activeType, typeGroups]
  );

  const totalShown = visibleGroups.reduce((n, [, rows]) => n + rows.length, 0);

  return html`
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Resource Navigator</h2>
          <p className="caption">Tools, programs, people, organizations, conferences, and field literature — grouped by resource type.</p>
        </div>
      </div>

      <div className="resource-controls">
        <input
          className="resource-search"
          type="search"
          value=${resourceQuery}
          onInput=${(e) => setResourceQuery(e.target.value)}
          placeholder="Search titles, topics, or context…"
        />
        <div className="type-pill-row">
          <button
            className=${`type-pill ${activeType === "all" ? "active" : ""}`}
            onClick=${() => setActiveType("all")}
          >
            All
            <span>${filteredResourceRows.length}</span>
          </button>
          ${typeGroups.map(([code, rows]) => {
            const meta = CONTENT_TYPE_META[code] || { label: code };
            return html`
              <button
                key=${code}
                className=${`type-pill ${activeType === code ? "active" : ""}`}
                onClick=${() => setActiveType(code)}
              >
                ${meta.label}
                <span>${rows.length}</span>
              </button>
            `;
          })}
        </div>
      </div>

      <p className="caption" style=${{ marginTop: "0.5rem" }}>${totalShown} resource${totalShown !== 1 ? "s" : ""} shown.</p>

      ${visibleGroups.map(([code, rows]) => {
        const meta = CONTENT_TYPE_META[code] || { plural: code };
        const isRich = RICH_TYPES.has(code);
        return html`
          <div key=${code} className="resource-type-section">
            <h3 className="resource-type-head">
              ${meta.plural}
              <span className="count-pill">${rows.length}</span>
            </h3>
            ${isRich
              ? html`
                  <div className="resource-card-grid">
                    ${rows.map((row) => html`<${ResourceCard} key=${row.key} row=${row} />`)}
                  </div>
                `
              : html`<${CompactTypeSection} rows=${rows} />`}
          </div>
        `;
      })}
    </section>
  `;
}
