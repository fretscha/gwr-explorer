"""Build a small sampled copy of the GWR source DB for fast, hermetic tests.

Samples the first N buildings plus their related entrances/dwellings and ALL code rows.
Run once: `uv run python tests/make_fixture.py /path/to/data_ch.sqlite`
"""
import sqlite3
import sys
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gwr_fixture.sqlite"
N_BUILDINGS = 500


def build(source_path: str) -> None:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if FIXTURE_PATH.exists():
        FIXTURE_PATH.unlink()
    src = sqlite3.connect(source_path)
    dst = sqlite3.connect(FIXTURE_PATH)
    # copy schema
    for (sql,) in src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"):
        dst.execute(sql)
    egids = [r[0] for r in src.execute("SELECT EGID FROM building ORDER BY EGID LIMIT ?", (N_BUILDINGS,))]
    marks = ",".join("?" * len(egids))
    for table in ("building", "entrance", "dwelling"):
        cols = [c[1] for c in src.execute(f"PRAGMA table_info({table})")]
        rows = src.execute(f"SELECT * FROM {table} WHERE EGID IN ({marks})", egids).fetchall()
        placeholders = ",".join("?" * len(cols))
        dst.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    for row in src.execute("SELECT * FROM code"):
        dst.execute("INSERT INTO code VALUES (?,?,?,?,?,?,?,?,?)", row)
    dst.commit()
    dst.close()
    src.close()
    print(f"Wrote {FIXTURE_PATH} with {len(egids)} buildings")


if __name__ == "__main__":
    build(sys.argv[1])
