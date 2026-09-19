from __future__ import annotations

import hashlib
import math
from io import BytesIO

from PIL import Image, UnidentifiedImageError

try:  # Optional acceleration/compatibility with the imagehash package.
    import imagehash as _imagehash
except ImportError:  # The project also has a small built-in fallback.
    _imagehash = None


class ImageHashError(ValueError):
    pass


def _fallback_phash(img: Image.Image) -> str:
    """Compact 64-bit perceptual hash compatible with the project's distance model.

    Uses a 32x32 grayscale image, 2-D DCT, and the median of the low-frequency
    8x8 coefficients (DC excluded). It is intentionally self-contained so the
    application still works if the optional ImageHash dependency is unavailable.
    """
    gray = img.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    n = 32
    cos_table = [[math.cos(math.pi * (2 * x + 1) * u / (2 * n)) for x in range(n)] for u in range(8)]
    coeffs = []
    for u in range(8):
        au = math.sqrt(1 / n) if u == 0 else math.sqrt(2 / n)
        for v in range(8):
            if u == 0 and v == 0:
                continue
            av = math.sqrt(1 / n) if v == 0 else math.sqrt(2 / n)
            total = 0.0
            for x in range(n):
                row = pixels[x * n:(x + 1) * n]
                cx = cos_table[u][x]
                for y in range(n):
                    total += row[y] * cx * cos_table[v][y]
            coeffs.append(au * av * total)
    ordered = sorted(coeffs)
    median = ordered[len(ordered) // 2]
    value = 0
    for c in coeffs:
        value = (value << 1) | int(c > median)
    return f"{value:016x}"


def _fallback_dhash(img: Image.Image) -> str:
    gray = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    px = list(gray.getdata())
    value = 0
    for y in range(8):
        for x in range(8):
            value = (value << 1) | int(px[y * 9 + x] > px[y * 9 + x + 1])
    return f"{value:016x}"


def hash_image(data: bytes) -> dict:
    if not data:
        raise ImageHashError("Image file is empty.")
    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        with Image.open(BytesIO(data)) as img:
            rgb = img.convert("RGB")
            if _imagehash is not None:
                phash = str(_imagehash.phash(rgb))
                dhash = str(_imagehash.dhash(rgb))
            else:
                phash = _fallback_phash(rgb)
                dhash = _fallback_dhash(rgb)
            width, height = rgb.size
            fmt = (img.format or "unknown").lower()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageHashError("The uploaded file is not a valid supported image.") from exc

    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "phash": phash,
        "dhash": dhash,
        "width": width,
        "height": height,
        "format": fmt,
        "bytes": len(data),
    }


def phash_distance(a: str, b: str) -> int:
    try:
        if _imagehash is not None:
            return int(_imagehash.hex_to_hash(a) - _imagehash.hex_to_hash(b))
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except Exception as exc:
        raise ImageHashError("Invalid perceptual hash.") from exc


def classify_distance(distance: int) -> str:
    if distance == 0:
        return "exact"
    if distance <= 5:
        return "very_close"
    if distance <= 10:
        return "similar"
    return "not_similar"
