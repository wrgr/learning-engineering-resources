"""Remove merged-lane work rows whose titles are clearly outside education, learning, or learning engineering."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Set

from utils import ROOT, load_dotenv_optional, load_json, write_json

DATA_MERGED = ROOT / "data" / "merged" / "papers_merged_lane.json"
LANE_SPECS = ROOT / "corpus" / "merged_lane" / "lane_work_specs.json"
AUDIT_OUT = ROOT / "corpus" / "merged_lane" / "offtopic_prune_audit.json"

# Title substrings / patterns for obvious non-education domains (materials science, clinical trials, etc.).
_TITLE_NEGATIVE_PATTERNS = [
    r"\bPET\b.*\bdepolymer",
    r"hydrolase",
    r"endosomal",
    r"cell-penetrating peptide",
    r"radiotherapy",
    r"stereotactic",
    r"sarcoma",
    r"bone fracture",
    r"cone beam computed tomography",
    r"lymphoma",
    r"mediastinal",
    r"soft tissue sarcoma",
    r"limb-preserving",
    r"photosystem",
    r"light-harvesting",
    r"\blhcii\b",
    r"chlorophyll",
    r"spinach",
    r"phytopathogen",
    r"rhizosphere",
    r"nanosheet",
    r"nanocluster",
    r"nanotube",
    r"\bbattery\b",
    r"lithium-ion",
    r"sodium-ion",
    r"vanadium oxide",
    r"electrolyte",
    r"zn battery",
    r"graphene oxide",
    r"\bmos2\b",
    r"metal organic framework",
    r"peanut shell",
    r"dnmt1",
    r"acute myeloid",
    r"microalga",
    r"esophageal squamous",
    r"breast cancer progression",
    r"piwi-interacting",
    r"chemoresistance",
    r"nitrogen[-‐]doped porous carbon",
    r"particle physics",
    r"standard model effective field theory",
    r"higgs",
    r"electroweak",
    r"gravitational wave",
    r"starobinsky",
    r"supergravity",
    r"cosmic string",
    r"lorentz violation",
    r"gamma-ray bursts",
    r"750 gev",
    r"radars to monitor stream",
    r"extraordinary floods",
    r"debris flow warning",
    r"al-li base products for aerospace",
    r"upadacitinib",
    r"atopic dermatitis",
    r"psoriatic arthritis",
    r"ulcerative colitis",
    r"supply chain",
    r"demand forecast sharing",
    r"retroperitoneal oblique",
    r"intervertebral disc",
    r"minimally invasive direct lateral interbody",
    r"impact™ computerized",
    r"discriminant construct validity of impact",
    r"review of particle physics",
    r"nanoGrav",
    r"pulsar timing",
    r"erythrocyte membrane.*gold",
    r" na3pse4 ",
    r" zncl2 ",
    r"anderson-like.*photochromism",
    r"x-ray and uv dual photochromism",
    r"heparan sulfate proteoglycans.*proteopathic",
    r"structure of (spinach|maize) photosystem",
    r"competition for iron drives phytopathogen",
    r"machine learning: new ideas and tools in environmental science",
    r"information diffusion in online social networks: models and methods",
    r"fantasy sports leagues",
    r"vo2max improvements in adults",
    r"myspace: social networking",
    r"probable fate of the standard model",
]
_NEG_RE = [re.compile(p, re.I) for p in _TITLE_NEGATIVE_PATTERNS]

# If these appear in the title, do not treat as off-topic (education anchors).
_EDU_HINT = re.compile(
    r"education|student|school|teach|learn(ing)? engineering|pedagog|classroom|tutor|assessment",
    re.I,
)

# Hard-exclude domains even when a vague “learning” substring might appear elsewhere.
_HARD_EXCLUDE = re.compile(
    r"radiotherapy|sarcoma|battery|photosystem|particle physics|gravitational|upadacitinib|peanut shell",
    re.I,
)


def title_is_offtopic(title: str) -> bool:
    """Return True when the title is clearly outside learning / education / LE scope."""
    t = title or ""
    for rx in _NEG_RE:
        if rx.search(t):
            if _HARD_EXCLUDE.search(t):
                return True
            if _EDU_HINT.search(t):
                return False
            return True
    return False


def filter_lane_specs(specs: List[dict], keep_ids: Set[str]) -> List[dict]:
    """Keep only rows whose work_id is in keep_ids."""
    return [row for row in specs if (row.get("work_id") or "").strip() in keep_ids]


def main() -> None:
    """CLI: prune lane_work_specs from offtopic titles; optional audit JSON."""
    load_dotenv_optional()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--papers",
        type=Path,
        default=DATA_MERGED,
        help="Merged lane papers JSON (for titles)",
    )
    parser.add_argument("--specs", type=Path, default=LANE_SPECS)
    parser.add_argument("--write", action="store_true", help="Write filtered lane_work_specs.json")
    args = parser.parse_args()

    payload = load_json(args.papers)
    removed_detail = []
    remove_ids: Set[str] = set()
    for paper in payload.get("papers") or []:
        title = (paper.get("title") or "").strip()
        wid = (paper.get("id") or "").strip()
        if title_is_offtopic(title):
            remove_ids.add(wid)
            removed_detail.append({"work_id": wid, "title": title})

    all_ids = {(p.get("id") or "").strip() for p in payload.get("papers") or []}
    keep_ids = all_ids - remove_ids

    specs = load_json(args.specs)
    if not isinstance(specs, list):
        raise SystemExit("lane_work_specs must be a JSON array")
    filtered = filter_lane_specs(specs, keep_ids)
    removed_rows = len(specs) - len(filtered)

    audit = {
        "removed_work_ids": sorted(remove_ids),
        "removed_paper_count": len(remove_ids),
        "kept_lane_row_count": len(filtered),
        "lane_specs_rows_dropped": removed_rows,
        "removed_detail": removed_detail,
    }
    write_json(AUDIT_OUT, audit)

    print(
        f"Off-topic titles: {len(remove_ids)} papers; lane rows removed: {removed_rows}; "
        f"lane rows kept: {len(filtered)}. Audit -> {AUDIT_OUT}"
    )

    if args.write:
        write_json(args.specs, filtered)
        print(f"Wrote {args.specs}")


if __name__ == "__main__":
    main()
