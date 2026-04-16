/**
 * Page footer: edition switcher (mirrors the hero) plus the shared disclaimer
 * so readers who scroll past the hero can still open the other static HTML entry point.
 */
import { html } from "../../lib.js";
import {
  EDITION_LABEL_CLASSIC,
  EDITION_LABEL_MERGED,
  EDITION_LINK_TO_CLASSIC_TITLE,
  EDITION_LINK_TO_MERGED_TITLE,
  SITE_DISCLAIMER,
} from "../../siteCopy.js";

/**
 * @param {{ edition?: "classic"|"merged" }} props
 */
export function SiteFooter({ edition = "classic" }) {
  const isMerged = edition === "merged";
  return html`
    <footer className="wrap site-footer">
      <div className="site-footer-edition" role="navigation" aria-label="Site edition">
        <span className="edition-chip edition-chip-footer">${isMerged ? EDITION_LABEL_MERGED : EDITION_LABEL_CLASSIC}</span>
        <span className="site-footer-edition-sep" aria-hidden="true">·</span>
        ${isMerged
          ? html`<a href="index.html" className="footer-edition-link" title=${EDITION_LINK_TO_CLASSIC_TITLE}>Curated edition</a>`
          : html`<a href="merged.html" className="footer-edition-link" title=${EDITION_LINK_TO_MERGED_TITLE}>Broadened corpus</a>`}
      </div>
      <p>${SITE_DISCLAIMER}</p>
    </footer>
  `;
}
