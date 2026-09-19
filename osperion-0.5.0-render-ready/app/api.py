from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import APP_NAME, VERSION, get_retention_days, set_retention_days
from .service import analyze_text, persist, analyze_image, persist_image
from .db import (
    history, search, stats, cleanup, create_investigation, list_investigations,
    get_investigation, update_investigation, delete_investigation,
    list_entries, create_entry, update_entry, delete_entry, list_images, delete_image
)

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title=APP_NAME, version=VERSION)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"ok": True, "name": APP_NAME, "version": VERSION}

@app.post("/api/analyze")
async def api_analyze(file: UploadFile | None = File(None), text: str | None = Form(None),
                      platform: str = Form("auto"), investigation_id: int | None = Form(None)):
    if file is not None:
        raw = await file.read()
        content = raw.decode("utf-8", errors="replace")
        filename = file.filename or "upload"
    elif text:
        content = text
        filename = "pasted-inspect-code"
    else:
        raise HTTPException(400, "Provide inspect/source code as text or a file.")
    if len(content) > 25_000_000:
        raise HTTPException(413, "Input is larger than the 25 MB safety limit.")
    try:
        return analyze_text(content, filename, platform, investigation_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/save")
def api_save(payload: dict):
    report = payload.get("report")
    filename = payload.get("filename", "saved-evidence")
    investigation_id = payload.get("investigation_id", report.get("investigation_id") if isinstance(report, dict) else None)
    if not isinstance(report, dict) or "input_sha256" not in report:
        raise HTTPException(400, "Invalid report.")
    try:
        eid = persist(report, filename, int(investigation_id) if investigation_id is not None else None)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"saved": True, "evidence_id": eid, "investigation_id": investigation_id}

@app.post("/api/images/analyze")
async def api_analyze_image(file: UploadFile = File(...), investigation_id: int | None = Form(None)):
    raw = await file.read()
    if len(raw) > 15_000_000:
        raise HTTPException(413, "Image is larger than the 15 MB safety limit.")
    try:
        return analyze_image(raw, investigation_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/images/save")
async def api_save_image(file: UploadFile = File(...), investigation_id: int = Form(...),
                         label: str = Form(""), platform: str = Form("unknown")):
    raw = await file.read()
    if len(raw) > 15_000_000:
        raise HTTPException(413, "Image is larger than the 15 MB safety limit.")
    try:
        image_id = persist_image(raw, file.filename or "image", label, platform, investigation_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"saved": True, "image_id": image_id, "investigation_id": investigation_id}


@app.get("/api/investigations/{investigation_id}/images")
def api_images(investigation_id: int):
    if not get_investigation(investigation_id):
        raise HTTPException(404, "Investigation not found.")
    return {"items": list_images(investigation_id)}


@app.delete("/api/images/{image_id}")
def api_delete_image(image_id: int):
    if not delete_image(image_id):
        raise HTTPException(404, "Image asset not found.")
    return {"deleted": True}


@app.get("/api/investigations")
def api_investigations():
    return {"items": list_investigations()}

@app.post("/api/investigations")
def api_create_investigation(payload: dict):
    try:
        iid = create_investigation(str(payload.get("name", "")), str(payload.get("description", "")))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return get_investigation(iid)

@app.get("/api/investigations/{investigation_id}")
def api_get_investigation(investigation_id: int):
    item = get_investigation(investigation_id)
    if not item:
        raise HTTPException(404, "Investigation not found.")
    return {"investigation": item, "entries": list_entries(investigation_id),
            "evidence": history(200, investigation_id), "images": list_images(investigation_id), "stats": stats(investigation_id)}

@app.put("/api/investigations/{investigation_id}")
def api_update_investigation(investigation_id: int, payload: dict):
    try:
        ok = update_investigation(investigation_id, str(payload.get("name", "")), str(payload.get("description", "")))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok: raise HTTPException(404, "Investigation not found.")
    return get_investigation(investigation_id)

@app.delete("/api/investigations/{investigation_id}")
def api_delete_investigation(investigation_id: int):
    if not delete_investigation(investigation_id):
        raise HTTPException(404, "Investigation not found.")
    return {"deleted": True}

@app.post("/api/investigations/{investigation_id}/entries")
def api_create_entry(investigation_id: int, payload: dict):
    try:
        eid = create_entry(investigation_id, str(payload.get("entry_type", "note")),
                           str(payload.get("title", "")), str(payload.get("content", "")))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"entry": next(x for x in list_entries(investigation_id) if x["entry_id"] == eid)}

@app.put("/api/entries/{entry_id}")
def api_update_entry(entry_id: int, payload: dict):
    try:
        ok = update_entry(entry_id, str(payload.get("entry_type", "note")),
                          str(payload.get("title", "")), str(payload.get("content", "")))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok: raise HTTPException(404, "Entry not found.")
    return {"updated": True}

@app.delete("/api/entries/{entry_id}")
def api_delete_entry(entry_id: int):
    if not delete_entry(entry_id):
        raise HTTPException(404, "Entry not found.")
    return {"deleted": True}

@app.get("/api/history")
def api_history(limit: int = 100, investigation_id: int | None = None):
    return {"items": history(max(1, min(limit, 500)), investigation_id), "retention_days": get_retention_days()}

@app.get("/api/search")
def api_search(q: str, limit: int = 100):
    return {"query": q, "items": search(q, max(1, min(limit, 500)))}

@app.get("/api/stats")
def api_stats(investigation_id: int | None = None):
    return stats(investigation_id)

@app.post("/api/settings/retention")
def api_retention(payload: dict):
    try: days = set_retention_days(int(payload["days"]))
    except Exception: raise HTTPException(400, "days must be an integer")
    cleanup()
    return {"retention_days": days}
