from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Artifact:
    type: str
    value: str
    normalized: str
    platform: str
    confidence: str
    context: str
    evidence: str
    location: str
    method: str
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
