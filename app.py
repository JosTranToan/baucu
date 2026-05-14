from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db, init_db
from helpers import (
    get_current_term, get_eligible_students,
    get_nomination_results, get_final_vote_results, get_top_candidates
)

app = Flask(__name__)
app.secret_key = "bau-cu-lop-secret-2024"  # Đổi cái này trước khi deploy

# ────────────────────────────────────────────────
# Auth
# ────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form["student_code"].strip()
        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE student_code=? AND is_active=1", (code,)
        ).fetchone()
        conn.close()
        if student:
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            session["is_admin"] = (code == "ADMIN")
            return redirect(url_for("index"))
        flash("Mã học sinh không đúng hoặc không tồn tại.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "student_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Chỉ admin mới vào được trang này.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

# ────────────────────────────────────────────────
# Home
# ────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    term = get_current_term()
    conn = get_db()
    elections = []
    if term:
        elections = conn.execute("""
            SELECT e.*, p.name as position_name, p.top_n
            FROM elections e
            JOIN positions p ON e.position_id = p.id
            WHERE e.term_id = ?
            ORDER BY p.id
        """, (term["id"],)).fetchall()
    conn.close()
    return render_template("index.html", term=term, elections=elections)

# ────────────────────────────────────────────────
# Admin — Students
# ────────────────────────────────────────────────

@app.route("/admin/students")
@login_required
@admin_required
def admin_students():
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return render_template("admin_students.html", students=students)

@app.route("/admin/students/add", methods=["POST"])
@login_required
@admin_required
def admin_add_student():
    name = request.form["name"].strip()
    code = request.form["student_code"].strip()
    if name and code:
        conn = get_db()
        try:
            conn.execute("INSERT INTO students (name, student_code) VALUES (?, ?)", (name, code))
            conn.commit()
            flash(f"Đã thêm học sinh: {name}")
        except Exception as e:
            flash(f"Lỗi: {e}")
        conn.close()
    return redirect(url_for("admin_students"))

@app.route("/admin/students/import", methods=["POST"])
@login_required
@admin_required
def admin_import_students():
    """Import nhiều học sinh cùng lúc, mỗi dòng: MãHS,Tên"""
    raw = request.form["bulk"].strip()
    conn = get_db()
    count = 0
    for line in raw.splitlines():
        parts = line.strip().split(",", 1)
        if len(parts) == 2:
            code, name = parts[0].strip(), parts[1].strip()
            try:
                conn.execute("INSERT OR IGNORE INTO students (name, student_code) VALUES (?, ?)", (name, code))
                count += 1
            except:
                pass
    conn.commit()
    conn.close()
    flash(f"Đã import {count} học sinh.")
    return redirect(url_for("admin_students"))

# ────────────────────────────────────────────────
# Admin — Terms
# ────────────────────────────────────────────────

@app.route("/admin/terms")
@login_required
@admin_required
def admin_terms():
    conn = get_db()
    terms = conn.execute("SELECT * FROM terms ORDER BY year DESC, semester DESC").fetchall()
    conn.close()
    return render_template("admin_terms.html", terms=terms)

@app.route("/admin/terms/add", methods=["POST"])
@login_required
@admin_required
def admin_add_term():
    year = int(request.form["year"])
    semester = int(request.form["semester"])
    conn = get_db()
    try:
        conn.execute("INSERT OR IGNORE INTO terms (year, semester) VALUES (?, ?)", (year, semester))
        conn.commit()
        flash(f"Đã thêm học kỳ {semester} năm {year}.")
    except Exception as e:
        flash(f"Lỗi: {e}")
    conn.close()
    return redirect(url_for("admin_terms"))

@app.route("/admin/terms/set_current/<int:term_id>")
@login_required
@admin_required
def set_current_term(term_id):
    conn = get_db()
    conn.execute("UPDATE terms SET is_current=0")
    conn.execute("UPDATE terms SET is_current=1 WHERE id=?", (term_id,))
    conn.commit()
    conn.close()
    flash("Đã đặt học kỳ hiện tại.")
    return redirect(url_for("admin_terms"))

# ────────────────────────────────────────────────
# Admin — Elections
# ────────────────────────────────────────────────

@app.route("/admin/elections")
@login_required
@admin_required
def admin_elections():
    term = get_current_term()
    conn = get_db()
    positions = conn.execute("SELECT * FROM positions ORDER BY id").fetchall()
    elections = []
    if term:
        elections = conn.execute("""
            SELECT e.*, p.name as position_name
            FROM elections e JOIN positions p ON e.position_id=p.id
            WHERE e.term_id=?
        """, (term["id"],)).fetchall()
    conn.close()
    return render_template("admin_elections.html", term=term, positions=positions, elections=elections)

@app.route("/admin/elections/create/<int:position_id>")
@login_required
@admin_required
def create_election(position_id):
    term = get_current_term()
    if not term:
        flash("Chưa có học kỳ hiện tại.")
        return redirect(url_for("admin_elections"))
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO elections (position_id, term_id, phase) VALUES (?, ?, 1)",
            (position_id, term["id"])
        )
        conn.commit()
        flash("Đã mở bầu cử vòng 1.")
    except Exception as e:
        flash(f"Lỗi: {e}")
    conn.close()
    return redirect(url_for("admin_elections"))

@app.route("/admin/elections/<int:election_id>/next_phase")
@login_required
@admin_required
def next_phase(election_id):
    conn = get_db()
    conn.execute("UPDATE elections SET phase=2 WHERE id=?", (election_id,))
    conn.commit()
    conn.close()
    flash("Đã chuyển sang vòng bầu chính thức.")
    return redirect(url_for("admin_elections"))

