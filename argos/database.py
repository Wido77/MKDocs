from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS investigations (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
 authorization_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (authorization_confirmed IN (0,1)),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS targets (
 id INTEGER PRIMARY KEY, investigation_id INTEGER NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
 value TEXT NOT NULL, normalized_url TEXT, registered_domain TEXT,
 authorization_scope TEXT NOT NULL DEFAULT 'public-passive', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
 id INTEGER PRIMARY KEY, target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
 collector_name TEXT NOT NULL, collector_version TEXT NOT NULL, configuration_json TEXT NOT NULL DEFAULT '{}',
 status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed')), started_at TEXT, finished_at TEXT, error_message TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
 id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 relative_path TEXT NOT NULL, sha256 TEXT NOT NULL, mime_type TEXT, byte_size INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
 id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL, category TEXT NOT NULL, evidence_key TEXT NOT NULL,
 value_json TEXT NOT NULL, source_reference TEXT NOT NULL,
 classification TEXT NOT NULL CHECK(classification IN ('evidence','inference','hypothesis')),
 confidence TEXT NOT NULL CHECK(confidence IN ('low','medium','high')), notes TEXT NOT NULL DEFAULT '', observed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
 id INTEGER PRIMARY KEY, investigation_id INTEGER NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
 url TEXT NOT NULL, label TEXT NOT NULL, accessed_at TEXT NOT NULL, notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS findings (
 id INTEGER PRIMARY KEY, investigation_id INTEGER NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
 statement TEXT NOT NULL, classification TEXT NOT NULL CHECK(classification IN ('evidence','inference','hypothesis')),
 confidence TEXT NOT NULL CHECK(confidence IN ('low','medium','high')),
 review_status TEXT NOT NULL DEFAULT 'draft' CHECK(review_status IN ('draft','reviewed','rejected')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        connection = self.connect()
        try:
            connection.executescript(SCHEMA)
        finally:
            connection.close()

    def create_investigation(self, title: str, summary: str, target: str, authorized: bool) -> dict[str, object]:
        title, target = title.strip(), target.strip()
        if not title:
            raise ValueError("El título es obligatorio.")
        if not target:
            raise ValueError("El objetivo es obligatorio.")
        if not authorized:
            raise ValueError("Debes confirmar el alcance autorizado antes de continuar.")
        now = utc_now()
        connection = self.connect()
        try:
            investigation = connection.execute(
                "INSERT INTO investigations (title, summary, authorization_confirmed, created_at, updated_at) VALUES (?, ?, 1, ?, ?)",
                (title, summary.strip(), now, now),
            )
            target_row = connection.execute(
                "INSERT INTO targets (investigation_id, value, created_at) VALUES (?, ?, ?)",
                (investigation.lastrowid, target, now),
            )
            connection.commit()
        finally:
            connection.close()
        return {"id": investigation.lastrowid, "title": title, "target": {"id": target_row.lastrowid, "value": target}, "created_at": now}

    def list_investigations(self) -> list[dict[str, object]]:
        query = """SELECT i.id, i.title, i.summary, i.created_at, GROUP_CONCAT(t.value, ' | ') targets
                   FROM investigations i LEFT JOIN targets t ON t.investigation_id=i.id
                   GROUP BY i.id ORDER BY i.created_at DESC"""
        connection = self.connect()
        try:
            rows = connection.execute(query).fetchall()
        finally:
            connection.close()
        return [{"id": row["id"], "title": row["title"], "summary": row["summary"], "targets": row["targets"] or "", "created_at": row["created_at"]} for row in rows]

    def get_target(self, target_id: int) -> dict[str, object] | None:
        connection = self.connect()
        try:
            row = connection.execute("SELECT t.*, i.authorization_confirmed FROM targets t JOIN investigations i ON i.id=t.investigation_id WHERE t.id=?", (target_id,)).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def begin_run(self, target_id: int, collector: str, version: str) -> int:
        connection = self.connect()
        try:
            row = connection.execute("INSERT INTO runs (target_id,collector_name,collector_version,status,started_at) VALUES (?,?,?,?,?)", (target_id, collector, version, "running", utc_now()))
            connection.commit()
            return row.lastrowid
        finally:
            connection.close()

    def finish_run(self, run_id: int, status: str, error: str | None = None) -> None:
        connection = self.connect()
        try:
            connection.execute("UPDATE runs SET status=?,finished_at=?,error_message=? WHERE id=?", (status, utc_now(), error, run_id))
            connection.commit()
        finally:
            connection.close()

    def add_artifact(self, run_id: int, path: str, sha256: str, mime: str, size: int) -> int:
        connection = self.connect()
        try:
            row = connection.execute("INSERT INTO artifacts (run_id,relative_path,sha256,mime_type,byte_size,created_at) VALUES (?,?,?,?,?,?)", (run_id, path, sha256, mime, size, utc_now()))
            connection.commit()
            return row.lastrowid
        finally:
            connection.close()

    def add_evidence(self, run_id: int, artifact_id: int, category: str, key: str, value: object, source: str, observed: str) -> int:
        connection = self.connect()
        try:
            row = connection.execute("INSERT INTO evidence (run_id,artifact_id,category,evidence_key,value_json,source_reference,classification,confidence,observed_at) VALUES (?,?,?,?,?,?, 'evidence','high',?)", (run_id, artifact_id, category, key, json.dumps(value, ensure_ascii=False), source, observed))
            connection.commit()
            return row.lastrowid
        finally:
            connection.close()

    def investigation_detail(self, investigation_id: int, run_id: int | None = None) -> dict[str, object] | None:
        connection = self.connect()
        try:
            investigation = connection.execute("SELECT * FROM investigations WHERE id=?", (investigation_id,)).fetchone()
            if not investigation:
                return None
            targets = connection.execute("SELECT * FROM targets WHERE investigation_id=? ORDER BY id", (investigation_id,)).fetchall()
            runs = connection.execute("SELECT r.*, t.value target FROM runs r JOIN targets t ON t.id=r.target_id WHERE t.investigation_id=? ORDER BY r.id DESC", (investigation_id,)).fetchall()
            selected_run = run_id or (runs[0]["id"] if runs else None)
            evidence = connection.execute("SELECT e.*, a.relative_path FROM evidence e LEFT JOIN artifacts a ON a.id=e.artifact_id JOIN runs r ON r.id=e.run_id JOIN targets t ON t.id=r.target_id WHERE t.investigation_id=? AND e.run_id=? ORDER BY CASE e.category WHEN 'dns' THEN 1 WHEN 'http' THEN 2 WHEN 'tls' THEN 3 ELSE 9 END, e.id", (investigation_id, selected_run)).fetchall() if selected_run else []
            return {"investigation": dict(investigation), "targets": [dict(row) for row in targets], "runs": [dict(row) for row in runs], "selected_run": selected_run, "evidence": [dict(row) for row in evidence]}
        finally:
            connection.close()
