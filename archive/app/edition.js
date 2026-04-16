/**
 * Detects which static dataset edition the SPA should load (classic vs merged broad corpus).
 */

/** @returns {"classic"|"merged"} */
export function getDataEdition() {
  if (typeof window === "undefined") return "classic";
  if (window.__LER_EDITION__ === "merged") return "merged";
  const params = new URLSearchParams(window.location.search || "");
  if (params.get("edition") === "merged") return "merged";
  return "classic";
}