@app.route("/admin/elections/<int:election_id>/close")
@login_required
@admin_required
def close_election(election_id):
    """Close election and record winner into position_history"""
    conn = get_db()
    election = conn.execute(
        "SELECT * FROM elections WHERE id=?", (election_id,)
    ).fetchone()
    results = get_final_vote_results(election_id)
    if results:
        winner = results[0]
        try:
            conn.execute(
                "INSERT OR IGNORE INTO position_history (student_id, position_id, term_id) VALUES (?,?,?)",
                (winner["id"], election["position_id"], election["term_id"])
            )
            conn.execute("UPDATE elections SET is_closed=1 WHERE id=?", (election_id,))
            conn.commit()
            flash(f"🎉 {winner['name']} đắc cử!")
        except Exception as e:
            flash(f"Lỗi: {e}")
    else:
        flash("Chưa có phiếu bầu.")
    conn.close()
    return redirect(url_for("admin_elections"))

# ────────────────────────────────────────────────
# Voting — Phase 1 (Đề cử)
# ────────────────────────────────────────────────

@app.route("/vote/<int:election_id>/nominate", methods=["GET", "POST"])
@login_required
def nominate(election_id):
    conn = get_db()
    election = conn.execute(
        "SELECT e.*, p.name as position_name, p.top_n FROM elections e JOIN positions p ON e.position_id=p.id WHERE e.id=?",
        (election_id,)
    ).fetchone()

    if not election or election["phase"] != 1 or election["is_closed"]:
        flash("Vòng đề cử chưa mở hoặc đã đóng.")
        conn.close()
        return redirect(url_for("index"))

    voter_id = session["student_id"]
    already_voted = conn.execute(
        "SELECT 1 FROM nominations WHERE election_id=? AND voter_id=?", (election_id, voter_id)
    ).fetchone()

    eligible = get_eligible_students(election["position_id"])

    if request.method == "POST" and not already_voted:
        nominee_id = int(request.form["nominee_id"])
        # Check nominee is eligible
        eligible_ids = {s["id"] for s in eligible}
        if nominee_id in eligible_ids:
            conn.execute(
                "INSERT INTO nominations (election_id, voter_id, nominee_id) VALUES (?,?,?)",
                (election_id, voter_id, nominee_id)
            )
            conn.commit()
            flash("Đã ghi nhận đề cử của bạn!")
        else:
            flash("Người này không đủ điều kiện.")
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("nominate.html", election=election, eligible=eligible, already_voted=already_voted)

# ────────────────────────────────────────────────
# Voting — Phase 2 (Bầu chính thức)
# ────────────────────────────────────────────────

@app.route("/vote/<int:election_id>/final", methods=["GET", "POST"])
@login_required
def final_vote(election_id):
    conn = get_db()
    election = conn.execute(
        "SELECT e.*, p.name as position_name FROM elections e JOIN positions p ON e.position_id=p.id WHERE e.id=?",
        (election_id,)
    ).fetchone()

    if not election or election["phase"] != 2 or election["is_closed"]:
        flash("Vòng bầu chưa mở hoặc đã đóng.")
        conn.close()
        return redirect(url_for("index"))

    voter_id = session["student_id"]
    already_voted = conn.execute(
        "SELECT 1 FROM final_votes WHERE election_id=? AND voter_id=?", (election_id, voter_id)
    ).fetchone()

    candidates = get_top_candidates(election_id)

    if request.method == "POST" and not already_voted:
        candidate_id = int(request.form["candidate_id"])
        candidate_ids = {c["id"] for c in candidates}
        if candidate_id in candidate_ids:
            conn.execute(
                "INSERT INTO final_votes (election_id, voter_id, candidate_id) VALUES (?,?,?)",
                (election_id, voter_id, candidate_id)
            )
            conn.commit()
            flash("Đã ghi nhận phiếu bầu!")
        else:
            flash("Ứng viên không hợp lệ.")
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("final_vote.html", election=election, candidates=candidates, already_voted=already_voted)

# ────────────────────────────────────────────────
# Results
# ────────────────────────────────────────────────

@app.route("/results/<int:election_id>")
@login_required
def results(election_id):
    conn = get_db()
    election = conn.execute(
        "SELECT e.*, p.name as position_name, p.top_n FROM elections e JOIN positions p ON e.position_id=p.id WHERE e.id=?",
        (election_id,)
    ).fetchone()
    conn.close()

    nom_results = get_nomination_results(election_id)
    final_results = get_final_vote_results(election_id) if election["phase"] == 2 else []
    top_candidates = get_top_candidates(election_id)

    return render_template("results.html",
        election=election,
        nom_results=nom_results,
        final_results=final_results,
        top_candidates=top_candidates
    )

# ────────────────────────────────────────────────
# History
# ────────────────────────────────────────────────

@app.route("/history")
@login_required
def history():
    conn = get_db()
    records = conn.execute("""
        SELECT s.name, s.student_code, p.name as position_name, t.year, t.semester
        FROM position_history ph
        JOIN students s ON ph.student_id=s.id
        JOIN positions p ON ph.position_id=p.id
        JOIN terms t ON ph.term_id=t.id
        ORDER BY t.year DESC, t.semester DESC, p.id
    """).fetchall()
    conn.close()
    return render_template("history.html", records=records)

# ────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
