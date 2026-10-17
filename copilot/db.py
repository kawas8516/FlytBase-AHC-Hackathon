import sqlite3
from contextlib import contextmanager

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS areas(area_id TEXT PRIMARY KEY, name TEXT, team_id TEXT, lat REAL, lon REAL);
CREATE TABLE IF NOT EXISTS teams(team_id TEXT PRIMARY KEY, name TEXT, lead_user_id TEXT);
CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY, name TEXT, role TEXT, team_id TEXT);
CREATE TABLE IF NOT EXISTS wells(
  asset_id TEXT PRIMARY KEY, name TEXT, well_type TEXT, area_id TEXT, team_id TEXT,
  in_charge_user_id TEXT, lat REAL, lon REAL, installed_on TEXT, recorded_status TEXT,
  last_inspection_id TEXT, equipment_json TEXT);
CREATE TABLE IF NOT EXISTS inspections(
  inspection_id TEXT PRIMARY KEY, asset_id TEXT, inspected_at TEXT, inspector_user_id TEXT, method TEXT,
  ambient_temp_c REAL, wellhead_temp_c REAL, spill_detected INTEGER, spill_area_pct REAL,
  spill_est_volume_bbl REAL, notes TEXT, evidence_json TEXT);
CREATE INDEX IF NOT EXISTS ix_ins_asset ON inspections(asset_id, inspected_at);
CREATE TABLE IF NOT EXISTS maintenance(
  maintenance_id TEXT PRIMARY KEY, asset_id TEXT, started_at TEXT, completed_at TEXT, maintenance_type TEXT,
  equipment_kind TEXT, issue TEXT, action_taken TEXT, technician_user_id TEXT, contractor TEXT,
  downtime_hours REAL, cost_labor REAL, cost_parts REAL, cost_total REAL,
  triggered_by_inspection_id TEXT, report_file TEXT);
CREATE INDEX IF NOT EXISTS ix_mnt_asset ON maintenance(asset_id, started_at);
CREATE TABLE IF NOT EXISTS reg_events(
  event_id TEXT PRIMARY KEY, asset_id TEXT, date TEXT, agency TEXT, event_type TEXT, protocol_id TEXT,
  related_inspection_id TEXT, hours_to_report REAL, detail TEXT, fine_usd REAL, status TEXT);
CREATE TABLE IF NOT EXISTS notes(
  note_id TEXT PRIMARY KEY, asset_id TEXT, created_at TEXT, author_user_id TEXT, note_type TEXT,
  inspection_id TEXT, text TEXT, valid_from TEXT, valid_to TEXT);
CREATE TABLE IF NOT EXISTS docs(doc_id TEXT PRIMARY KEY, kind TEXT, path TEXT, title TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS reports(
  maintenance_id TEXT PRIMARY KEY, asset_id TEXT, path TEXT, text TEXT, extracted_json TEXT);
CREATE TABLE IF NOT EXISTS rules(
  scope TEXT, key TEXT, value REAL, unit TEXT, doc_id TEXT, section TEXT, quote TEXT, via TEXT,
  PRIMARY KEY(scope, key));
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(ref, kind, asset_id, title, text);
"""


def connect(path=None) -> sqlite3.Connection:
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    return con


@contextmanager
def session(path=None):
    con = connect(path)
    try:
        yield con
        con.commit()
    finally:
        con.close()
