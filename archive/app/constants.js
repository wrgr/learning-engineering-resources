/** Shared paths between classic and merged editions (seed/hop papers and endnotes stay in `data/`). */
const SHARED_DATA_FILES = {
  topicMap: { path: "data/topic_map.json" },
  resources: { path: "data/icicle_resources.json" },
  seedPapers: { path: "data/papers_seed.json" },
  hopPapers: { path: "data/papers_one_hop.json" },
  endnotesEnriched: { path: "data/endnotes_enriched.json" },
  endnotesRaw: { path: "data/endnotes_raw.json" },
  programs: { path: "data/programs_summary.json" },
  gaps: { path: "data/gaps.json" },
  extraDocs: {
    path: "data/extra_docs.json",
    optional: true,
    fallback: { count: 0, documents: [] },
  },
};

/** Default site: summary + graph under `data/`. */
export const DATA_FILES_CLASSIC = {
  ...SHARED_DATA_FILES,
  summary: { path: "data/build_summary.json" },
  graph: { path: "data/graph.json" },
};

/** Broadened edition: merged summary/graph + optional merged-lane papers (distilled core vs expanded). */
export const DATA_FILES_MERGED = {
  ...SHARED_DATA_FILES,
  summary: { path: "data/merged/build_summary.json" },
  graph: { path: "data/merged/graph.json" },
  mergedLane: {
    path: "data/merged/papers_merged_lane.json",
    optional: true,
    fallback: { papers: [] },
  },
};

/** @param {"classic"|"merged"} edition */
export function getDataFiles(edition) {
  return edition === "merged" ? DATA_FILES_MERGED : DATA_FILES_CLASSIC;
}

/**
 * Merged-edition paper search shortcuts; labels mirror intents in
 * `corpus/merged_lane/openalex_thematic_queries.json` (harvest strings differ from these UI queries).
 */
export const MERGED_THEMATIC_SEARCH_PRESETS = [
  { id: "ai_education", label: "AI + education", query: "intelligent tutoring artificial intelligence" },
  { id: "ai_learning_engineering", label: "AI + learning engineering", query: "learning engineering machine learning" },
  { id: "llms_in_education", label: "LLMs in education", query: "large language model education generative" },
];

/** @deprecated Use getDataFiles(getDataEdition()) — kept for grep/lint compatibility. */
export const DATA_FILES = DATA_FILES_CLASSIC;

export const RESOURCE_GROUP_ORDER = [
  "People & Teams",
  "Conferences & Events",
  "Methods & Tools",
  "Programs & Organizations",
  "Books & Reading",
  "Media & Webinars",
  "Standards & Infrastructure",
  "Other",
];

/** Display metadata for each ICICLE resource content_type code. */
export const CONTENT_TYPE_META = {
  PP: { label: "People", plural: "People & Practitioners", order: 0 },
  CE: { label: "Conferences", plural: "Conferences & Events", order: 1 },
  CO: { label: "Organizations", plural: "Communities & Organizations", order: 2 },
  PC: { label: "Programs", plural: "Programs & Curricula", order: 3 },
  TP: { label: "Tools", plural: "Tools & Platforms", order: 4 },
  GL: { label: "Reports", plural: "Reports & Resources", order: 5 },
  AP: { label: "Papers", plural: "Academic Papers", order: 6 },
  GT: { label: "Topics (graph)", plural: "Topics & domains", order: 7 },
  GC: { label: "Concepts (graph)", plural: "Concepts", order: 8 },
  GP: { label: "Papers (graph)", plural: "Papers in graph", order: 9 },
};

export const OLD_LENS_URL = "https://education.jhu.edu/academics/masters-programs/learning-design-technology/";
export const NEW_LENS_URL =
  "https://education.jhu.edu/masters-programs/master-of-education-in-learning-design-and-technology/";

export const NODE_COLORS = {
  topic_part: "#0f766e",
  topic_surface: "#f97316",
  topic: "#334155",
  concept: "#6d28d9",
  paper_seed: "#1d4ed8",
  paper_hop: "#a16207",
  paper_merged: "#7c3aed",
  resource: "#0f766e",
  unknown: "#94a3b8",
};

export const CP1252_REPAIRS = {
  "\u0091": "'",
  "\u0092": "'",
  "\u0093": '"',
  "\u0094": '"',
  "\u0096": "-",
  "\u0097": "-",
  "\u00A0": " ",
};

export const CONTROL_CHARS_RE = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g;
export const PERSON_RE = /\b([A-Z][a-z]+(?:\s+[A-Z][a-z.'-]+){1,2})\b/g;
export const ORG_RE =
  /\b([A-Z][A-Za-z&.'-]+(?:\s+[A-Z][A-Za-z&.'-]+){0,8}\s(?:University|College|Institute|Consortium|Community|School|Academy|Committee|Center|Centre|Agency|Laboratory|Labs))\b/g;

export const PERSON_BLOCKLIST = new Set([
  "Learning Engineering",
  "Learning Sciences",
  "Open Learning",
  "Design Thinking",
  "Stage Two",
  "Higher Education",
  "Market Interest",
  "Mission Critical",
  "Performance Task",
  "Silver Lining",
  "Generalizable Learning",
  "Organization Maturity",
  "Learning Design",
  "Instructional Design",
  "Data Use",
]);

export const TOKEN_BLOCKLIST = new Set([
  "the",
  "and",
  "for",
  "with",
  "from",
  "learning",
  "engineering",
  "chapter",
  "toolkit",
  "resource",
  "resources",
  "icicle",
]);

export const GENERIC_RESOURCE_TITLES = new Set([
  "activity",
  "introduction",
  "presentation",
  "workbook",
  "resource",
  "resources",
  "video",
  "tool",
  "article",
  "link",
  "source",
]);
