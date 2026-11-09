import sqlite3
from datetime import date
from pathlib import Path
from schemas import JobPost

DB_PATH = Path(__file__).parent / "data" / "jobs.db"  # data/ is gitignored

DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # create data/ if it doesn't exist

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute(
    "PRAGMA foreign_keys = ON"
)  # SQLite only enforces REFERENCES when this is on

# IF NOT EXISTS: safe to run every time; only creates the tables the first time
conn.executescript("""
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY,
    source          TEXT NOT NULL UNIQUE,
    company         TEXT NOT NULL,
    role            TEXT NOT NULL,
    location        TEXT,
    work_mode       TEXT,
    seniority       TEXT,
    salary_min      INTEGER,
    salary_max      INTEGER,
    salary_currency TEXT,
    salary_period   TEXT,
    saved_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill  TEXT NOT NULL,
    kind   TEXT NOT NULL CHECK (kind IN ('required', 'nice_to_have'))
);
""")


def job_exists(source: str) -> bool:
    """True if a post from this source (URL or file) is already saved."""
    row = conn.execute("SELECT 1 FROM jobs WHERE source = ?", (source,)).fetchone()
    return row is not None


def save_job(job: JobPost, source: str):
    """Save a job and its skills; returns the new job id."""
    data = job.model_dump()  # JobPost -> dict
    required = data.pop(
        "skills_required"
    )  # lists go to the skills table, not the jobs table
    nice_to_have = data.pop("skills_nice_to_have")

    with (
        conn
    ):  # one transaction: the job and its skills are saved together, or not at all
        cursor = conn.execute(
            """INSERT INTO jobs (source, company, role, location, work_mode, seniority,
                                 salary_min, salary_max, salary_currency, salary_period, saved_at)
               VALUES (:source, :company, :role, :location, :work_mode, :seniority,
                       :salary_min, :salary_max, :salary_currency, :salary_period, :saved_at)""",
            {**data, "source": source, "saved_at": date.today().isoformat()},
        )
        job_id = cursor.lastrowid  # the id SQLite gave the new row
        conn.executemany(
            "INSERT INTO skills (job_id, skill, kind) VALUES (?, ?, ?)",
            [(job_id, skill, "required") for skill in required]
            + [(job_id, skill, "nice_to_have") for skill in nice_to_have],
        )
    return job_id


def list_jobs():
    """All saved jobs, one tuple per row."""
    return conn.execute(
        "SELECT id, company, role, work_mode, salary_min, salary_max, salary_currency, salary_period FROM jobs"
    ).fetchall()


def list_saved_jobs() -> str:
    """List the job posts the user has saved in their job database, with each post's required skills.
    Use this for questions about the user's saved or tracked jobs."""
    rows = conn.execute(
        """SELECT j.id, j.company, j.role, j.location, j.work_mode,
                  j.salary_min, j.salary_max, j.salary_currency, j.salary_period, j.source,
                  GROUP_CONCAT(s.skill, ', ')
           FROM jobs j LEFT JOIN skills s ON s.job_id = j.id AND s.kind = 'required'
           GROUP BY j.id"""
    ).fetchall()
    lines = []
    for id_, company, role, location, mode, smin, smax, cur, period, source, skills in rows:
        salary = f"{smin}-{smax} {cur}/{period}" if smin else "not given"
        lines.append(f"{id_}. {company} - {role} | {location} | {mode} | salary: {salary} | "
                     f"required: {skills or '-'} | source: {source}")
    return "\n".join(lines) or "No jobs saved yet."