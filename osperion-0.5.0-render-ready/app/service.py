from __future__ import annotations
from .extract import extract
from .db import correlate, save_report, compare_image_hashes, save_image
from .image_hash import hash_image

def analyze_text(text: str, filename: str = "input", platform: str = "auto", investigation_id: int | None = None) -> dict:
    report = extract(text, filename, platform)
    report["investigation_id"] = investigation_id
    report["correlations"] = correlate(report, investigation_id=investigation_id)
    report["correlation_count"] = len(report["correlations"])
    return report

def persist(report: dict, filename: str, investigation_id: int | None = None) -> int:
    return save_report(report, filename, investigation_id=investigation_id)


def analyze_image(data: bytes, investigation_id: int | None = None) -> dict:
    hashes = hash_image(data)
    matches = compare_image_hashes(hashes, investigation_id=investigation_id)
    return {**hashes, "investigation_id": investigation_id, "matches": matches, "match_count": len(matches)}


def persist_image(data: bytes, filename: str, label: str, platform: str, investigation_id: int) -> int:
    return save_image(data, filename, label, platform, investigation_id)
