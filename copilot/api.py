"""FastAPI server: chat, users, conversations, ledger, raw records. Serves the built web UI from web/dist."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from .agent import Copilot
from .config import ROOT, TODAY

app = FastAPI(title="Wellspring Asset Copilot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
bot = Copilot()


class Ask(BaseModel):
    user_id: str
    conv_id: int
    question: str


class NewConv(BaseModel):
    user_id: str
    session_date: str | None = None


@app.get("/api/meta")
def meta():
    with db.session() as con:
        users = [dict(r) for r in con.execute("SELECT u.*, t.name team FROM users u LEFT JOIN teams t USING(team_id) ORDER BY u.name")]
        areas = [dict(r) for r in con.execute("SELECT * FROM areas ORDER BY name")]
        n = con.execute("SELECT count(*) FROM wells").fetchone()[0]
        rules = [dict(r) for r in con.execute("SELECT scope, key, value, unit, doc_id, section, via FROM rules WHERE value IS NOT NULL ORDER BY scope, key")]
    return {"users": users, "areas": areas, "wells": n, "today": TODAY.isoformat(), "rules": rules}


@app.post("/api/conversations")
def new_conv(body: NewConv):
    sd = date.fromisoformat(body.session_date) if body.session_date else TODAY
    return {"conv_id": bot.ledger.new_conversation(body.user_id, sd), "session_date": sd.isoformat()}


@app.get("/api/conversations")
def list_conv(user_id: str):
    out = []
    for c in bot.ledger.conversations(user_id):
        msgs = bot.ledger.messages(c["id"], user_id)
        out.append({**c, "first": next((m["content"] for m in msgs if m["role"] == "user"), ""), "count": len(msgs)})
    return out


@app.get("/api/conversations/{conv_id}")
def get_conv(conv_id: int, user_id: str):
    msgs = bot.ledger.messages(conv_id, user_id)
    return [{"role": m["role"], "content": m["content"], "payload": json.loads(m["payload"]) if m["payload"] else None} for m in msgs]


@app.post("/api/ask")
def ask(body: Ask):
    c = bot.ledger.conversation(body.conv_id)
    if not c or c["user_id"] != body.user_id:
        raise HTTPException(403, "conversation belongs to another user")
    return bot.ask(body.user_id, body.conv_id, body.question)


@app.get("/api/ledger")
def ledger():
    d = bot.ledger.data()
    return [{**f, "author": d.name(f["author_id"])} for f in reversed(bot.ledger.facts()) if f["kind"] != "preference"]


@app.get("/api/memory")
def memory(user_id: str):
    """This user's own earlier result sets (private memory). Filtered by user_id in SQL."""
    rows = bot.ledger.con.execute(
        "SELECT id, session_date, question, op, entity_ids FROM result_sets WHERE user_id=? ORDER BY session_date DESC, id DESC LIMIT 40",
        (user_id,)).fetchall()
    return [{**dict(r), "entity_ids": json.loads(r["entity_ids"])} for r in rows]


@app.post("/api/reset")
def reset():
    bot.ledger.reset()
    return {"ok": True}


@app.get("/api/attention")
def attention():
    from .attention import feed
    return feed(bot.ledger.ops())


@app.get("/api/record/{rid}")
def record(rid: str):
    tables = [("inspections", "inspection_id"), ("maintenance", "maintenance_id"), ("reg_events", "event_id"), ("notes", "note_id")]
    with db.session() as con:
        for t, k in tables:
            r = con.execute(f"SELECT * FROM {t} WHERE {k}=?", (rid,)).fetchone()
            if r:
                out = {"type": t, "record": dict(r)}
                if t == "maintenance":
                    rep = con.execute("SELECT text FROM reports WHERE maintenance_id=?", (rid,)).fetchone()
                    if rep:
                        out["report"] = rep[0]
                return out
        doc = rid.split(" ")[0].split("#")[0]
        r = con.execute("SELECT * FROM docs WHERE doc_id=?", (doc,)).fetchone()
        if r:
            return {"type": "doc", "record": {"doc_id": r["doc_id"], "title": r["title"]}, "report": r["text"]}
    for f in bot.ledger.facts():
        if f["id"] == rid:
            return {"type": "ledger", "record": f}
    raise HTTPException(404, rid)


dist = ROOT / "web" / "dist"
if dist.exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        return FileResponse(dist / "index.html")
