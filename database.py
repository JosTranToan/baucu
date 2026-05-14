import sqlite3
import os

DB_PATH = "election.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_code TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            top_n INTEGER NOT NULL DEFAULT 3  -- 5 for lớp trưởng/phó, 3 for the rest
        );

        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL CHECK(semester IN (1,2)),
            is_current INTEGER DEFAULT 0,
            UNIQUE(year, semester)
        );

        CREATE TABLE IF NOT EXISTS position_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            position_id INTEGER NOT NULL REFERENCES positions(id),
            term_id INTEGER NOT NULL REFERENCES terms(id),
            UNIQUE(position_id, term_id)
        );

        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id INTEGER NOT NULL REFERENCES positions(id),
            term_id INTEGER NOT NULL REFERENCES terms(id),
            phase INTEGER NOT NULL DEFAULT 1 CHECK(phase IN (1,2)),
            is_closed INTEGER DEFAULT 0,
            UNIQUE(position_id, term_id)
        );

        CREATE TABLE IF NOT EXISTS nominations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL REFERENCES elections(id),
            voter_id INTEGER NOT NULL REFERENCES students(id),
            nominee_id INTEGER NOT NULL REFERENCES students(id),
            UNIQUE(election_id, voter_id)
        );

        CREATE TABLE IF NOT EXISTS final_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL REFERENCES elections(id),
            voter_id INTEGER NOT NULL REFERENCES students(id),
            candidate_id INTEGER NOT NULL REFERENCES students(id),
            UNIQUE(election_id, voter_id)
        );
    """)

    # Seed positions
    positions = [
        ("Lớp trưởng", 5),
        ("Lớp phó", 5),
        ("Ban học tập", 3),
        ("Ban văn nghệ", 3),
        ("Ban thể thao", 3),
        ("Ban kỷ luật", 3),
        ("Ban đối ngoại", 3),
        ("Ban tài chính", 3),
        ("Ban truyền thông", 3),
        ("Ban từ thiện", 3),
        ("Ban sự kiện", 3),
        ("Ban trang trí", 3),
        ("Ban hậu cần", 3),
        ("Ban y tế", 3),
        ("Ban môi trường", 3),
        ("Ban thư ký", 3),
        ("Ban lịch sử - địa lý", 3),
        ("Ban công nghệ", 3),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO positions (name, top_n) VALUES (?, ?)", positions
    )

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
