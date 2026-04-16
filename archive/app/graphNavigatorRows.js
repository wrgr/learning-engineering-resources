/**
 * Builds Resource Navigator rows from visible graph nodes (topics, concepts, papers)
 * so the navigator can mirror non-resource graph content when "community" mode is on.
 */
import { browseGroupKey } from "./graph.js";

/**
 * @param {{ nodes?: object[] }} visibleGraph
 * @returns {object[]}
 */
export function graphNodesToNavigatorRows(visibleGraph) {
  const rows = [];
  for (const node of visibleGraph?.nodes || []) {
    const gk = browseGroupKey(node);
    if (gk === "resource") continue;
    if (gk !== "topic" && gk !== "concept" && gk !== "paper") continue;

    const code = gk === "topic" ? "GT" : gk === "concept" ? "GC" : "GP";
    let url = "";
    if (gk === "paper") {
      const id = String(node.id || "");
      if (id.startsWith("W")) url = `https://openalex.org/${id}`;
    }

    rows.push({
      key: `graph-node-${node.id}`,
      section: "Corpus graph",
      title: node.label || node.id,
      url,
      context: `Graph node · ${gk}${(node.hop || 0) > 0 ? ` · hop ${node.hop}` : ""}`,
      topic_codes: Array.isArray(node.topic_codes) ? node.topic_codes : [],
      content_type: code,
      status: "",
      resource_id: "",
      from_graph: true,
    });
  }
  return rows;
}
