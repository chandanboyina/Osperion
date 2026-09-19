from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from .config import db_path, data_dir, get_retention_days
from .image_hash import hash_image, phash_distance, classify_distance

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS investigations (
  investigation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
  evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
  investigation_id INTEGER,
  sha256 TEXT NOT NULL,
  filename TEXT NOT NULL,
  platform TEXT NOT NULL,
  created_at TEXT NOT NULL,
  artifact_count INTEGER NOT NULL,
  parser_version TEXT NOT NULL,
  FOREIGN KEY(investigation_id) REFERENCES investigations(investigation_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  value TEXT NOT NULL,
  normalized TEXT NOT NULL,
  platform TEXT NOT NULL,
  confidence TEXT NOT NULL,
  context TEXT NOT NULL,
  location TEXT NOT NULL,
  method TEXT NOT NULL,
  detail TEXT NOT NULL,
  FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS investigation_entries (
  entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
  investigation_id INTEGER NOT NULL,
  entry_type TEXT NOT NULL CHECK(entry_type IN ('note','report','remark')),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(investigation_id) REFERENCES investigations(investigation_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_artifacts_norm ON artifacts(normalized);
CREATE INDEX IF NOT EXISTS idx_artifacts_type_norm ON artifacts(type, normalized);
CREATE INDEX IF NOT EXISTS idx_evidence_created ON evidence(created_at);
CREATE INDEX IF NOT EXISTS idx_entries_investigation ON investigation_entries(investigation_id, updated_at);
"""

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    # Run only the base tables first. This is deliberately ordered so an older
    # 0.2.x database (whose evidence table did not have investigation_id) can
    # be opened safely. Creating an index on a missing column would otherwise
    # abort initialization before the migration gets a chance to run.
    conn.executescript(SCHEMA)

    # Migration from 0.2.x: add investigation_id to an existing evidence table.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(evidence)").fetchall()}
    if "investigation_id" not in cols:
        conn.execute(
            "ALTER TABLE evidence ADD COLUMN investigation_id INTEGER "
            "REFERENCES investigations(investigation_id) ON DELETE SET NULL"
        )

    # Image hashes are kept as local investigation assets. The table is created
    # after legacy migrations so existing 0.2/0.3 databases remain usable.
    conn.execute("""CREATE TABLE IF NOT EXISTS image_assets (
      image_id INTEGER PRIMARY KEY AUTOINCREMENT,
      investigation_id INTEGER NOT NULL,
      filename TEXT NOT NULL,
      label TEXT NOT NULL DEFAULT '',
      platform TEXT NOT NULL DEFAULT 'unknown',
      sha256 TEXT NOT NULL,
      phash TEXT NOT NULL,
      dhash TEXT NOT NULL,
      width INTEGER NOT NULL,
      height INTEGER NOT NULL,
      byte_size INTEGER NOT NULL,
      stored_path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(investigation_id) REFERENCES investigations(investigation_id) ON DELETE CASCADE
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_image_phash ON image_assets(phash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_image_investigation ON image_assets(investigation_id, created_at)")

    # Indexes that depend on migrated columns are created only after migration.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_investigation ON evidence(investigation_id)")
    conn.commit()
    return conn

def cleanup() -> int:
    """Remove only temporary, unassigned evidence.

    Investigation evidence is permanent by design. Once evidence is explicitly
    saved to an investigation, retention cleanup must never delete it.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=get_retention_days())).isoformat()
    with connect() as c:
        cur = c.execute(
            "DELETE FROM evidence WHERE investigation_id IS NULL AND created_at < ?",
            (cutoff,)
        )
        c.commit()
        return cur.rowcount

def create_investigation(name: str, description: str = "") -> int:
    name = name.strip()
    if not name:
        raise ValueError("Investigation name is required.")
    now = now_iso()
    with connect() as c:
        cur = c.execute("INSERT INTO investigations(name,description,created_at,updated_at) VALUES(?,?,?,?)",
                        (name, description.strip(), now, now))
        c.commit()
        return int(cur.lastrowid)

def list_investigations() -> list[dict]:
    with connect() as c:
        rows = c.execute("""
          SELECT i.*,
                 (SELECT COUNT(*) FROM evidence e WHERE e.investigation_id=i.investigation_id) AS evidence_count,
                 (SELECT COUNT(*) FROM investigation_entries n WHERE n.investigation_id=i.investigation_id) AS entry_count,
                 (SELECT COUNT(*) FROM artifacts a JOIN evidence e ON e.evidence_id=a.evidence_id WHERE e.investigation_id=i.investigation_id) AS artifact_count,
                 (SELECT COUNT(*) FROM image_assets im WHERE im.investigation_id=i.investigation_id) AS image_count
          FROM investigations i ORDER BY i.updated_at DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_investigation(investigation_id: int) -> dict | None:
    with connect() as c:
        row = c.execute("""
          SELECT i.*,
                 (SELECT COUNT(*) FROM evidence e WHERE e.investigation_id=i.investigation_id) AS evidence_count,
                 (SELECT COUNT(*) FROM investigation_entries n WHERE n.investigation_id=i.investigation_id) AS entry_count,
                 (SELECT COUNT(*) FROM artifacts a JOIN evidence e ON e.evidence_id=a.evidence_id WHERE e.investigation_id=i.investigation_id) AS artifact_count,
                 (SELECT COUNT(*) FROM image_assets im WHERE im.investigation_id=i.investigation_id) AS image_count
          FROM investigations i WHERE i.investigation_id=?
        """, (investigation_id,)).fetchone()
        return dict(row) if row else None

def update_investigation(investigation_id: int, name: str, description: str = "") -> bool:
    name = name.strip()
    if not name:
        raise ValueError("Investigation name is required.")
    with connect() as c:
        cur = c.execute("UPDATE investigations SET name=?, description=?, updated_at=? WHERE investigation_id=?",
                        (name, description.strip(), now_iso(), investigation_id))
        c.commit()
        return cur.rowcount > 0

def delete_investigation(investigation_id: int) -> bool:
    with connect() as c:
        cur = c.execute("DELETE FROM investigations WHERE investigation_id=?", (investigation_id,))
        c.commit()
        return cur.rowcount > 0

def list_entries(investigation_id: int) -> list[dict]:
    with connect() as c:
        rows = c.execute("SELECT * FROM investigation_entries WHERE investigation_id=? ORDER BY updated_at DESC",
                         (investigation_id,)).fetchall()
        return [dict(r) for r in rows]

def create_entry(investigation_id: int, entry_type: str, title: str, content: str) -> int:
    if entry_type not in {"note", "report", "remark"}:
        raise ValueError("entry_type must be note, report, or remark")
    title = title.strip() or entry_type.title()
    if not content.strip():
        raise ValueError("Entry content is required.")
    now = now_iso()
    with connect() as c:
        exists = c.execute("SELECT 1 FROM investigations WHERE investigation_id=?", (investigation_id,)).fetchone()
        if not exists:
            raise ValueError("Investigation not found.")
        cur = c.execute("""INSERT INTO investigation_entries
                         (investigation_id,entry_type,title,content,created_at,updated_at)
                         VALUES(?,?,?,?,?,?)""",
                        (investigation_id, entry_type, title, content, now, now))
        c.execute("UPDATE investigations SET updated_at=? WHERE investigation_id=?", (now, investigation_id))
        c.commit()
        return int(cur.lastrowid)

def update_entry(entry_id: int, entry_type: str, title: str, content: str) -> bool:
    if entry_type not in {"note", "report", "remark"}:
        raise ValueError("entry_type must be note, report, or remark")
    if not content.strip():
        raise ValueError("Entry content is required.")
    with connect() as c:
        cur = c.execute("""UPDATE investigation_entries
                         SET entry_type=?, title=?, content=?, updated_at=?
                         WHERE entry_id=?""",
                        (entry_type, title.strip() or entry_type.title(), content, now_iso(), entry_id))
        if cur.rowcount:
            row = c.execute("SELECT investigation_id FROM investigation_entries WHERE entry_id=?", (entry_id,)).fetchone()
            if row:
                c.execute("UPDATE investigations SET updated_at=? WHERE investigation_id=?", (now_iso(), row["investigation_id"]))
        c.commit()
        return cur.rowcount > 0

def delete_entry(entry_id: int) -> bool:
    with connect() as c:
        row = c.execute("SELECT investigation_id FROM investigation_entries WHERE entry_id=?", (entry_id,)).fetchone()
        cur = c.execute("DELETE FROM investigation_entries WHERE entry_id=?", (entry_id,))
        if cur.rowcount and row:
            c.execute("UPDATE investigations SET updated_at=? WHERE investigation_id=?", (now_iso(), row["investigation_id"]))
        c.commit()
        return cur.rowcount > 0

def list_images(investigation_id: int) -> list[dict]:
    with connect() as c:
        rows = c.execute("""SELECT image_id, investigation_id, filename, label, platform,
                                  sha256, phash, dhash, width, height, byte_size, created_at
                           FROM image_assets WHERE investigation_id=? ORDER BY created_at DESC""",
                         (investigation_id,)).fetchall()
        return [dict(r) for r in rows]


def compare_image_hashes(hashes: dict, investigation_id: int | None = None, limit: int = 100) -> list[dict]:
    cleanup()
    sql = "SELECT image_id, investigation_id, filename, label, platform, sha256, phash, dhash, width, height, byte_size, created_at FROM image_assets"
    params: list = []
    if investigation_id is not None:
        sql += " WHERE investigation_id=?"
        params.append(investigation_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as c:
        rows = c.execute(sql, params).fetchall()
    matches = []
    for r in rows:
        distance = phash_distance(hashes["phash"], r["phash"])
        exact_file = hashes["sha256"] == r["sha256"]
        category = "exact_file" if exact_file else classify_distance(distance)
        if exact_file or distance <= 10:
            matches.append({**dict(r), "phash_distance": distance, "match_type": category,
                            "note": ("Exact file SHA-256 match." if exact_file else
                                      "Perceptual similarity only; not proof of common ownership or identity.")})
    matches.sort(key=lambda x: (0 if x["match_type"] == "exact_file" else 1, x["phash_distance"], x["created_at"]))
    return matches


def save_image(data: bytes, filename: str, label: str, platform: str, investigation_id: int) -> int:
    with connect() as c:
        if not c.execute("SELECT 1 FROM investigations WHERE investigation_id=?", (investigation_id,)).fetchone():
            raise ValueError("Investigation not found.")
    hashes = hash_image(data)
    safe_name = Path(filename or "image.bin").name
    image_dir = data_dir() / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    stored_path = image_dir / f"{hashes['sha256'][:24]}_{safe_name}"
    if not stored_path.exists():
        stored_path.write_bytes(data)
    now = now_iso()
    with connect() as c:
        cur = c.execute("""INSERT INTO image_assets
          (investigation_id,filename,label,platform,sha256,phash,dhash,width,height,byte_size,stored_path,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
          (investigation_id, safe_name, label.strip(), platform.strip().lower() or "unknown", hashes["sha256"],
           hashes["phash"], hashes["dhash"], hashes["width"], hashes["height"], hashes["bytes"], str(stored_path), now))
        c.execute("UPDATE investigations SET updated_at=? WHERE investigation_id=?", (now, investigation_id))
        c.commit()
        return int(cur.lastrowid)


def delete_image(image_id: int) -> bool:
    with connect() as c:
        row = c.execute("SELECT stored_path, investigation_id FROM image_assets WHERE image_id=?", (image_id,)).fetchone()
        if not row:
            return False
        c.execute("DELETE FROM image_assets WHERE image_id=?", (image_id,))
        c.execute("UPDATE investigations SET updated_at=? WHERE investigation_id=?", (now_iso(), row["investigation_id"]))
        c.commit()
    try:
        Path(row["stored_path"]).unlink(missing_ok=True)
    except OSError:
        pass
    return True


def save_report(report: dict, filename: str, investigation_id: int | None = None) -> int:
    now = now_iso()
    with connect() as c:
        if investigation_id is not None:
            exists = c.execute("SELECT 1 FROM investigations WHERE investigation_id=?", (investigation_id,)).fetchone()
            if not exists:
                raise ValueError("Investigation not found.")
        cur = c.execute("""INSERT INTO evidence
          (investigation_id,sha256,filename,platform,created_at,artifact_count,parser_version)
          VALUES(?,?,?,?,?,?,?)""",
          (investigation_id, report["input_sha256"], filename, report["platform"], now,
           report["artifact_count"], report["parser_version"]))
        eid = cur.lastrowid
        c.executemany("""INSERT INTO artifacts
          (evidence_id,type,value,normalized,platform,confidence,context,location,method,detail)
          VALUES(?,?,?,?,?,?,?,?,?,?)""",
          [(eid, a["type"], a["value"], a["normalized"], a["platform"], a["confidence"],
            a["context"], a["location"], a["method"], a.get("detail", "")) for a in report["artifacts"]])
        if investigation_id is not None:
            c.execute("UPDATE investigations SET updated_at=? WHERE investigation_id=?", (now, investigation_id))
        c.commit()
        return int(eid)

def correlate(report: dict, investigation_id: int | None = None, limit: int = 100) -> list[dict]:
    cleanup()
    matches = []
    with connect() as c:
        for a in report["artifacts"]:
            if investigation_id is None:
                rows = c.execute("""SELECT a.*, e.filename, e.evidence_id, e.created_at, e.investigation_id
                                   FROM artifacts a JOIN evidence e ON e.evidence_id=a.evidence_id
                                   WHERE a.normalized=? ORDER BY e.created_at DESC LIMIT ?""",
                                 (a["normalized"], limit)).fetchall()
            else:
                rows = c.execute("""SELECT a.*, e.filename, e.evidence_id, e.created_at, e.investigation_id
                                   FROM artifacts a JOIN evidence e ON e.evidence_id=a.evidence_id
                                   WHERE a.normalized=? AND e.investigation_id=?
                                   ORDER BY e.created_at DESC LIMIT ?""",
                                 (a["normalized"], investigation_id, limit)).fetchall()
            for r in rows:
                matches.append({
                    "artifact_type": a["type"], "value": a["value"], "confidence": a["confidence"],
                    "matched_artifact_type": r["type"], "matched_value": r["value"],
                    "matched_evidence_id": r["evidence_id"], "matched_filename": r["filename"],
                    "matched_at": r["created_at"], "investigation_id": r["investigation_id"],
                    "note": "Previously observed artifact; this is not proof of common ownership or identity."
                })
    unique, seen = [], set()
    for m in matches:
        k = (m["artifact_type"], m["value"], m["matched_evidence_id"], m["matched_artifact_type"])
        if k not in seen:
            seen.add(k); unique.append(m)
    return unique

def search(query: str, limit: int = 100) -> list[dict]:
    cleanup()
    q = query.strip().casefold()
    with connect() as c:
        rows = c.execute("""SELECT a.*, e.filename, e.evidence_id, e.created_at, e.investigation_id
                           FROM artifacts a JOIN evidence e ON e.evidence_id=a.evidence_id
                           WHERE a.normalized LIKE ? OR lower(a.value) LIKE ?
                           ORDER BY e.created_at DESC LIMIT ?""", (f"%{q}%", f"%{q}%", limit)).fetchall()
        return [dict(r) for r in rows]

def history(limit: int = 100, investigation_id: int | None = None) -> list[dict]:
    """Return saved evidence plus artifacts previously observed in other captures.

    The extra match data lets the investigation UI show which observable
    artifacts were repeated, rather than only showing a raw artifact count.
    """
    cleanup()
    with connect() as c:
        if investigation_id is None:
            rows = c.execute(
                "SELECT * FROM evidence ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM evidence WHERE investigation_id=? "
                "ORDER BY created_at DESC LIMIT ?",
                (investigation_id, limit)
            ).fetchall()

        result = []
        for row in rows:
            item = dict(row)
            matches = c.execute(
                """SELECT DISTINCT
                          a.type AS artifact_type,
                          a.value AS value,
                          a.confidence AS confidence,
                          other.evidence_id AS matched_evidence_id,
                          other.filename AS matched_filename,
                          other.created_at AS matched_at
                   FROM artifacts a
                   JOIN evidence other ON other.evidence_id != a.evidence_id
                   JOIN artifacts previous
                     ON previous.evidence_id = other.evidence_id
                    AND previous.normalized = a.normalized
                   WHERE a.evidence_id = ?
                     AND (? IS NULL OR other.investigation_id = ?)
                   ORDER BY other.created_at DESC
                   LIMIT 100""",
                (row["evidence_id"], investigation_id, investigation_id)
            ).fetchall()
            item["matches"] = [dict(m) for m in matches]
            item["match_count"] = len(item["matches"])
            result.append(item)
        return result

def stats(investigation_id: int | None = None) -> dict:
    cleanup()
    with connect() as c:
        if investigation_id is None:
            e = c.execute("SELECT COUNT(*) n FROM evidence").fetchone()["n"]
            a = c.execute("SELECT COUNT(*) n FROM artifacts").fetchone()["n"]
            im = c.execute("SELECT COUNT(*) n FROM image_assets").fetchone()["n"]
            p = c.execute("SELECT platform, COUNT(*) n FROM evidence GROUP BY platform ORDER BY n DESC").fetchall()
        else:
            e = c.execute("SELECT COUNT(*) n FROM evidence WHERE investigation_id=?", (investigation_id,)).fetchone()["n"]
            a = c.execute("""SELECT COUNT(*) n FROM artifacts a JOIN evidence e ON e.evidence_id=a.evidence_id
                             WHERE e.investigation_id=?""", (investigation_id,)).fetchone()["n"]
            im = c.execute("SELECT COUNT(*) n FROM image_assets WHERE investigation_id=?", (investigation_id,)).fetchone()["n"]
            p = c.execute("SELECT platform, COUNT(*) n FROM evidence WHERE investigation_id=? GROUP BY platform ORDER BY n DESC",
                          (investigation_id,)).fetchall()
    return {"evidence": e, "artifacts": a, "images": im, "platforms": [dict(x) for x in p],
            "retention_days": get_retention_days(), "investigation_id": investigation_id}


def investigation_export(investigation_id: int) -> dict | None:
    """Return a complete point-in-time snapshot for investigation report export."""
    cleanup()
    with connect() as c:
        inv = c.execute("SELECT * FROM investigations WHERE investigation_id=?", (investigation_id,)).fetchone()
        if not inv:
            return None
        evidence_rows = c.execute(
            "SELECT * FROM evidence WHERE investigation_id=? ORDER BY created_at ASC, evidence_id ASC",
            (investigation_id,)
        ).fetchall()
        evidence = []
        for e in evidence_rows:
            item = dict(e)
            artifact_rows = c.execute(
                "SELECT * FROM artifacts WHERE evidence_id=? ORDER BY artifact_id ASC",
                (e["evidence_id"],)
            ).fetchall()
            item["artifacts"] = [dict(a) for a in artifact_rows]
            evidence.append(item)
        entries = [dict(r) for r in c.execute(
            "SELECT * FROM investigation_entries WHERE investigation_id=? ORDER BY created_at ASC, entry_id ASC",
            (investigation_id,)
        ).fetchall()]
        images = [dict(r) for r in c.execute(
            """SELECT image_id, investigation_id, filename, label, platform, sha256, phash, dhash,
                      width, height, byte_size, created_at
               FROM image_assets WHERE investigation_id=?
               ORDER BY created_at ASC, image_id ASC""",
            (investigation_id,)
        ).fetchall()]
    return {
        "investigation": dict(inv),
        "evidence": evidence,
        "entries": entries,
        "images": images,
        "stats": stats(investigation_id),
        "generated_at": now_iso(),
    }
