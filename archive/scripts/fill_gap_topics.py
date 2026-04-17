"""Add curated resources for under-covered topics T02, T05, T09.

Each entry carries provenance.dataset = 'gap-fill-curated-2026-04'
to distinguish from ICICLE-harvested or Excel-sourced material.
Deduplicates against existing registry entries by normalized name/title.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TABLES = ROOT / "archive" / "corpus" / "tables"
PP_REGISTRY = TABLES / "programs_people_registry.json"
IC_REGISTRY = TABLES / "icicle_resources_registry.json"
CORPUS = ROOT / "archive" / "corpus"
PAPERS_JSONL = CORPUS / "academic_papers.jsonl"
SEEDS_JSONL = CORPUS / "expansion_seed_queries.jsonl"

DATASET = "gap-fill-curated-2026-04"


def load_json(path: Path) -> list:
    """Load a JSON array from a file."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: list) -> None:
    """Write a JSON array to a file."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file."""
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write a JSONL file."""
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize(text: str) -> str:
    """Normalize text for dedup."""
    return " ".join(text.lower().strip().split())


def next_id(registry: list, prefix: str) -> int:
    """Find the next available ID number for a given prefix."""
    max_n = 0
    for r in registry:
        rid = r.get("resource_id", "")
        if rid.startswith(prefix):
            try:
                n = int(rid.split("-")[-1])
                max_n = max(max_n, n)
            except ValueError:
                pass
    return max_n + 1


# ═══════════════════════════════════════════════════════════════════
# T02: Systems Engineering & Human Factors
# ═══════════════════════════════════════════════════════════════════

T02_PAPERS = [
    {
        "title": "Handbook of Human Systems Integration",
        "authors": "Harold R. Booher",
        "year": 2003,
        "venue": "Wiley",
        "doi": "",
        "url": "https://www.wiley.com/en-us/Handbook+of+Human+Systems+Integration-p-9780471020530",
        "primary_topic": "T02",
        "secondary_topics": "T10",
        "significance": "The definitive reference for HSI methodology. Establishes the six HSI domains (manpower, personnel, training, human factors, safety, health) and how they constrain system design. Directly applicable to learning system architecture where the human is the top-level design constraint.",
    },
    {
        "title": "Cognitive Work Analysis: Toward Safe, Productive, and Healthy Computer-Based Work",
        "authors": "Kim J. Vicente",
        "year": 1999,
        "venue": "Lawrence Erlbaum Associates",
        "doi": "10.1201/b12457",
        "url": "",
        "primary_topic": "T02",
        "secondary_topics": "T09, T03",
        "significance": "Introduced Cognitive Work Analysis (CWA) as a framework for analyzing complex sociotechnical systems. The abstraction hierarchy and work domain analysis methods are directly applicable to modeling learning environments as cognitive work systems.",
    },
    {
        "title": "Engineering Psychology and Human Performance",
        "authors": "Christopher D. Wickens; Justin G. Hollands; Simon Banbury; Raja Parasuraman",
        "year": 2013,
        "venue": "Pearson (4th edition)",
        "doi": "",
        "url": "",
        "primary_topic": "T02",
        "secondary_topics": "T01",
        "significance": "Standard textbook applying information-processing psychology to system design. Covers attention, perception, memory, and decision-making constraints that learning engineers must account for. The cognitive engineering perspective that bridges T01 (learning science) and T02 (systems engineering).",
    },
    {
        "title": "The Design of Everyday Things",
        "authors": "Donald A. Norman",
        "year": 2013,
        "venue": "Basic Books (revised edition)",
        "doi": "",
        "url": "",
        "primary_topic": "T02",
        "secondary_topics": "T03",
        "significance": "Foundational human-centered design text. Norman's principles (affordances, signifiers, mappings, feedback, conceptual models) are design heuristics for any learning system interface. The LE Toolkit explicitly references Norman's framework.",
    },
    {
        "title": "Joint Cognitive Systems: Foundations of Cognitive Systems Engineering",
        "authors": "Erik Hollnagel; David D. Woods",
        "year": 2005,
        "venue": "CRC Press",
        "doi": "10.1201/9781420038194",
        "url": "",
        "primary_topic": "T02",
        "secondary_topics": "T09",
        "significance": "Reframes human-machine systems as joint cognitive systems where performance emerges from the coupling of human and artifact. Directly relevant to adaptive learning systems where tutor and student form a joint cognitive unit.",
    },
    {
        "title": "Information Processing and Human-Machine Interaction: An Approach to Cognitive Engineering",
        "authors": "Jens Rasmussen",
        "year": 1986,
        "venue": "North-Holland",
        "doi": "",
        "url": "",
        "primary_topic": "T02",
        "secondary_topics": "T01, T09",
        "significance": "Introduced the skill-rule-knowledge (SRK) framework for modeling human performance at different levels of cognitive control. SRK is directly applicable to ITS design: different tutoring strategies are needed depending on whether the learner is operating at skill, rule, or knowledge level.",
    },
    {
        "title": "Sociotechnical Systems Theory as a Diagnostic Tool for Examining Underperformance in Integrated Learning Engineering Teams",
        "authors": "Steven J. Landry; Purdue Engineering Education",
        "year": 2022,
        "venue": "ASEE Annual Conference",
        "doi": "",
        "url": "https://peer.asee.org/",
        "primary_topic": "T02",
        "secondary_topics": "T15, T16",
        "significance": "Applies Emery and Trist's sociotechnical systems theory to diagnose breakdowns in integrated LE teams. One of the few papers explicitly connecting STS principles to learning engineering practice.",
    },
]

T02_REGISTRY = [
    {
        "content_type": "GL",
        "name": "MIL-STD-1472H: Human Engineering Design Criteria for Military Systems",
        "affiliation_or_venue": "U.S. Department of Defense",
        "url": "https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=36903",
        "primary_topic": "T02",
        "secondary_topics": "T10",
        "description": "DoD standard specifying human engineering design criteria for military systems, equipment, and facilities. The authoritative source for human factors requirements in defense training systems. Directly applicable to military LE system design.",
    },
    {
        "content_type": "GL",
        "name": "NASA Human Systems Integration Practitioner's Guide",
        "affiliation_or_venue": "NASA",
        "url": "https://www.nasa.gov/",
        "primary_topic": "T02",
        "secondary_topics": "T10, T08",
        "description": "NASA's operational guide to implementing HSI across the systems engineering lifecycle. Demonstrates how human-centered analysis (task analysis, workload, error analysis) integrates with traditional systems engineering milestones. Applicable to complex LE system development.",
    },
    {
        "content_type": "CO",
        "name": "Human Factors and Ergonomics Society",
        "affiliation_or_venue": "HFES",
        "url": "https://www.hfes.org/",
        "primary_topic": "T02",
        "secondary_topics": "T08",
        "description": "Professional society for human factors and ergonomics. Publishes Human Factors journal and organizes the annual HFES conference. The Training Systems technical group directly addresses LE-relevant human factors in instructional systems.",
    },
    {
        "content_type": "CO",
        "name": "INCOSE Systems Engineering Body of Knowledge (SEBoK)",
        "affiliation_or_venue": "International Council on Systems Engineering",
        "url": "https://sebokwiki.org/",
        "primary_topic": "T02",
        "secondary_topics": "T03, T16",
        "description": "Open wiki-based body of knowledge for systems engineering. Includes the Human Systems Integration knowledge area. The SE process framework (requirements, architecture, integration, verification) is the engineering process backbone that LE adapts for learning system development.",
    },
]


# ═══════════════════════════════════════════════════════════════════
# T05: Knowledge Representation
# ═══════════════════════════════════════════════════════════════════

T05_PAPERS = [
    {
        "title": "The Knowledge-Learning-Instruction Framework: Bridging the Science-Practice Chasm to Enhance Robust Student Learning",
        "authors": "Kenneth R. Koedinger; Albert T. Corbett; Charles Perfetti",
        "year": 2012,
        "venue": "Cognitive Science",
        "doi": "10.1111/j.1551-6709.2012.01245.x",
        "url": "",
        "primary_topic": "T05",
        "secondary_topics": "T01, T03",
        "significance": "THE bridge paper between knowledge representation and learning engineering. Introduces the KLI taxonomy: knowledge components (facts, skills, principles) mapped to learning events (instruction, practice, assessment) mapped to instructional principles. The most cited framework for LE knowledge representation.",
    },
    {
        "title": "Learning Factors Analysis — A General Method for Cognitive Model Comparison on Student Performance Data",
        "authors": "Hao Cen; Kenneth R. Koedinger; Brian Junker",
        "year": 2006,
        "venue": "International Conference on Intelligent Tutoring Systems (ITS 2006)",
        "doi": "10.1007/11774303_17",
        "url": "",
        "primary_topic": "T05",
        "secondary_topics": "T04, T06",
        "significance": "Introduced Learning Factors Analysis (LFA), a data-driven method for discovering and validating knowledge components from student performance data. Enables automated refinement of the knowledge model underlying an ITS — the practical operationalization of T05 for adaptive systems.",
    },
    {
        "title": "New Potentials for Data-Driven Intelligent Tutoring System Development and Optimization",
        "authors": "Kenneth R. Koedinger; Elizabeth A. McLaughlin; John C. Stamper",
        "year": 2014,
        "venue": "AI Magazine",
        "doi": "10.1609/aimag.v35i3.2548",
        "url": "",
        "primary_topic": "T05",
        "secondary_topics": "T04, T06",
        "significance": "Demonstrates how data-driven knowledge component discovery can optimize ITS. The paper shows that well-specified knowledge components predict student performance better than poorly specified ones — empirical validation that knowledge representation quality drives learning outcomes.",
    },
    {
        "title": "Advances in Intelligent Tutoring Systems",
        "authors": "Roger Nkambou; Jacqueline Bourdeau; Riichiro Mizoguchi",
        "year": 2010,
        "venue": "Springer (Studies in Computational Intelligence, vol 308)",
        "doi": "10.1007/978-3-642-14363-2",
        "url": "",
        "primary_topic": "T05",
        "secondary_topics": "T06",
        "significance": "Comprehensive volume on ITS architecture with dedicated chapters on domain ontology engineering, learner model ontology, and instructional planning ontology. Mizoguchi's chapter on ontological engineering for ITS is the most systematic treatment of knowledge representation for adaptive learning systems.",
    },
    {
        "title": "Instructional Factors Analysis: A Cognitive Model for Multiple Instructional Interventions",
        "authors": "Min Chi; Kenneth R. Koedinger; Gareth J. Gordon; Pamela Jordan; Kurt VanLehn",
        "year": 2011,
        "venue": "International Conference on Educational Data Mining (EDM 2011)",
        "doi": "",
        "url": "https://educationaldatamining.org/EDM2011/",
        "primary_topic": "T05",
        "secondary_topics": "T04, T01",
        "significance": "Extended Learning Factors Analysis to model the interaction between knowledge components and instructional methods. Shows that the same knowledge component may require different instructional approaches depending on its type — linking knowledge representation directly to instructional design decisions.",
    },
    {
        "title": "Educational Knowledge Graph: A Survey and Empirical Study",
        "authors": "Yupei Zhang; Renyu Zhu; Ming Li",
        "year": 2023,
        "venue": "IEEE Transactions on Knowledge and Data Engineering",
        "doi": "10.1109/TKDE.2023.3332789",
        "url": "",
        "primary_topic": "T05",
        "secondary_topics": "T04, T07",
        "significance": "Comprehensive survey of knowledge graph construction and application in education. Covers concept extraction, prerequisite relationship mining, and knowledge graph-based recommendation. Maps the state of the art in computational knowledge representation for learning systems.",
    },
]

T05_REGISTRY = [
    {
        "content_type": "TP",
        "name": "DataShop — LearnSphere Educational Data Repository",
        "affiliation_or_venue": "Carnegie Mellon University / LearnLab",
        "url": "https://pslcdatashop.web.cmu.edu/",
        "primary_topic": "T05",
        "secondary_topics": "T04, T06",
        "description": "World's largest open repository of educational interaction data. Stores student performance logs indexed by knowledge component models. The canonical infrastructure for empirical validation of knowledge representations — if your KC model predicts student learning curves well, it's a good representation.",
    },
    {
        "content_type": "TP",
        "name": "CTAT — Cognitive Tutor Authoring Tools",
        "affiliation_or_venue": "Carnegie Mellon University / HCII",
        "url": "https://github.com/CMUCTAT/CTAT",
        "primary_topic": "T05",
        "secondary_topics": "T06, T09",
        "description": "Authoring environment for building model-tracing and example-tracing cognitive tutors. Authors encode domain knowledge as production rules (model-tracing) or annotated examples (example-tracing). The primary tool for operationalizing expert knowledge into runnable knowledge component models.",
    },
    {
        "content_type": "GL",
        "name": "IMS Global Competency and Academic Standards Exchange (CASE)",
        "affiliation_or_venue": "1EdTech (formerly IMS Global)",
        "url": "https://www.1edtech.org/standards/case",
        "primary_topic": "T05",
        "secondary_topics": "T11, T16",
        "description": "Technical standard for expressing and exchanging competency frameworks, learning outcomes, and academic standards in machine-readable form. Enables interoperable knowledge representation across learning platforms — the infrastructure layer for competency-based knowledge models.",
    },
    {
        "content_type": "CO",
        "name": "Credential Engine / Credential Transparency Description Language (CTDL)",
        "affiliation_or_venue": "Credential Engine",
        "url": "https://credentialengine.org/",
        "primary_topic": "T05",
        "secondary_topics": "T16, T11",
        "description": "Open-source data standard and registry for describing credentials, competencies, and learning pathways. CTDL encodes 1,200+ properties for representing what people know and can do. The emerging national infrastructure for credential-level knowledge representation.",
    },
]


# ═══════════════════════════════════════════════════════════════════
# T09: Expert Knowledge Elicitation
# ═══════════════════════════════════════════════════════════════════

T09_PAPERS = [
    {
        "title": "Working Minds: A Practitioner's Guide to Cognitive Task Analysis",
        "authors": "Beth Crandall; Gary Klein; Robert R. Hoffman",
        "year": 2006,
        "venue": "MIT Press",
        "doi": "",
        "url": "https://mitpress.mit.edu/9780262532815/working-minds/",
        "primary_topic": "T09",
        "secondary_topics": "T02",
        "significance": "The definitive practitioner's guide to CTA methods. Covers critical decision method, knowledge audit, simulation interviews, and concept mapping — the core elicitation toolkit for learning engineers building expert models. Used in military, healthcare, and aviation training design.",
    },
    {
        "title": "The Cambridge Handbook of Expertise and Expert Performance",
        "authors": "K. Anders Ericsson; Neil Charness; Paul J. Feltovich; Robert R. Hoffman",
        "year": 2006,
        "venue": "Cambridge University Press",
        "doi": "10.1017/CBO9780511816796",
        "url": "",
        "primary_topic": "T09",
        "secondary_topics": "T01, T15",
        "significance": "Comprehensive handbook covering the science of expertise across domains. Establishes the theoretical foundation for why expert knowledge must be elicited (it's largely tacit and automatic) and what methods work. The scientific backbone for T09.",
    },
    {
        "title": "Cognitive Task Analysis",
        "authors": "Richard E. Clark; David F. Feldon; Jeroen J. G. van Merriënboer; Kenneth A. Yates; Sean Early",
        "year": 2008,
        "venue": "Handbook of Research on Educational Communications and Technology (Springer)",
        "doi": "10.1007/978-0-387-09657-6_34",
        "url": "",
        "primary_topic": "T09",
        "secondary_topics": "T03, T12",
        "significance": "Authoritative chapter connecting CTA methods directly to instructional design. Shows how elicited expert knowledge maps to training objectives, practice sequences, and assessment criteria. The bridge paper between T09 (elicitation) and T03 (LE process) / T12 (instructional design).",
    },
    {
        "title": "Varieties of Knowledge Elicitation Techniques",
        "authors": "Nancy J. Cooke",
        "year": 1994,
        "venue": "International Journal of Human-Computer Studies",
        "doi": "10.1006/ijhc.1994.1083",
        "url": "",
        "primary_topic": "T09",
        "secondary_topics": "T02",
        "significance": "Systematic taxonomy of knowledge elicitation techniques: interviews, observation, process tracing, conceptual techniques, and formal methods. Evaluates each technique's reliability, validity, and practicality. The most-cited methods review for KE in cognitive engineering.",
    },
    {
        "title": "Applied Cognitive Task Analysis (ACTA): A Practitioner's Toolkit for Understanding Cognitive Task Demands",
        "authors": "Laura G. Militello; Robert J. B. Hutton",
        "year": 1998,
        "venue": "Ergonomics",
        "doi": "10.1080/001401398186883",
        "url": "",
        "primary_topic": "T09",
        "secondary_topics": "T02, T03",
        "significance": "Introduced the streamlined ACTA methodology: task diagram, knowledge audit, simulation interview, and cognitive demands table. Designed to be usable by practitioners (not just researchers). Widely adopted in military and healthcare training design as a lightweight CTA alternative.",
    },
    {
        "title": "Sources of Power: How People Make Decisions",
        "authors": "Gary Klein",
        "year": 1998,
        "venue": "MIT Press",
        "doi": "",
        "url": "https://mitpress.mit.edu/9780262611466/sources-of-power/",
        "primary_topic": "T09",
        "secondary_topics": "T01, T02",
        "significance": "Established the Recognition-Primed Decision (RPD) model of expert decision-making. Shows that experts recognize patterns and simulate actions rather than comparing options analytically. Foundational for understanding what expert knowledge looks like and why traditional elicitation methods fail to capture it.",
    },
    {
        "title": "Protocol Analysis: Verbal Reports as Data",
        "authors": "K. Anders Ericsson; Herbert A. Simon",
        "year": 1993,
        "venue": "MIT Press (revised edition)",
        "doi": "",
        "url": "https://mitpress.mit.edu/9780262550239/protocol-analysis/",
        "primary_topic": "T09",
        "secondary_topics": "T17",
        "significance": "The methodological foundation for think-aloud protocol analysis. Ericsson and Simon established the conditions under which verbal reports are valid data about cognitive processes. Every CTA method that uses think-aloud builds on this work.",
    },
]

T09_REGISTRY = [
    {
        "content_type": "CO",
        "name": "Naturalistic Decision Making Association",
        "affiliation_or_venue": "NDM",
        "url": "https://www.naturalisticdecisionmaking.org/",
        "primary_topic": "T09",
        "secondary_topics": "T02",
        "description": "Research community studying expert decision-making in real-world conditions. NDM methods (critical decision method, cognitive task analysis) are the primary toolkit for eliciting expert knowledge in high-stakes training domains: military, healthcare, aviation, firefighting.",
    },
    {
        "content_type": "PP",
        "name": "Robert R. Hoffman",
        "affiliation_or_venue": "Institute for Human and Machine Cognition (IHMC)",
        "url": "https://www.ihmc.us/groups/rhoffman/",
        "primary_topic": "T09",
        "secondary_topics": "T02, T01",
        "description": "Pioneer of cognitive task analysis and knowledge elicitation methodology. Co-authored 'Working Minds' and the Cambridge Handbook of Expertise. Led development of CTA methods for military training at IHMC. Bridges expertise research with practical training system design.",
    },
    {
        "content_type": "PP",
        "name": "Gary Klein",
        "affiliation_or_venue": "MacroCognition LLC (formerly Klein Associates)",
        "url": "https://www.macrocognition.com/",
        "primary_topic": "T09",
        "secondary_topics": "T02, T01",
        "description": "Creator of the Recognition-Primed Decision model and Critical Decision Method. His naturalistic decision-making research established that expert performance depends on pattern recognition and mental simulation — defining what CTA must capture to build effective training.",
    },
]


def main() -> None:
    """Add curated gap-fill resources to the corpus."""
    pp_registry = load_json(PP_REGISTRY)
    ic_registry = load_json(IC_REGISTRY)
    papers = load_jsonl(PAPERS_JSONL)
    seeds = load_jsonl(SEEDS_JSONL)

    pp_next = next_id(pp_registry, "LE-PP-")
    ic_next = next_id(ic_registry, "LE-IC-")

    existing_pp_names = {normalize(r.get("name", "")) for r in pp_registry}
    existing_paper_titles = {normalize(p.get("title", "")) for p in papers}
    existing_seed_ids = {s.get("seed_id", "") for s in seeds}

    added = {"papers": 0, "registry": 0, "seeds": 0, "skipped": 0}

    # Add papers (all topics)
    for topic_papers in [T02_PAPERS, T05_PAPERS, T09_PAPERS]:
        for p in topic_papers:
            norm = normalize(p["title"])
            if norm in existing_paper_titles:
                added["skipped"] += 1
                continue
            rid = f"GF-{p['primary_topic']}-{added['papers']+1:03d}"
            row = {
                "resource_id": rid,
                "title": p["title"],
                "authors": p["authors"],
                "year": p["year"],
                "venue": p["venue"],
                "doi": p.get("doi", ""),
                "url": p.get("url", ""),
                "primary_topic": p["primary_topic"],
                "secondary_topics": p["secondary_topics"],
                "significance": p["significance"],
                "content_type": "AP",
                "source": f"gap-fill-curated:{p['primary_topic']}",
                "provenance_dataset": DATASET,
            }
            papers.append(row)
            existing_paper_titles.add(norm)
            added["papers"] += 1

            # Add seed query for OpenAlex expansion
            seed_id = f"GF-{p['primary_topic']}-{p['year']}"
            if seed_id not in existing_seed_ids:
                seeds.append({
                    "seed_id": seed_id,
                    "seed_kind": "gap_fill_curated",
                    "query_text": p["title"],
                    "doi": p.get("doi", ""),
                    "year": p["year"],
                })
                existing_seed_ids.add(seed_id)
                added["seeds"] += 1

    # Add registry entries (all topics)
    for topic_entries in [T02_REGISTRY, T05_REGISTRY, T09_REGISTRY]:
        for entry in topic_entries:
            norm = normalize(entry["name"])
            if norm in existing_pp_names:
                added["skipped"] += 1
                continue
            new_id = f"LE-PP-{pp_next:03d}"
            secondary = entry.get("secondary_topics", "")
            if isinstance(secondary, list):
                secondary = ", ".join(secondary)
            row = {
                "resource_id": new_id,
                "status": "APPROVED",
                "content_type": entry["content_type"],
                "name": entry["name"],
                "affiliation_or_venue": entry.get("affiliation_or_venue", ""),
                "url": entry.get("url", ""),
                "primary_topic": entry["primary_topic"],
                "secondary_topics": secondary,
                "description": entry["description"],
                "notes": f"Gap-fill curated ({DATASET}). Primary topic: {entry['primary_topic']}.",
            }
            pp_registry.append(row)
            existing_pp_names.add(norm)
            pp_next += 1
            added["registry"] += 1

    write_json(PP_REGISTRY, pp_registry)
    write_jsonl(PAPERS_JSONL, papers)
    write_jsonl(SEEDS_JSONL, seeds)

    print(f"Gap-fill complete (provenance: {DATASET}):")
    for key, val in sorted(added.items()):
        print(f"  {key}: {val}")
    print(f"\nFinal counts:")
    print(f"  programs_people_registry: {len(pp_registry)}")
    print(f"  academic_papers: {len(papers)}")
    print(f"  expansion_seed_queries: {len(seeds)}")


if __name__ == "__main__":
    main()
