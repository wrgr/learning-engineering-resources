"""Orchestrate IEEE/ICICLE conference harvest, merge proposed lane rows, optional citing pass, and merged site dataset build."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

from utils import ROOT, load_dotenv_optional

SCRIPTS = ROOT / "scripts"


def _run(py_file: Path, argv: List[str]) -> None:
    """Run a script in this repo with the same interpreter."""
    cmd = [sys.executable, str(py_file)] + argv
    proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> None:
    """CLI: harvest -> merge proposed -> optional citing expansion -> build_merged_site_dataset."""
    load_dotenv_optional()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-harvest", action="store_true", help="Skip OpenAlex conference harvest.")
    parser.add_argument("--skip-merge", action="store_true", help="Skip merging proposed_lane_additions into lane_work_specs.")
    parser.add_argument(
        "--with-citing-expansion",
        action="store_true",
        help="Run collect_citing_works_openalex.py (adds API load; writes citing_one_hop_candidates.json).",
    )
    parser.add_argument(
        "--citing-rounds",
        type=int,
        choices=(1, 2),
        default=1,
        help="Forward to collect_citing_works_openalex when --with-citing-expansion is set.",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip build_merged_site_dataset.py.")
    parser.add_argument(
        "--harvest-replace",
        action="store_true",
        help="Harvest without --merge-existing (overwrite ieee_conference_seed_work_ids work_ids). Default unions with existing ids.",
    )
    args = parser.parse_args()

    if not args.skip_harvest:
        hv = ["--merge-existing", "--max-total", "10000"]
        if args.harvest_replace:
            hv = ["--max-total", "10000"]
        _run(SCRIPTS / "harvest_ieee_icicle_conference_works.py", hv)

    if not args.skip_merge:
        _run(SCRIPTS / "merge_proposed_into_lane_work_specs.py", [])

    if args.with_citing_expansion:
        _run(
            SCRIPTS / "collect_citing_works_openalex.py",
            ["--rounds", str(args.citing_rounds)],
        )

    if not args.skip_build:
        _run(SCRIPTS / "build_merged_site_dataset.py", [])

    print("Merged lane automation finished.")


if __name__ == "__main__":
    main()
