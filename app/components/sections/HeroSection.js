import { html } from "../../lib.js";

export function HeroSection({ stats }) {
  return html`
    <header className="wrap hero">
      <div className="hero-layout">
        <div className="hero-copy">
          <p className="eyebrow">Learning Engineering Knowledge Studio</p>
          <h1>Topic-linked evidence workspace for papers, programs, and field artifacts</h1>
          <p className="lede">
            This edition is rebuilt from the latest corpus pipeline: topics map directly to seed papers, expansion papers, and
            non-paper resources, with provenance visible on every node.
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
    </header>
  `;
}
