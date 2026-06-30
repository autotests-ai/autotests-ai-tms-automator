import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCaseState:
    project_id: int
    test_case_id: int
    status_id: int
    last_modified: int
    processing: str


class StateStore:
    def __init__(self, database_path: str) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS test_case_state (
                project_id INTEGER NOT NULL,
                test_case_id INTEGER NOT NULL,
                status_id INTEGER NOT NULL,
                last_modified INTEGER NOT NULL,
                processing TEXT NOT NULL DEFAULT 'idle',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, test_case_id)
            );

            CREATE TABLE IF NOT EXISTS status_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                test_case_id INTEGER NOT NULL,
                test_case_name TEXT,
                from_status_id INTEGER,
                to_status_id INTEGER NOT NULL,
                detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                handled INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS automation_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                test_case_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT
            );

            CREATE TABLE IF NOT EXISTS project_repositories (
                project_id INTEGER PRIMARY KEY,
                project_name TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                repo_url TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._conn.commit()

    def get_state(self, project_id: int, test_case_id: int) -> TestCaseState | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT project_id, test_case_id, status_id, last_modified, processing
                FROM test_case_state
                WHERE project_id = ? AND test_case_id = ?
                """,
                (project_id, test_case_id),
            ).fetchone()
        if row is None:
            return None
        return TestCaseState(**dict(row))

    def upsert_state(
        self,
        project_id: int,
        test_case_id: int,
        status_id: int,
        last_modified: int,
        processing: str | None = None,
    ) -> None:
        current = self.get_state(project_id, test_case_id)
        proc = processing if processing is not None else (current.processing if current else "idle")
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO test_case_state (
                    project_id, test_case_id, status_id, last_modified, processing, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, test_case_id) DO UPDATE SET
                    status_id = excluded.status_id,
                    last_modified = excluded.last_modified,
                    processing = excluded.processing,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (project_id, test_case_id, status_id, last_modified, proc),
            )
            self._conn.commit()

    def set_processing(self, project_id: int, test_case_id: int, processing: str) -> None:
        with self._lock:
            self._conn.execute(
                """
                UPDATE test_case_state
                SET processing = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ? AND test_case_id = ?
                """,
                (processing, project_id, test_case_id),
            )
            self._conn.commit()

    def record_transition(
        self,
        project_id: int,
        test_case_id: int,
        test_case_name: str,
        from_status_id: int | None,
        to_status_id: int,
    ) -> int:
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO status_transitions (
                    project_id, test_case_id, test_case_name, from_status_id, to_status_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, test_case_id, test_case_name, from_status_id, to_status_id),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def create_job(self, project_id: int, test_case_id: int) -> int:
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO automation_jobs (project_id, test_case_id, status)
                VALUES (?, ?, 'pending')
                """,
                (project_id, test_case_id),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def finish_job(self, job_id: int, status: str, error: str | None = None) -> None:
        with self._lock:
            self._conn.execute(
                """
                UPDATE automation_jobs
                SET status = ?, error = ?, finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, error, job_id),
            )
            self._conn.commit()

    def has_open_job(self, project_id: int, test_case_id: int) -> bool:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT 1
                FROM automation_jobs
                WHERE project_id = ? AND test_case_id = ? AND status = 'pending'
                LIMIT 1
                """,
                (project_id, test_case_id),
            ).fetchone()
        return row is not None

    def get_last_job(self, project_id: int, test_case_id: int) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(
                """
                SELECT id, status, error
                FROM automation_jobs
                WHERE project_id = ? AND test_case_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_id, test_case_id),
            ).fetchone()

    def should_queue_automation(
        self,
        project_id: int,
        test_case_id: int,
        processing: str,
    ) -> bool:
        if processing in ("running", "done", "failed"):
            return False
        if self.has_open_job(project_id, test_case_id):
            return False
        last = self.get_last_job(project_id, test_case_id)
        if last is None:
            return True
        if last["status"] == "pending":
            return False
        if last["status"] == "completed" and processing == "done":
            return False
        return False

    def fetch_pending_jobs(self, limit: int = 10) -> list[sqlite3.Row]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, project_id, test_case_id
                FROM automation_jobs
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return list(rows)

    def mark_transition_handled(self, transition_id: int) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE status_transitions SET handled = 1 WHERE id = ?",
                (transition_id,),
            )
            self._conn.commit()

    def get_project_repo(self, project_id: int) -> dict[str, object] | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT project_id, project_name, repo_name, repo_url
                FROM project_repositories
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def save_project_repo(
        self,
        project_id: int,
        project_name: str,
        repo_name: str,
        repo_url: str,
    ) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO project_repositories (project_id, project_name, repo_name, repo_url)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    project_name = excluded.project_name,
                    repo_name = excluded.repo_name,
                    repo_url = excluded.repo_url
                """,
                (project_id, project_name, repo_name, repo_url),
            )
            self._conn.commit()
