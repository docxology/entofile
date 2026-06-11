"""Citation scholarship gates for the 0.4 manuscript.

These tests keep load-bearing security and related-work claims attached to
primary sources, and prevent RFC 8785 from drifting into an implementation
claim before JSON canonicalization support exists.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "manuscript"
BIB = MANUSCRIPT / "references.bib"


NEW_REQUIRED_KEYS = frozenset(
    {
        "mcgrew2004gcm",
        "joux2006forbidden",
        "bock2016nonce",
        "rfc5116",
        "rfc8452",
        "nistfips1804",
        "nistfips197",
        "nistsp80057pt1r5",
        "nist2022sp800161r1",
        "rfc8785",
        "haber1991timestamp",
        "merkle1988digital",
        "cwe409",
        "cwe22",
        "soilandreyes2022rocrate",
        "w3cprovo2013",
        "rfc9052",
        "kaitai2026",
        "sandve2013reproducible",
        "wilson2017goodenough",
        "acm2024artifactbadging",
        "torresarias2019intoto",
        "ccsds2024oais",
        "premis2015",
    }
)

UPGRADED_REQUIRED_FIELDS = {
    "dworkin2007gcm": frozenset({"doi", "url"}),
    "krawczyk2010hkdf": frozenset({"doi", "url"}),
    "nikitin2019purb": frozenset({"doi", "url"}),
    "wilkinson2016fair": frozenset({"doi", "url"}),
    "w3cprov2013": frozenset({"howpublished"}),
    "nist2024mlkem": frozenset({"doi", "url"}),
    "nist2024mldsa": frozenset({"doi", "url"}),
    "rfc8452": frozenset({"doi", "url"}),
    "nistsp80057pt1r5": frozenset({"doi", "url"}),
    "nist2022sp800161r1": frozenset({"doi", "url"}),
    "sandve2013reproducible": frozenset({"doi", "url"}),
    "wilson2017goodenough": frozenset({"doi", "url"}),
    "bagit2018": frozenset({"doi", "url"}),
    "ccsds2024oais": frozenset({"url"}),
    "premis2015": frozenset({"url"}),
}


def _bib_text() -> str:
    return BIB.read_text(encoding="utf-8")


def _bib_entries() -> dict[str, str]:
    text = _bib_text()
    matches = list(re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,", text))
    entries: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries[match.group(1)] = text[start:end]
    return entries


def _manuscript_sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(MANUSCRIPT.glob("[0-9][0-9]*.md"))
        if path.name != "99_references.md"
    }


def _manuscript_text() -> str:
    return "\n".join(_manuscript_sources().values())


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _cited_keys(text: str) -> set[str]:
    return set(re.findall(r"@([A-Za-z0-9_:-]+)", text))


def test_required_scholarship_keys_exist_in_bibliography() -> None:
    entries = _bib_entries()
    missing = sorted(NEW_REQUIRED_KEYS - set(entries))
    assert not missing, f"Missing bibliography keys: {missing}"


def test_upgraded_entries_keep_primary_doi_or_url_metadata() -> None:
    entries = _bib_entries()
    missing: list[str] = []
    for key, fields in UPGRADED_REQUIRED_FIELDS.items():
        body = entries.get(key, "")
        for field in fields:
            if not re.search(rf"^\s*{field}\s*=", body, flags=re.IGNORECASE | re.MULTILINE):
                missing.append(f"{key}.{field}")
    assert not missing, f"Missing required bibliography fields: {missing}"


def test_nikitin_purb_entry_uses_primary_author_metadata() -> None:
    body = _bib_entries()["nikitin2019purb"]
    assert "Ford, Bryan" in body
    assert "Troncoso" not in body


def test_new_load_bearing_keys_are_cited_in_renderable_manuscript() -> None:
    cited = _cited_keys(_manuscript_text())
    missing = sorted(NEW_REQUIRED_KEYS - cited)
    assert not missing, "New required keys must be cited in manuscript body: " + ", ".join(missing)


def test_weak_rocrate_note_is_not_used_in_renderable_manuscript() -> None:
    assert "soiland2016research" not in _cited_keys(_manuscript_text())


def test_rfc8785_is_a_limit_not_claimed_jcs_compliance() -> None:
    text = _manuscript_text()
    normalized = text.lower()
    allowed_limit_phrases = (
        "does not implement or claim jcs compliance",
        "does not make ento rfc 8785-compliant",
    )
    for phrase in allowed_limit_phrases:
        normalized = normalized.replace(phrase, "")

    forbidden = (
        r"\bjcs[- ]compliant\b",
        r"\brfc\s*8785[- ]compliant\b",
        r"\bimplements\s+(?:the\s+)?(?:json canonicalization scheme|jcs|rfc\s*8785)\b",
        r"\bcomplies\s+with\s+(?:jcs|rfc\s*8785)\b",
    )
    hits = [pattern for pattern in forbidden if re.search(pattern, normalized)]
    assert not hits, f"Manuscript makes a positive JCS/RFC8785 compliance claim: {hits}"

    methodology = (MANUSCRIPT / "02_methodology.md").read_text(encoding="utf-8")
    proof = (MANUSCRIPT / "02b_proof_and_observability.md").read_text(encoding="utf-8")
    proof_one_line = " ".join(proof.split())
    assert "exact JSON bytes emitted by `manifest_to_json`" in methodology
    assert "does not implement or claim JCS compliance" in proof_one_line


def test_aes_gcm_siv_is_only_future_work_not_implemented_claim() -> None:
    text = _manuscript_text()
    lowered = text.lower()
    forbidden = (
        "implements aes-gcm-siv",
        "uses aes-gcm-siv",
        "default aes-gcm-siv",
        "aes-gcm-siv profile",
    )
    hits = [phrase for phrase in forbidden if phrase in lowered]
    assert not hits, f"Manuscript implies implemented AES-GCM-SIV: {hits}"

    methodology = (MANUSCRIPT / "02_methodology.md").read_text(encoding="utf-8")
    limitations = (MANUSCRIPT / "08_limitations_and_threat_model.md").read_text(
        encoding="utf-8"
    )
    assert "not implemented in ENTO {{FORMAT_VERSION}}" in methodology
    assert "not an ENTO {{FORMAT_VERSION}} behavior" in _one_line(limitations)


def test_reproducibility_and_supply_chain_scholarship_are_cited_in_load_bearing_sections() -> None:
    setup = (MANUSCRIPT / "05_experimental_setup.md").read_text(encoding="utf-8")
    reproducibility = (MANUSCRIPT / "06_reproducibility.md").read_text(
        encoding="utf-8"
    )
    security = (MANUSCRIPT / "02c_security_verification.md").read_text(
        encoding="utf-8"
    )
    limitations = (MANUSCRIPT / "08_limitations_and_threat_model.md").read_text(
        encoding="utf-8"
    )
    for key in ("sandve2013reproducible", "wilson2017goodenough"):
        assert f"@{key}" in setup
        assert f"@{key}" in reproducibility
    assert "@acm2024artifactbadging" in setup
    assert "@acm2024artifactbadging" in reproducibility
    for key in ("nistsp80057pt1r5", "nist2022sp800161r1", "torresarias2019intoto"):
        assert f"@{key}" in security
        assert f"@{key}" in limitations


def test_preservation_scholarship_is_cited_without_archive_overclaim() -> None:
    intro = (MANUSCRIPT / "01_introduction.md").read_text(encoding="utf-8")
    related = (MANUSCRIPT / "07_scope_and_related_work.md").read_text(
        encoding="utf-8"
    )
    limitations = (MANUSCRIPT / "08_limitations_and_threat_model.md").read_text(
        encoding="utf-8"
    )
    research_note = (ROOT / "docs" / "research" / "related_formats.md").read_text(
        encoding="utf-8"
    )

    for text in (intro, related, limitations, research_note):
        assert "@ccsds2024oais" in text
        assert "@premis2015" in text

    combined = _one_line("\n".join((intro, related, limitations, research_note))).lower()
    for required_boundary in (
        "does not replace",
        "not an archival repository",
        "external to the ento file format",
        "file-format layer",
    ):
        assert required_boundary in combined

    forbidden = (
        "ento implements oais",
        "ento is an oais",
        "ento implements premis",
        "ento is premis",
        "ento provides repository certification",
    )
    offenders = [phrase for phrase in forbidden if phrase in combined]
    assert not offenders, f"Preservation scholarship overclaim: {offenders}"
