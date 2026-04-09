import { html } from "../../lib.js";
import { prettyDomain } from "../../text.js";

export function ResourceNavigatorSection({
  groupedResources,
  filteredResourceRows,
  missingResourceTopicCodes,
  entities,
  activeEntities,
  toggleEntity,
  resourceQuery,
  setResourceQuery,
  clearEntities,
}) {
  return html`
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Resource Navigator</h2>
          <p className="caption">Resources are grouped by topic so papers and non-paper artifacts stay aligned.</p>
        </div>
      </div>

      <p className="caption">${filteredResourceRows.length} resources currently shown.</p>
      ${missingResourceTopicCodes?.length
        ? html`
            <p className="caption">
              Topics currently missing non-paper resources: ${missingResourceTopicCodes.join(", ")}.
            </p>
          `
        : ""}

      <div className="resource-topic-grid">
        ${groupedResources.map(
          ({ group, rows }) => html`
            <article className="resource-topic-card" key=${group}>
                <h3>${group} <span className="count-pill">${rows.length}</span></h3>
              <ul className="flat-list compact">
                ${rows.slice(0, 14).map(
                  (row) => html`
                    <li key=${row.key}>
                      ${row.url
                        ? html`<a href=${row.url} target="_blank" rel="noreferrer">${row.title}</a>`
                        : html`<span>${row.title}</span>`}
                      <div className="resource-meta">${row.section}${prettyDomain(row.url) ? ` | ${prettyDomain(row.url)}` : ""}</div>
                    </li>
                  `
                )}
              </ul>

              ${rows.length > 14
                ? html`
                    <details>
                      <summary>Show ${rows.length - 14} more</summary>
                      <ul className="flat-list compact">
                        ${rows.slice(14).map(
                          (row) => html`
                            <li key=${`${row.key}:more`}>
                              ${row.url
                                ? html`<a href=${row.url} target="_blank" rel="noreferrer">${row.title}</a>`
                                : html`<span>${row.title}</span>`}
                              <div className="resource-meta">
                                ${row.section}${prettyDomain(row.url) ? ` | ${prettyDomain(row.url)}` : ""}
                              </div>
                            </li>
                          `
                        )}
                      </ul>
                    </details>
                  `
                : ""}
            </article>
          `
        )}
      </div>

      <details className="filter-tray">
        <summary>Optional filters</summary>
        <div className="controls" style=${{ marginTop: "0.55rem" }}>
          <input
            type="search"
            value=${resourceQuery}
            onInput=${(event) => setResourceQuery(event.target.value)}
            placeholder="Search titles, sections, or context"
          />
        </div>
        <div className="entity-row">
          ${(entities || []).slice(0, 36).map(
            (entity) => html`
              <button
                key=${entity.key}
                className=${`entity-chip ${activeEntities.includes(entity.key) ? "active" : ""}`}
                onClick=${() => toggleEntity(entity.key)}
              >
                ${entity.name}
                <span>${entity.count}</span>
              </button>
            `
          )}
        </div>
        ${activeEntities.length || resourceQuery
          ? html`
              <div className="resource-actions">
                <button className="ghost-btn" onClick=${clearEntities}>Clear entities</button>
                <button className="ghost-btn" onClick=${() => setResourceQuery("")}>Clear search</button>
              </div>
            `
          : ""}
      </details>
    </section>
  `;
}
