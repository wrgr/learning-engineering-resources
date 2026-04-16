/**
 * Papers and Artifacts: search and artifact filter over seed + expansion papers; topic browse when not searching.
 */
import { MERGED_THEMATIC_SEARCH_PRESETS } from "../../constants.js";
import { html } from "../../lib.js";

function scopeClass(scope) {
  if (scope === "hop") return "paper-scope-tag paper-scope-hop";
  if (scope === "merged") return "paper-scope-tag paper-scope-merged";
  return "paper-scope-tag paper-scope-seed";
}

function scopeLabel(paper) {
  if (paper.scope === "hop") return "Expansion";
  if (paper.scope === "merged") return "Broad lane";
  return "Seed";
}

function PaperDetailBlock({ paper }) {
  const authorLine = paper.authors.length ? paper.authors.join(", ") : "Authors unavailable";
  const tier =
    paper.corpus_tier === "expanded"
      ? html`<span className="paper-tier-tag paper-tier-expanded">Expanded tier</span>`
      : html`<span className="paper-tier-tag paper-tier-core">Core tier</span>`;
  return html`
    <details className="paper-hit">
      <summary>${paper.title}</summary>
      <p className="paper-hit-meta">
        <span className=${scopeClass(paper.scope)}>${scopeLabel(paper)}</span>
        ${paper.scope === "merged" ? tier : null}
        ${authorLine}${paper.year ? ` · ${paper.year}` : ""}
      </p>
      <p
        className=${paper.abstractQA.missing ? "abstract missing" : paper.abstractQA.qaFlag ? "abstract warning" : "abstract"}
      >
        ${paper.abstractQA.proxy ? "[Proxy description] " : ""}
        ${paper.abstractQA.preview}
      </p>
      <p><strong>Citation:</strong> ${paper.citation_plain || "No citation available."}</p>
      ${paper.source_url
        ? html`<p><a href=${paper.source_url} target="_blank" rel="noreferrer">source</a></p>`
        : ""}
    </details>
  `;
}

export function PapersSection({
  edition,
  search,
  setSearch,
  artifactFilter,
  setArtifactFilter,
  artifactOptions,
  filteredPapers,
  topicPaperClusters,
  dataQuality,
}) {
  const queryTrim = (search || "").trim();
  const listNote =
    edition === "merged"
      ? "Core and Expanded apply only to broad-lane papers. Seed and one-hop papers are unchanged. The graph's Corpus view uses the same tier for visualization."
      : "Seed and one-hop papers both appear here. The graph's \"Include related papers\" toggle affects only the graph, not this list. When you are not searching, papers are grouped by topic; search matches the full list below.";

  return html`
    <section id="papers" className="panel">
      <div className="panel-head">
        <div>
          <h2>Papers and Artifacts</h2>
          <p className="caption">${listNote}</p>
        </div>
        <div className="controls">
          <input
            type="search"
            value=${search}
            onInput=${(event) => setSearch(event.target.value)}
            placeholder="Search by title, author, or citation"
          />
          <select value=${artifactFilter} onChange=${(event) => setArtifactFilter(event.target.value)}>
            <option value="all">All artifact types</option>
            ${artifactOptions.map((type) => html`<option key=${type} value=${type}>${type}</option>`)}
          </select>
        </div>
      </div>
      ${edition === "merged"
        ? html`
            <div className="paper-thematic-presets" role="group" aria-label="Thematic search shortcuts">
              <span className="caption">Quick thematic search:</span>
              ${MERGED_THEMATIC_SEARCH_PRESETS.map(
                (preset) => html`
                  <button
                    type="button"
                    className="pill-btn"
                    key=${preset.id}
                    onClick=${() => setSearch(preset.query)}
                  >
                    ${preset.label}
                  </button>
                `
              )}
            </div>
          `
        : null}

      <p className="caption">${filteredPapers.length} papers across ${topicPaperClusters.length} topic clusters.</p>
      <div className="quality-banner">
        <strong>Coverage notes:</strong>
        ${dataQuality.missingAbstractCount} papers are missing abstract text, ${dataQuality.proxyAbstractCount} use proxy descriptions,
        ${dataQuality.shortTitleCount} have short titles,
        and ${dataQuality.missingResourceTopicCount} topics have no non-paper resources yet.
        ${dataQuality.missingResourceTopicCodes?.length
          ? html` Topics missing resources: ${dataQuality.missingResourceTopicCodes.join(", ")}.`
          : ""}
      </div>

      ${queryTrim
        ? html`
            <div className="paper-search-matches">
              <h3 className="paper-search-matches-head">
                Matching papers <span className="count-pill">${filteredPapers.length}</span>
              </h3>
              <p className="caption">Clear the search box to browse by topic cluster again.</p>
              ${filteredPapers.length
                ? html`
                    <ul className="flat-list compact paper-flat-list">
                      ${filteredPapers.map(
                        (paper) => html`
                          <li key=${`hit:${paper.id}`}>
                            <${PaperDetailBlock} paper=${paper} />
                          </li>
                        `
                      )}
                    </ul>
                  `
                : html`<p className="caption">No papers match — try different words, clear the artifact filter, or check spelling.</p>`}
            </div>
          `
        : html`
            <details className="paper-tray" open>
              <summary>Browse by topic</summary>
              <div className="topic-paper-grid">
                ${topicPaperClusters.map(
                  (cluster) => html`
                    <article className="topic-paper-card" key=${cluster.key}>
                      <h3>${cluster.label}</h3>
                      <p className="caption">${cluster.papers.length} papers</p>
                      <details>
                        <summary>Show papers</summary>
                        <ul className="flat-list compact">
                          ${cluster.papers.map(
                            (paper) => html`
                              <li key=${`cluster:${cluster.key}:${paper.id}`}>
                                <${PaperDetailBlock} paper=${paper} />
                              </li>
                            `
                          )}
                        </ul>
                      </details>
                    </article>
                  `
                )}
              </div>
            </details>
          `}
    </section>
  `;
}
