import { html } from "../../lib.js";

export function ProgramsSection({ groupedPrograms }) {
  return html`
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Programs and Field Landscape</h2>
          <p className="caption">Program and organization records are sourced from the curated non-paper registry.</p>
        </div>
      </div>

      ${Object.entries(groupedPrograms)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(
          ([category, programs]) => html`
            <div className="program-group" key=${category}>
              <h3>${category}</h3>
              <div className="program-grid">
                ${programs.map((program) => {
                  const displayLinks =
                    program.links.length || program.category !== "academic"
                      ? program.links
                      : [`https://duckduckgo.com/?q=${encodeURIComponent(`${program.name} learning program`)}`];

                  return html`
                    <article className="program-card" key=${program.name}>
                      <h4>${program.name}</h4>
                      <p>${program.summary}</p>

                      ${displayLinks.length
                        ? html`
                            <p className="program-links">
                              ${displayLinks.map(
                                (link, index) => html`
                                  <a key=${`${program.name}:${link}`} href=${link} target="_blank" rel="noreferrer"
                                    >${index === 0 ? "primary link" : "source"}</a
                                  >
                                `
                              )}
                            </p>
                          `
                        : ""}

                      ${program.relatedMentions?.length
                        ? html`
                            <details>
                              <summary>Related Adjacent Mentions (${program.relatedMentions.length})</summary>
                              <ul className="flat-list compact">
                                ${program.relatedMentions.map(
                                  (mention) => html`<li key=${`${program.name}:${mention}`}>${mention}</li>`
                                )}
                              </ul>
                            </details>
                          `
                        : ""}
                    </article>
                  `;
                })}
              </div>
            </div>
          `
        )}
    </section>
  `;
}
