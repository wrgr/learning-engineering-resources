"""Tests for people record normalization, upsert logic, and search."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_people import (
    _FALSE_POSITIVE_PATTERNS,
    _next_person_id,
    _split_name,
    auto_triage_gh,
    normalize_github_record,
    normalize_jsonl_record,
    normalize_linkedin_pb_record,
    upsert_record,
)
from search_people import _matches, search


# ── _split_name ───────────────────────────────────────────────────────────────

def test_split_name_two_parts():
    assert _split_name("Jane Doe") == ("Jane", "Doe")

def test_split_name_three_parts():
    assert _split_name("Mary Jo Smith") == ("Mary", "Jo Smith")

def test_split_name_single_token():
    first, last = _split_name("mononym")
    assert first == ""
    assert last == "mononym"

def test_split_name_empty():
    assert _split_name("") == ("", "")


# ── _next_person_id ───────────────────────────────────────────────────────────

def test_next_id_empty_registry():
    assert _next_person_id([]) == "LE-P-001"

def test_next_id_increments():
    existing = [{"person_id": "LE-P-003"}, {"person_id": "LE-P-001"}]
    assert _next_person_id(existing) == "LE-P-004"


# ── auto_triage_gh ────────────────────────────────────────────────────────────

def test_triage_approved_on_keyword():
    triage, reason = auto_triage_gh("I work in learning engineering", "jdoe")
    assert triage == "CANDIDATE"
    assert "learning engineering" in reason

def test_triage_needs_review_no_keywords():
    triage, reason = auto_triage_gh("I like hiking", "outdoorsy")
    assert triage == "NEEDS_REVIEW"


# ── _FALSE_POSITIVE_PATTERNS ──────────────────────────────────────────────────

@pytest.mark.parametrize("headline", [
    # ML/AI subdisciplines
    "Machine Learning Engineer @ Google",
    "Deep Learning Engineer | PyTorch",
    "Reinforcement Learning Engineer at OpenAI",
    "Transfer Learning Researcher",
    "Federated Learning Engineer",
    "Representation Learning Engineer",
    "Contrastive Learning Engineer",
    "Self-supervised Learning Engineer",
    "ML Engineer at Meta",
    "NLP Engineer | Transformers",
    "Computer Vision Engineer",
    "MLOps Engineer",
    # Robotics
    "Robotics Learning Engineer | ROS",
    # Continuous-learner adjective phrases
    "Fast-learning engineer passionate about cloud",
    "Quick-learning engineer transitioning to ML",
    "Ever learning engineer building great things",
    "Keep Learning Engineer; Apache Pinot committer",
    "Continuously learning engineer",
    # Typo variant captured from real data
    "Senior Software & Machile Learning Engineer",
])
def test_false_positive_patterns_match(headline):
    assert _FALSE_POSITIVE_PATTERNS.search(headline), f"Expected match for: {headline!r}"


@pytest.mark.parametrize("headline", [
    "Learning Engineer at Carnegie Mellon University",
    "Senior Learning Engineer | Bridging Learning Science & Technology",
    "STEM Learning Engineer | Adaptive Learning (Area9 Rhapsode)",
    "Lead Digital Learning Engineer / Senior Front-End Developer",
    "Digital Learning Engineer | EdTech | AI",
    "E-learning Engineer at TransPerfect",
    "Learning Engineer and Adjunct Faculty",
    "AF Career Development Academy, Learning Engineer",
])
def test_false_positive_patterns_do_not_match_valid(headline):
    assert not _FALSE_POSITIVE_PATTERNS.search(headline), f"Unexpected match for: {headline!r}"


# ── normalize_linkedin_pb_record triage ───────────────────────────────────────

def test_linkedin_pb_deep_learning_flagged():
    rec = normalize_linkedin_pb_record(
        display_name="Alex Smith", headline="Deep Learning Engineer | PyTorch | NLP",
        location="San Francisco, CA", company="Google", job_title="Deep Learning Engineer",
        industry="Internet", lists=["le-global-keyword"], retrieved_date="2026-04-14",
    )
    assert rec["triage"] == "NEEDS_REVIEW"

def test_linkedin_pb_valid_le_is_candidate():
    rec = normalize_linkedin_pb_record(
        display_name="Jane Doe", headline="Learning Engineer at Carnegie Mellon University",
        location="Pittsburgh, PA", company="CMU", job_title="Learning Engineer",
        industry="Higher Education", lists=["le-global-keyword"], retrieved_date="2026-04-14",
    )
    assert rec["triage"] == "CANDIDATE"

def test_linkedin_pb_triage_override_respected():
    rec = normalize_linkedin_pb_record(
        display_name="Bob", headline="Learning Engineer",
        location="US", company="Acme", job_title="LE",
        industry="", lists=["le-global-keyword"],
        triage_override="NEEDS_REVIEW", retrieved_date="2026-04-14",
    )
    assert rec["triage"] == "NEEDS_REVIEW"
    assert rec["triage_reason"] == "manual override"


# ── normalize_github_record ───────────────────────────────────────────────────

def test_normalize_strips_at_from_company():
    rec = {"login": "jdoe", "name": "Jane Doe", "company": "@acme", "bio": ""}
    result = normalize_github_record(rec, retrieved_date="2026-04-14")
    assert result["organization"] == "acme"

def test_normalize_fallback_display_name():
    rec = {"login": "jdoe", "name": None}
    result = normalize_github_record(rec, retrieved_date="2026-04-14")
    assert result["display_name"] == "jdoe"

def test_normalize_provenance_fields():
    rec = {"login": "jdoe", "html_url": "https://github.com/jdoe"}
    result = normalize_github_record(rec, query="learning engineering", retrieved_date="2026-04-14")
    assert result["provenance"]["source"] == "github_search"
    assert result["provenance"]["query"] == "learning engineering"
    assert result["provenance"]["retrieved_date"] == "2026-04-14"


# ── upsert_record ─────────────────────────────────────────────────────────────

def test_upsert_new_record():
    rec = {"github_login": "jdoe", "display_name": "Jane Doe", "status": "CANDIDATE"}
    result = upsert_record(rec, [])
    assert len(result) == 1
    assert result[0]["person_id"] == "LE-P-001"

def test_upsert_updates_existing():
    existing = [{"github_login": "jdoe", "person_id": "LE-P-001", "status": "APPROVED"}]
    updated = {"github_login": "jdoe", "display_name": "Jane Doe Updated", "status": "CANDIDATE"}
    result = upsert_record(updated, existing)
    assert len(result) == 1
    assert result[0]["person_id"] == "LE-P-001"
    assert result[0]["status"] == "APPROVED"   # existing status preserved
    assert result[0]["display_name"] == "Jane Doe Updated"


# ── _matches / search ─────────────────────────────────────────────────────────

SAMPLE_RECORDS = [
    {"display_name": "Jane Doe", "organization": "MIT", "location": "Cambridge, MA",
     "job_title": "Researcher", "primary_topic": "T13", "triage": "APPROVED",
     "status": "CANDIDATE", "last_name": "Doe", "first_name": "Jane"},
    {"display_name": "Bob Smith", "organization": "Stanford", "location": "Palo Alto, CA",
     "job_title": "Professor", "primary_topic": "T02", "triage": "NEEDS_REVIEW",
     "status": "CANDIDATE", "last_name": "Smith", "first_name": "Bob"},
]

def test_matches_by_name():
    assert _matches(SAMPLE_RECORDS[0], {"display_name": "jane"})
    assert not _matches(SAMPLE_RECORDS[1], {"display_name": "jane"})

def test_matches_multiple_filters():
    assert _matches(SAMPLE_RECORDS[0], {"organization": "mit", "triage": "APPROVED"})
    assert not _matches(SAMPLE_RECORDS[0], {"organization": "mit", "triage": "NEEDS_REVIEW"})


# ── normalize_jsonl_record ────────────────────────────────────────────────────

def test_normalize_jsonl_rg_record():
    rec = {
        "query_id": "Q002",
        "source": "RG",
        "raw": {
            "name": "Gautam Yadav",
            "rg_title": "Learning Engineer",
            "affiliation": "Carnegie Mellon University",
            "rg_url": "https://www.researchgate.net/profile/Gautam-Yadav-5",
        },
        "triage": "yes",
        "triage_reason": "Explicit RG profile title",
    }
    result = normalize_jsonl_record(rec, retrieved_date="2026-04-14")
    assert result["display_name"] == "Gautam Yadav"
    assert result["job_title"] == "Learning Engineer"
    assert result["organization"] == "Carnegie Mellon University"
    assert result["triage"] == "APPROVED"
    assert result["status"] == "APPROVED"
    assert result["provenance"]["source"] == "researchgate"
    assert result["provenance"]["query"] == "Q002"


def test_normalize_jsonl_gs_record():
    rec = {
        "query_id": "Q003",
        "source": "GS",
        "raw": {
            "name": "Lauren Totino",
            "gs_title": "Learning Engineer",
            "affiliation": "Massachusetts Institute of Technology",
            "gs_url": "https://scholar.google.com/citations?[Lauren-Totino]",
        },
        "triage": "yes",
    }
    result = normalize_jsonl_record(rec, retrieved_date="2026-04-14")
    assert result["job_title"] == "Learning Engineer"
    assert result["provenance"]["source"] == "google_scholar"
    assert result["triage"] == "APPROVED"


def test_normalize_jsonl_probable_maps_to_candidate():
    rec = {
        "query_id": "Q002",
        "source": "RG",
        "raw": {"name": "Some Person", "rg_title": "Learning Engineer"},
        "triage": "probable",
    }
    result = normalize_jsonl_record(rec, retrieved_date="2026-04-14")
    assert result["triage"] == "CANDIDATE"
    assert result["status"] == "CANDIDATE"


def test_normalize_jsonl_no_maps_to_rejected():
    rec = {
        "query_id": "Q002",
        "source": "RG",
        "raw": {"name": "Rod Roscoe", "rg_title": "Professor (Associate)"},
        "triage": "no",
    }
    result = normalize_jsonl_record(rec, retrieved_date="2026-04-14")
    assert result["triage"] == "REJECTED"
    assert result["status"] == "ARCHIVED"


# ── upsert_record display_name dedup ──────────────────────────────────────────

def test_upsert_dedup_by_display_name():
    """Records with no github_login should dedup on display_name (case-insensitive)."""
    existing = [{"github_login": "", "display_name": "Gautam Yadav", "person_id": "LE-P-001", "status": "APPROVED"}]
    new_rec = {"github_login": "", "display_name": "Gautam Yadav", "status": "CANDIDATE"}
    result = upsert_record(new_rec, existing)
    assert len(result) == 1
    assert result[0]["person_id"] == "LE-P-001"
    assert result[0]["status"] == "APPROVED"  # existing status preserved


def test_upsert_display_name_case_insensitive():
    existing = [{"github_login": "", "display_name": "GAUTAM YADAV", "person_id": "LE-P-001", "status": "APPROVED"}]
    new_rec = {"github_login": "", "display_name": "Gautam Yadav", "status": "CANDIDATE"}
    result = upsert_record(new_rec, existing)
    assert len(result) == 1


def test_upsert_different_names_creates_new_record():
    existing = [{"github_login": "", "display_name": "Gautam Yadav", "person_id": "LE-P-001", "status": "APPROVED"}]
    new_rec = {"github_login": "", "display_name": "Lauren Totino", "status": "CANDIDATE"}
    result = upsert_record(new_rec, existing)
    assert len(result) == 2
    assert result[1]["person_id"] == "LE-P-002"
