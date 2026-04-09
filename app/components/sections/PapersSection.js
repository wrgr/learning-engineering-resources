import { html } from "../../lib.js";

export function PapersSection({
  search,
  setSearch,
  artifactFilter,
  setArtifactFilter,
  artifactOptions,
  filteredPapers,
  topicPaperClusters,
  dataQuality,
}) {
  return html`
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Papers and Artifacts</h2>
          <p className="caption">Papers are grouped by topic code, with one expandable card per topic cluster.</p>
        </div>
        <div className="controls">
          <input
            type="search"
            value=${search}
            onInput=${(event) => setSearch(event.target.value)}
            placeholder="Search title, author, citation"
          />
          <select value=${artifactFilter} onChange=${(event) => setArtifactFilter(event.target.value)}>
            <option value="all">All artifact types</option>
            ${artifactOptions.map((type) => html`<option key=${type} value=${type}>${type}</option>`)}
          </select>
        </div>
      </div>

      <p className="caption">${filteredPapers.length} artifacts mapped across ${topicPaperClusters.length} topic clusters.</p>
      <div className="quality-banner">
        <strong>Data quality:</strong>
        ${dataQuality.missingAbstractCount} papers have no abstract metadata, ${dataQuality.shortTitleCount} paper titles are short,
        and ${dataQuality.missingResourceTopicCount} topics currently have no non-paper resources.
        ${dataQuality.missingResourceTopicCodes?.length
          ? html` Missing resource topics: ${dataQuality.missingResourceTopicCodes.join(", ")}.`
          : ""}
      </div>

      <details className="paper-tray">
        <summary>Topic-clustered paper tray</summary>
        <div className="topic-paper-grid">
          ${topicPaperClusters.map(
            (cluster) => html`
              <article className="topic-paper-card" key=${cluster.key}>
                <h3>${cluster.label}</h3>
                <p className="caption">${cluster.papers.length} papers</p>
                <details>
                  <summary>Expand papers</summary>
                  <ul className="flat-list compact">
                    ${cluster.papers.map((paper) => {
                      const authorLine = paper.authors.length ? paper.authors.join(", ") : "Authors unavailable";
                      return html`
                        <li key=${`cluster:${cluster.key}:${paper.id}`}>
                          <details>
                            <summary>${paper.title}</summary>
                            <p>${authorLine}${paper.year ? ` (${paper.year})` : ""}</p>
                            <p
                              className=${paper.abstractQA.missing
                                ? "abstract missing"
                                : paper.abstractQA.qaFlag
                                  ? "abstract warning"
                                  : "abstract"}
                            >
                              ${paper.abstractQA.preview}
                            </p>
                            <p><strong>Citation:</strong> ${paper.citation_plain || "Citation unavailable."}</p>
                            ${paper.source_url
                              ? html`<p><a href=${paper.source_url} target="_blank" rel="noreferrer">source</a></p>`
                              : ""}
                          </details>
                        </li>
                      `;
                    })}
                  </ul>
                </details>
              </article>
            `
          )}
        </div>
      </details>
    </section>
  `;
}
