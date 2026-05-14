from database import get_db

def get_current_term():
    conn = get_db()
    term = conn.execute("SELECT * FROM terms WHERE is_current=1").fetchone()
    conn.close()
    return term

def get_eligible_students(position_id):
    """
    Returns students who CAN be nominated for a given position in the current term.
    Excluded if:
    - Currently holding any position this term
    - Has held this specific position before
    - Held any position in the directly adjacent semester
    """
    term = get_current_term()
    if not term:
        return []

    year, semester = term["year"], term["semester"]

    # Adjacent term: if current is HK1, adjacent is HK2 of previous year; if HK2, adjacent is HK1 of same year
    if semester == 1:
        adj_year, adj_sem = year - 1, 2
    else:
        adj_year, adj_sem = year, 1

    conn = get_db()

    excluded = conn.execute("""
        SELECT DISTINCT ph.student_id FROM position_history ph
        JOIN terms t ON ph.term_id = t.id
        WHERE
            -- Currently holding any position this term
            (t.year = ? AND t.semester = ?)
            OR
            -- Already held THIS position before (any term)
            (ph.position_id = ?)
            OR
            -- Held any position in the adjacent semester
            (t.year = ? AND t.semester = ?)
    """, (year, semester, position_id, adj_year, adj_sem)).fetchall()

    excluded_ids = {r["student_id"] for r in excluded}

    all_students = conn.execute(
        "SELECT * FROM students WHERE is_active=1"
    ).fetchall()

    conn.close()

    return [s for s in all_students if s["id"] not in excluded_ids]

def get_nomination_results(election_id):
    conn = get_db()
    results = conn.execute("""
        SELECT s.id, s.name, s.student_code, COUNT(n.id) as vote_count
        FROM nominations n
        JOIN students s ON n.nominee_id = s.id
        WHERE n.election_id = ?
        GROUP BY n.nominee_id
        ORDER BY vote_count DESC
    """, (election_id,)).fetchall()
    conn.close()
    return results

def get_final_vote_results(election_id):
    conn = get_db()
    results = conn.execute("""
        SELECT s.id, s.name, s.student_code, COUNT(fv.id) as vote_count
        FROM final_votes fv
        JOIN students s ON fv.candidate_id = s.id
        WHERE fv.election_id = ?
        GROUP BY fv.candidate_id
        ORDER BY vote_count DESC
    """, (election_id,)).fetchall()
    conn.close()
    return results

def get_top_candidates(election_id):
    """Get top N candidates from phase 1 nominations"""
    conn = get_db()
    election = conn.execute(
        "SELECT e.*, p.top_n FROM elections e JOIN positions p ON e.position_id=p.id WHERE e.id=?",
        (election_id,)
    ).fetchone()
    conn.close()
    if not election:
        return []
    results = get_nomination_results(election_id)
    return results[:election["top_n"]]
