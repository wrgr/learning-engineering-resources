import { html } from "../../lib.js";

export function UpdateWorkflowSection() {
  return html`
    <section className="panel">
      <h2>Update Workflow</h2>
      <p className="caption">Use this sequence when refreshing the corpus, expansion set, and website data.</p>
      <ol className="flat-list compact">
        <li>
          Rebuild corpus outputs from the workbook and methodology with <code>python3 scripts/build_corpus.py</code>.
        </li>
        <li>
          Regenerate expansion candidates with <code>python3 scripts/run_openalex_expansion.py ...</code>, then apply core filters.
        </li>
        <li>
          Build website data from corpus outputs with <code>python3 scripts/build_dataset.py</code>.
        </li>
        <li>
          Verify topic-to-paper and topic-to-resource links in the graph and resource navigator.
        </li>
        <li>
          Run a quick UI check at <a href="http://127.0.0.1:8000/" target="_blank" rel="noreferrer">http://127.0.0.1:8000/</a>
          and confirm topic clusters, filters, and selected-node provenance.
        </li>
      </ol>
      <p className="caption">
        Full IEEE ICICLE content, partners, and community listings are maintained on the official site:
        <a href="https://sagroups.ieee.org/icicle/" target="_blank" rel="noreferrer"> https://sagroups.ieee.org/icicle/</a>.
      </p>
    </section>
  `;
}
