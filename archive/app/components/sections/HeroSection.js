import { html } from "../../lib.js";
import {
  EDITION_LABEL_CLASSIC,
  EDITION_LABEL_MERGED,
  EDITION_LINK_TO_CLASSIC_TITLE,
  EDITION_LINK_TO_MERGED_TITLE,
  SITE_DISCLAIMER,
} from "../../siteCopy.js";

/**
 * @param {{ stats: [string, string|number][], edition?: "classic"|"merged" }} props
 */
export function HeroSection({ stats, edition = "classic" }) {
  const isMerged = edition === "merged";
  const title = isMerged
    ? "Learning engineering workspace — broadened corpus"
    : "A curated evidence workspace for the learning engineering field";
  const lede = isMerged
    ? "Topics and provenance match the curated site. This edition adds a second paper lane beyond seed papers and one-hop citations, split into Core and Expanded tiers. In the graph, Corpus view controls whether Expanded-tier papers appear."
    : "Explore core and related papers, field programs, and non-paper resources — each linked to a topic and traceable back to its source. Provenance is visible on every item.";

  return html`
    <header className="wrap hero" id="overview">
      <div className="hero-layout">
        <div className="hero-copy">
          <p className="eyebrow">Learning Engineering</p>
          <p className="edition-chip" aria-label="Site edition">${isMerged ? EDITION_LABEL_MERGED : EDITION_LABEL_CLASSIC}</p>
          <h1>${title}</h1>
          <p className="lede">${lede}</p>
          <p style=${{ marginTop: "0.9rem" }} className="hero-actions">
            <a href="whitepaper.html" className="wp-cta">Read the whitepaper →</a>
            ${isMerged
              ? html`<a href="index.html" className="hero-edition-link" title=${EDITION_LINK_TO_CLASSIC_TITLE}>Switch to curated edition →</a>`
              : html`<a href="merged.html" className="hero-edition-link" title=${EDITION_LINK_TO_MERGED_TITLE}>Switch to broadened corpus →</a>`}
          </p>
        </div>
        <figure className="hero-figure">
          <img src="assets/what-is-le-banner.png" alt="Learning engineering framework poster" />
        </figure>
      </div>

      <div className="stats-grid">
        ${stats.map(
          ([label, value]) => html`
            <article className="stat-card" key=${label}>
              <div className="k">${label}</div>
              <div className="v">${value}</div>
            </article>
          `
        )}
      </div>

      <p className="hero-disclaimer">${SITE_DISCLAIMER}</p>
    </header>
  `;
}
