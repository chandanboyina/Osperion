from __future__ import annotations
import hashlib
import html
import json
import re
from urllib.parse import urlparse, urlunparse
from .models import Artifact

URL_RE = re.compile(r'https?://[^\s<>"\'\\]+', re.I)
USERNAME_KEYS = re.compile(r'(?i)["\'](?:username|screen_name|handle)["\']\s*:\s*["\']([^"\']{1,100})["\']')
ID_KEYS = re.compile(r'(?i)["\'](user_?id|userid|profile_?id|member_?id|media_?id|post_?id|comment_?id|object_?id|page_?id|entityurn|objecturn|profileurn|trackingurn|pk)["\']\s*:\s*["\']?([^"\',}\s]+)')
URN_RE = re.compile(r'urn:li:[A-Za-z0-9_()\-,:]+')
NUMERIC_ID_RE = re.compile(r'(?<![\w])\d{6,25}(?![\w])')
IMG_RE = re.compile(r'(?i)(?:src|href|url|image|profile_pic_url|thumbnail|avatar)["\']?\s*[:=]\s*["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']')

PLATFORMS = {
    "instagram": ("instagram.com", "cdninstagram.com", "fbcdn.net"),
    "facebook": ("facebook.com", "fbcdn.net", "fbsbx.com"),
    "linkedin": ("linkedin.com",),
    "x": ("x.com", "twitter.com", "twimg.com"),
    "reddit": ("reddit.com", "redd.it", "redditmedia.com"),
    "tiktok": ("tiktok.com", "tiktokcdn.com"),
    "youtube": ("youtube.com", "youtu.be", "googlevideo.com"),
    "github": ("github.com", "githubusercontent.com"),
    "threads": ("threads.net",),
    "pinterest": ("pinterest.com", "pinimg.com"),
    "telegram": ("t.me", "telegram.org"),
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def detect_platform(text: str, explicit: str | None = None) -> str:
    if explicit and explicit != "auto":
        return explicit.lower()
    low = text.lower()
    for name, domains in PLATFORMS.items():
        if any(d in low for d in domains):
            return name
    return "unknown"


def normalize_url(value: str) -> str:
    value = html.unescape(value).strip().rstrip(".,;)]}")
    try:
        p = urlparse(value)
        host = p.hostname.lower() if p.hostname else ""
        # Query parameters can be transient CDN signatures. Preserve the path but
        # remove common tracking/signature parameters for comparison.
        if host and any(x in host for x in ("cdn", "fbcdn", "twimg", "pinimg", "tiktokcdn", "githubusercontent")):
            return urlunparse((p.scheme.lower(), host, p.path, "", "", ""))
        return urlunparse((p.scheme.lower(), host, p.path.rstrip("/"), "", p.query, ""))
    except Exception:
        return value


def classify_url(url: str) -> tuple[str, str]:
    host = (urlparse(url).hostname or "").lower()
    path = urlparse(url).path.lower()
    cdn_hosts = ("cdn", "fbcdn", "twimg", "pinimg", "tiktokcdn", "githubusercontent", "redd.it")
    if any(x in host for x in cdn_hosts) or any(x in path for x in ("/cdn", "/media", "/images", "/profile_pic")):
        return "cdn_url", "medium"
    if re.search(r'\.(jpg|jpeg|png|webp|gif|mp4|mov)(?:$|\?)', path):
        return "media_url", "medium"
    return "url", "observed"


def extract(text: str, filename: str = "input", explicit_platform: str | None = None) -> dict:
    platform = detect_platform(text, explicit_platform)
    artifacts: list[Artifact] = []
    seen: set[tuple[str, str]] = set()

    def add(a: Artifact):
        key = (a.type, a.normalized)
        if not a.value or key in seen:
            return
        seen.add(key)
        artifacts.append(a)

    # URLs are always useful evidence and get conservative classification.
    for i, m in enumerate(URL_RE.finditer(text)):
        raw = m.group(0)
        typ, conf = classify_url(raw)
        add(Artifact(typ, raw, normalize_url(raw), platform, conf, "URL observed in supplied evidence", filename, str(m.start()), "url-regex"))

    # Structured key/value identifiers.
    for m in ID_KEYS.finditer(text):
        key, value = m.group(1), m.group(2).strip('"\'')
        lk = key.lower()
        if lk in {"entityurn", "objecturn", "profileurn", "trackingurn"} or value.startswith("urn:"):
            typ, conf = "urn", "high"
        elif "media" in lk or lk == "pk":
            typ, conf = "media_id", "medium"
        elif "comment" in lk:
            typ, conf = "comment_id", "high"
        elif "post" in lk or "object" in lk:
            typ, conf = "object_id", "high"
        elif "profile" in lk or "user" in lk or "member" in lk or "page" in lk:
            typ, conf = "profile_id", "high"
        else:
            typ, conf = "identifier", "observed"
        add(Artifact(typ, value, value, platform, conf, f"structured field: {key}", filename, str(m.start()), "json-key-regex", key))

    for m in URN_RE.finditer(text):
        add(Artifact("urn", m.group(0), m.group(0), platform, "high", "LinkedIn-style URN observed", filename, str(m.start()), "urn-regex"))

    for m in USERNAME_KEYS.finditer(text):
        value = m.group(1).strip()
        if value and value.lower() not in {"null", "none", "undefined"}:
            add(Artifact("username", value, value.casefold(), platform, "low", "username-like structured field; relationship unknown", filename, str(m.start()), "username-key-regex"))

    # Candidate numeric identifiers only when not already captured. Never label as profile ID.
    for m in NUMERIC_ID_RE.finditer(text):
        value = m.group(0)
        if len(value) > 18 or value.startswith("20") and len(value) == 13:
            continue
        add(Artifact("numeric_candidate", value, value, platform, "low", "numeric candidate; meaning not established", filename, str(m.start()), "numeric-regex"))

    # Common image/profile URL fields.
    for m in IMG_RE.finditer(text):
        raw = html.unescape(m.group(1))
        typ, conf = classify_url(raw)
        add(Artifact(typ, raw, normalize_url(raw), platform, conf, "image/media URL field", filename, str(m.start()), "image-url-regex"))

    # Context hints from visible JSON keys; useful for UI but not treated as relationships.
    context_tokens = []
    for token in ("profile", "user", "media", "post", "comment", "suggest", "recommended", "viewer", "actor", "author"):
        if re.search(rf'(?i)\b{re.escape(token)}\b', text):
            context_tokens.append(token)
    return {
        "schema_version": "1.0",
        "parser_version": "0.5.0",
        "input_sha256": sha256_text(text),
        "input_bytes": len(text.encode("utf-8", errors="replace")),
        "platform": platform,
        "artifact_count": len(artifacts),
        "context_hints": context_tokens[:20],
        "artifacts": [a.as_dict() for a in artifacts],
    }
