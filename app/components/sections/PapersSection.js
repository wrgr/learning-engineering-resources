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
          <p className="caption">Papers are grouped by topic, sorted by citation count. Expand any cluster to browse individual items.</p>
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

      <details className="paper-tray">
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
                              ${paper.abstractQA.proxy ? "[Proxy description] " : ""}
                              ${paper.abstractQA.preview}
                            </p>
                            <p><strong>Citation:</strong> ${paper.citation_plain || "No citation available."}</p>
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
