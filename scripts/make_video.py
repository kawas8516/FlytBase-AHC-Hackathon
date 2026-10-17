"""Builds the demo video: narration (edge-tts) + scripted browser run (Playwright) + merge (ffmpeg).
Usage: python scripts/make_video.py [--voice en-US-AndrewNeural] [--out docs/demo]
Needs the app running on http://localhost:8000 and pip install playwright edge-tts imageio-ffmpeg; playwright install chromium.
To use YOUR voice instead: record one WAV per scene named docs/demo/audio/<scene>.wav (scene ids printed below) and pass --own-voice."""
import argparse
import asyncio
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://localhost:8000"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SLIDE_CSS = """<style>body{margin:0;font-family:Bahnschrift,'Segoe UI',sans-serif;background:#f7f6f3;color:#1c1917;display:flex;flex-direction:column;justify-content:center;height:100vh;padding:0 90px;box-sizing:border-box}
h1{font-size:52px;margin:0 0 10px;letter-spacing:-0.02em}h2{font-size:34px;margin:0 0 22px}p,li{font-size:25px;line-height:1.5;color:#44403c}.sub{color:#78716c;font-size:22px}
.row{display:flex;gap:18px;align-items:stretch;margin:18px 0}.box{background:#fff;border:1px solid #e7e5e4;border-radius:12px;padding:16px 20px;flex:1;font-size:21px}
.box b{display:block;font-size:22px;margin-bottom:6px;color:#c2410c}.arrow{align-self:center;font-size:34px;color:#a8a29e}.tag{display:inline-block;background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:2px 10px;font-size:20px;margin:4px 6px 0 0}</style>"""

SLIDES = {
    "title": SLIDE_CSS + "<h1>Wellspring</h1><h2>Asset Intelligence Copilot</h2><p>Answers operators' questions about 600 wells, with the evidence, and remembers what people tell it.</p><p class='sub'>FlytBase Hacktoberfest 2026</p>",
    "idea": SLIDE_CSS + "<h2>One idea: a ledger, not a pile of prompts</h2><ul><li>Records and documents are <b>read-only</b></li><li>Everything people tell the copilot goes in a <b>ledger</b>: author, reason, scope, original kept</li><li>Every answer = data + documents + ledger</li><li>Rules are <b>parsed from the manuals and SOPs</b>, never hard-coded</li></ul>",
    "arch": SLIDE_CSS + "<h2>How it fits together</h2><div class='row'><div class='box'><b>Data</b>wells, inspections, repairs, reports, notes, regulator events</div><div class='arrow'>→</div><div class='box'><b>Ingest</b>SQLite + search index; report-only facts extracted</div><div class='arrow'>→</div><div class='box'><b>Rules</b>thresholds and deadlines parsed from manuals, SOPs, MOC memos, recall notice, regulator letter</div></div><div class='row'><div class='box'><b>Operators</b>deterministic: downtime, spills, gas-response, bypass/MOC, recalled pumps, status precedence</div><div class='arrow'>+</div><div class='box'><b>Ledger</b>corrections, rules, statements, hearsay; private memory and preferences per user</div><div class='arrow'>→</div><div class='box'><b>Answer</b>table, chart, map, heatmap + evidence IDs + proof<br><span class='sub'>Gemma only for odd phrasing</span></div></div>",
    "close": SLIDE_CSS + "<h2>What makes the answers trustworthy</h2><ul><li>Rules come from the documents, including revisions by date (SR-01: 24 h, then 12 h)</li><li>New well type T500 worked with no code change</li><li>It says when the data cannot answer (no pressure, no production volumes)</li><li>Every answer cites the records it used</li></ul><p class='sub'>Next: streaming, embeddings for free-form SOP questions, role-based permissions.</p>",
}

Q = {
    "q1": "All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data.",
    "q3": "Since 1 Nov 2026, every time an operator note reports gas at a well, did we get someone out to that well in time under our operating procedures? List every report and whether the response met the deadline.",
    "q4": "Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all.",
    "q8a": "WELL-0333's recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on.",
    "q8b": "Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list.",
    "q8c": "Which recalled pumps are still in the ground right now?",
    "q10": "When a well stays shut in longer than the repair itself, what are we usually waiting on: parts, crews, contractors or weather? Break it down by area for jobs started in 2026, with the typical number of extra days, and tell me if any area stands out.",
}

# scene id, narration, action name
SCENES = [
    ("s01_title", "This is Wellspring, a copilot that answers operators' plain-English questions about their wells, with the evidence, and remembers what people tell it. The test set has six hundred wells, seven areas, and new documents.", "slide:title"),
    ("s02_idea", "The core idea is a ledger, not a pile of prompts. Records and documents stay read-only. Everything people tell the copilot, a correction, a rule, a status, goes into a ledger with who said it, why, at what scope, and the original value is kept. Every answer is built from data, documents and the ledger.", "slide:idea"),
    ("s03_arch", "Data is loaded into a database and a search index. Rules are parsed out of the manuals, SOPs, memos, the recall notice and the regulator letter. Deterministic operators do the maths and return rows, evidence and proof. The language model, Gemma, is only used for unusual phrasing, and none of the final answers needed it.", "slide:arch"),
    ("s04_rules", "Here are the rules the copilot read from the documents. T200 needs fifteen degrees above air, T350 twenty. The new T500 well type from the test data, twenty-five, was picked up automatically with no code change. Even the S R zero one deadline follows the SOP revision: twenty-four hours before January first, twelve hours after.", "rules"),
    ("s05_q1", "First, an honest answer. Asked to map reservoir pressure, it says the data has no pressure readings. Pressure appears only as equipment limits in the manuals, so a map would be invented. It does not make one up.", "ask:q1:Michael Turner"),
    ("s06_q3", "Gas reports. Under the operations SOP, every gas or H2S note needs a field response, a repair job or a manual inspection, within twenty-four hours before January first and twelve hours after. Twenty-six reports, nine missed. Each row shows the note, the response record and the hours.", "ask:q3:Laura Simmons"),
    ("s07_q4", "Temporary bypasses. The copilot reads the management of change memos. Well zero-four-zero-five has no approval. Well zero-two-four-nine is past its expiry. Well zero-two-four-eight is allowed because memo forty-four extended memo thirty-one. And every row cites its notes and memo.", "ask:q4:Chris Dalton"),
    ("s08_q8a", "Now memory. Nathan Pierce, a supervisor, reports that the recalled pump on well three-three-three was swapped. The copilot records it as his first-hand report, with the work order missing, and applies it for everyone.", "ask:q8a:Nathan Pierce"),
    ("s09_q8b", "Olivia Grant says Nathan told her another pump was swapped. That is second-hand, so it is stored as unconfirmed and the pump stays on the recall list until someone confirms.", "ask:q8b:Olivia Grant"),
    ("s10_q8c", "Robert Hayes asks which recalled pumps are still in the ground. Eight wells. Well three-three-three is off the list, with Nathan named as the source. The other pump is still listed.", "ask:q8c:Robert Hayes"),
    ("s11_ledger", "The ledger shows what is shared with everyone: who said it, the status, and the original. Private preferences and each person's own conversations are kept apart, so one person's history never leaks to another.", "ledger"),
    ("s12_q10", "Last, a judgement question. When a well stays shut in longer than the repair, what are we waiting on? Weather accounts for sixty-three percent and parts for thirty-seven. Contractors and crews never appear in the notes, so it says so, and flags the areas that stand out.", "ask:q10:Michael Turner"),
    ("s13_close", "In short: rules read from the documents, deterministic operators, a ledger with provenance, and honest answers when the data cannot say. Thank you.", "slide:close"),
]


def dur(path: Path) -> float:
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


async def tts(outdir: Path, voice: str):
    import edge_tts
    for sid, text, _ in SCENES:
        p = outdir / f"{sid}.mp3"
        if not p.exists():
            await edge_tts.Communicate(text, voice, rate="+4%").save(str(p))


async def run_browser(outdir: Path, users: dict, durations: dict):
    from playwright.async_api import async_playwright
    starts = {}
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True)
        ctx = await br.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(outdir / "raw"),
                                   record_video_size={"width": 1280, "height": 720})
        page = await ctx.new_page()
        await page.request.post(f"{BASE}/api/reset")
        await page.goto(BASE)
        await page.wait_for_timeout(1500)
        t0 = time.time()
        in_app = False

        async def ensure_app():
            nonlocal in_app
            if not in_app:
                await page.goto(BASE)
                await page.wait_for_selector("header select")
                in_app = True

        async def pick_user(name):
            await page.select_option("header select", value=users[name])
            await page.wait_for_timeout(500)

        async def close_drawer():
            if await page.locator(".drawer").count():
                await page.click(".drawer button:has-text('Close')")
                await page.wait_for_timeout(300)

        async def ask(key, name):
            await close_drawer()
            await pick_user(name)
            await page.click("button:has-text('New chat')")
            before = await page.locator(".answer").count()
            await page.fill(".composer input", Q[key])
            await page.keyboard.press("Enter")
            await page.wait_for_function("n => document.querySelectorAll('.answer').length > n && !document.querySelector('.thinking')", arg=before, timeout=120000)
            await page.wait_for_timeout(800)
            await page.evaluate("document.querySelector('.chat').scrollTo({top: 0, behavior: 'smooth'})")

        for sid, text, action in SCENES:
            starts[sid] = time.time() - t0
            kind, *rest = action.split(":")
            if kind == "slide":
                in_app = False
                await page.set_content(SLIDES[rest[0]])
            elif kind == "rules":
                await ensure_app()
                await close_drawer()
                await page.click("button:has-text('Rules')")
            elif kind == "ledger":
                await ensure_app()
                await close_drawer()
                await page.click("button:has-text('Ledger')")
            elif kind == "ask":
                await ensure_app()
                await ask(rest[0], rest[1])
            while time.time() - t0 - starts[sid] < durations[sid] + 0.8:
                await page.wait_for_timeout(200)
        await ctx.close()
        video = await page.video.path()
        await br.close()
    return Path(video), starts


def merge(outdir: Path, video: Path, starts: dict, final: Path, own: bool):
    ext = "wav" if own else "mp3"
    cmd = [FFMPEG, "-y", "-i", str(video)]
    for sid, _, _ in SCENES:
        cmd += ["-i", str(outdir / ("audio" if own else "") / f"{sid}.{ext}")]
    parts, labels = [], []
    for i, (sid, _, _) in enumerate(SCENES, 1):
        ms = int(starts[sid] * 1000)
        parts.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    fc = ";".join(parts) + f";{''.join(labels)}amix=inputs={len(SCENES)}:normalize=0[aout]"
    cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(final)]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en-US-AndrewNeural")
    ap.add_argument("--out", default="docs/demo")
    ap.add_argument("--own-voice", action="store_true")
    a = ap.parse_args()
    outdir = ROOT / a.out
    (outdir / "raw").mkdir(parents=True, exist_ok=True)
    meta = httpx.get(f"{BASE}/api/meta", timeout=60).json()
    users = {u["name"]: u["user_id"] for u in meta["users"]}
    missing = {"Michael Turner", "Laura Simmons", "Chris Dalton", "Nathan Pierce", "Olivia Grant", "Robert Hayes"} - set(users)
    if missing:
        sys.exit(f"missing users: {missing}")
    if a.own_voice:
        ext, folder = "wav", outdir / "audio"
        durations = {sid: dur(folder / f"{sid}.wav") for sid, _, _ in SCENES}
    else:
        asyncio.run(tts(outdir, a.voice))
        durations = {sid: dur(outdir / f"{sid}.mp3") for sid, _, _ in SCENES}
    print("narration seconds:", round(sum(durations.values()), 1))
    video, starts = asyncio.run(run_browser(outdir, users, durations))
    final = outdir / "wellspring_demo.mp4"
    merge(outdir, video, starts, final, a.own_voice)
    print("wrote", final, "| length ~", round(max(starts[s] + durations[s] for s in starts) + 1, 1), "s")


if __name__ == "__main__":
    main()
