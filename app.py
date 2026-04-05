"""
SewaPark-AI — Flask Web App
Mobile-first carpark management for Gurdwara events
Run: python3 app.py
"""

import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, g, flash, jsonify

app = Flask(__name__)
app.secret_key = "sewapark-ai-kw26"
DB_PATH = "sewapark.db"

# ===== DB =====
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db: db.close()

# ===== HOME — Gurdwara selector =====
@app.route("/")
def index():
    db = get_db()
    gurdwaras = db.execute("SELECT * FROM gurdwaras WHERE active=1").fetchall()
    return render_template("index.html", gurdwaras=gurdwaras)

# ===== DASHBOARD =====
@app.route("/g/<int:gid>")
def dashboard(gid):
    db = get_db()
    gurdwara = db.execute("SELECT * FROM gurdwaras WHERE id=?", (gid,)).fetchone()
    if not gurdwara: return redirect(url_for("index"))

    lots = db.execute("SELECT * FROM lots WHERE gurdwara_id=? ORDER BY id", (gid,)).fetchall()
    ics = db.execute("SELECT * FROM ics WHERE gurdwara_id=? AND on_duty=1", (gid,)).fetchall()
    waitlist_count = db.execute("SELECT COUNT(*) FROM waitlist WHERE gurdwara_id=? AND status='waiting'", (gid,)).fetchone()[0]
    recent_incidents = db.execute("SELECT * FROM incidents WHERE gurdwara_id=? ORDER BY timestamp DESC LIMIT 5", (gid,)).fetchall()
    ragi_session = db.execute("SELECT * FROM ragi_sessions WHERE gurdwara_id=? AND status='active' ORDER BY triggered_at DESC LIMIT 1", (gid,)).fetchone()

    # Occupancy stats
    statuses = [l["status"] for l in lots]
    occupied = sum(1 for s in statuses if s in ["occupied","violation","reserved_booked"])
    empty = sum(1 for s in statuses if s in ["empty","reserved_empty"])
    total = len(statuses)
    pct = round(occupied/total*100) if total else 0

    # Group lots by zone
    zones = {}
    for lot in lots:
        z = lot["zone"]
        if z not in zones: zones[z] = []
        zones[z].append(lot)

    return render_template("dashboard.html",
        gurdwara=gurdwara, lots=lots, zones=zones,
        occupied=occupied, empty=empty, total=total, pct=pct,
        ics=ics, waitlist_count=waitlist_count,
        recent_incidents=recent_incidents, ragi_session=ragi_session,
        gid=gid
    )

# ===== LOT TOGGLE =====
@app.route("/g/<int:gid>/lot/<int:lot_id>/toggle", methods=["POST"])
def toggle_lot(gid, lot_id):
    db = get_db()
    lot = db.execute("SELECT * FROM lots WHERE id=?", (lot_id,)).fetchone()
    plate = request.form.get("plate","").upper().strip()

    if lot["status"] == "empty":
        db.execute("UPDATE lots SET status='occupied', plate=?, updated_at=datetime('now') WHERE id=?", (plate or None, lot_id))
    elif lot["status"] in ["occupied","violation"]:
        db.execute("UPDATE lots SET status='empty', plate=NULL, updated_at=datetime('now') WHERE id=?", (lot_id,))
    elif lot["status"] == "reserved_empty":
        db.execute("UPDATE lots SET status='reserved_booked', plate=?, updated_at=datetime('now') WHERE id=?", (plate or None, lot_id))
    elif lot["status"] == "reserved_booked":
        db.execute("UPDATE lots SET status='reserved_empty', plate=NULL, updated_at=datetime('now') WHERE id=?", (lot_id,))

    db.commit()
    return redirect(url_for("dashboard", gid=gid))

# ===== GATE =====
@app.route("/g/<int:gid>/gate/<action>", methods=["POST"])
def gate_action(gid, action):
    db = get_db()
    msg = "Gate OPENED" if action == "open" else "Gate CLOSED"
    db.execute("INSERT INTO notifications (gurdwara_id, message, type) VALUES (?,?,?)",
               (gid, f"GATE {action.upper()} — Manual override by IC", "system"))
    db.commit()
    flash(msg, "success" if action == "open" else "danger")
    return redirect(url_for("dashboard", gid=gid))

# ===== INCIDENTS =====
@app.route("/g/<int:gid>/incidents")
def incidents(gid):
    db = get_db()
    gurdwara = db.execute("SELECT * FROM gurdwaras WHERE id=?", (gid,)).fetchone()
    day = request.args.get("day")
    if day:
        rows = db.execute("SELECT i.*, c.name as ic_name FROM incidents i LEFT JOIN ics c ON i.ic_id=c.id WHERE i.gurdwara_id=? AND i.day=? ORDER BY i.timestamp DESC", (gid, day)).fetchall()
    else:
        rows = db.execute("SELECT i.*, c.name as ic_name FROM incidents i LEFT JOIN ics c ON i.ic_id=c.id WHERE i.gurdwara_id=? ORDER BY i.timestamp DESC", (gid,)).fetchall()
    ics = db.execute("SELECT * FROM ics WHERE gurdwara_id=?", (gid,)).fetchall()
    return render_template("incidents.html", gurdwara=gurdwara, incidents=rows, ics=ics, gid=gid, day=day)

@app.route("/g/<int:gid>/incidents/log", methods=["POST"])
def log_incident(gid):
    db = get_db()
    db.execute("""
        INSERT INTO incidents (gurdwara_id, ic_id, plate, type, severity, notes, day, event_name)
        VALUES (?,?,?,?,?,?,?,?)
    """, (gid,
          request.form.get("ic_id") or None,
          request.form.get("plate","").upper() or None,
          request.form["type"],
          request.form.get("severity","medium"),
          request.form["notes"],
          request.form.get("day") or None,
          request.form.get("event_name") or None))
    db.commit()
    flash("Incident logged ✓", "success")
    return redirect(url_for("incidents", gid=gid))

@app.route("/g/<int:gid>/incidents/<int:iid>/resolve", methods=["POST"])
def resolve_incident(gid, iid):
    db = get_db()
    db.execute("UPDATE incidents SET resolved=1, resolved_at=datetime('now'), resolved_notes=? WHERE id=?",
               (request.form.get("resolved_notes"), iid))
    db.commit()
    flash("Incident resolved ✓", "success")
    return redirect(url_for("incidents", gid=gid))

# ===== BOOKINGS =====
@app.route("/g/<int:gid>/bookings")
def bookings(gid):
    db = get_db()
    gurdwara = db.execute("SELECT * FROM gurdwaras WHERE id=?", (gid,)).fetchone()
    rows = db.execute("SELECT b.*, l.label as lot_label FROM bookings b JOIN lots l ON b.lot_id=l.id WHERE b.gurdwara_id=? ORDER BY b.created_at DESC", (gid,)).fetchall()
    reserved_lots = db.execute("SELECT * FROM lots WHERE gurdwara_id=? AND zone='reserved'", (gid,)).fetchall()
    return render_template("bookings.html", gurdwara=gurdwara, bookings=rows, reserved_lots=reserved_lots, gid=gid)

@app.route("/g/<int:gid>/bookings/create", methods=["POST"])
def create_booking(gid):
    db = get_db()
    plate = request.form["plate"].upper().strip()
    lot_id = request.form["lot_id"]
    db.execute("""
        INSERT INTO bookings (gurdwara_id, lot_id, plate, owner_name, type, event_name, jathedar_name, arrival_time)
        VALUES (?,?,?,?,?,?,?,?)
    """, (gid, lot_id, plate,
          request.form["owner_name"], request.form["type"],
          request.form["event_name"],
          request.form.get("jathedar_name") or None,
          request.form.get("arrival_time") or None))
    db.execute("UPDATE lots SET status='reserved_booked', plate=?, updated_at=datetime('now') WHERE id=?", (plate, lot_id))
    db.commit()
    flash(f"Booking confirmed for {plate} ✓", "success")
    return redirect(url_for("bookings", gid=gid))

@app.route("/g/<int:gid>/bookings/<int:bid>/cancel", methods=["POST"])
def cancel_booking(gid, bid):
    db = get_db()
    booking = db.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
    db.execute("UPDATE lots SET status='reserved_empty', plate=NULL WHERE id=?", (booking["lot_id"],))
    db.commit()
    flash("Booking cancelled", "warning")
    return redirect(url_for("bookings", gid=gid))

@app.route("/g/<int:gid>/bookings/<int:bid>/arrive", methods=["POST"])
def booking_arrive(gid, bid):
    db = get_db()
    db.execute("UPDATE bookings SET status='arrived' WHERE id=?", (bid,))
    db.commit()
    flash("Marked as arrived ✓", "success")
    return redirect(url_for("bookings", gid=gid))

# ===== WAITLIST =====
@app.route("/g/<int:gid>/waitlist")
def waitlist(gid):
    db = get_db()
    gurdwara = db.execute("SELECT * FROM gurdwaras WHERE id=?", (gid,)).fetchone()
    rows = db.execute("SELECT * FROM waitlist WHERE gurdwara_id=? AND status='waiting' ORDER BY position ASC", (gid,)).fetchall()
    ics = db.execute("SELECT * FROM ics WHERE gurdwara_id=?", (gid,)).fetchall()
    return render_template("waitlist.html", gurdwara=gurdwara, waitlist=rows, ics=ics, gid=gid)

@app.route("/g/<int:gid>/waitlist/add", methods=["POST"])
def add_waitlist(gid):
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM waitlist WHERE gurdwara_id=? AND status='waiting'", (gid,)).fetchone()[0]
    db.execute("INSERT INTO waitlist (gurdwara_id, plate, driver_name, contact_number, position) VALUES (?,?,?,?,?)",
               (gid, request.form["plate"].upper(), request.form["driver_name"], request.form["contact_number"], count+1))
    db.commit()
    flash(f"Added to waitlist at position #{count+1} ✓", "success")
    return redirect(url_for("waitlist", gid=gid))

@app.route("/g/<int:gid>/waitlist/<int:wid>/admit", methods=["POST"])
def admit_waitlist(gid, wid):
    db = get_db()
    db.execute("UPDATE waitlist SET status='admitted', admitted_at=datetime('now') WHERE id=?", (wid,))
    db.commit()
    flash("Sangat admitted ✓", "success")
    return redirect(url_for("waitlist", gid=gid))

# ===== RAGI ARRIVAL MODE =====
@app.route("/g/<int:gid>/ragi/trigger", methods=["POST"])
def trigger_ragi(gid):
    db = get_db()
    db.execute("UPDATE ragi_sessions SET status='cancelled' WHERE gurdwara_id=? AND status='active'", (gid,))
    plate = request.form.get("vehicle_plate","").upper().strip() or None
    eta = request.form.get("eta_mins", 10)
    ic_id = request.form.get("triggered_by", 1)
    db.execute("INSERT INTO ragi_sessions (gurdwara_id, vehicle_plate, eta_mins, triggered_by, status) VALUES (?,?,?,?,'active')",
               (gid, plate, eta, ic_id))
    db.execute("INSERT INTO notifications (gurdwara_id, message, type) VALUES (?,?,?)",
               (gid, f"☬ RAGI JATHA INBOUND {f'({plate})' if plate else ''} — ETA {eta} MINS. CLEAR DROP-OFF ZONE NOW.", "ragi_inbound"))
    db.commit()
    flash(f"☬ Ragi Arrival Mode ACTIVATED — ETA {eta} mins", "warning")
    return redirect(url_for("dashboard", gid=gid))

@app.route("/g/<int:gid>/ragi/<int:sid>/arrived", methods=["POST"])
def ragi_arrived(gid, sid):
    db = get_db()
    db.execute("UPDATE ragi_sessions SET status='arrived', arrived_at=datetime('now') WHERE id=?", (sid,))
    db.execute("INSERT INTO notifications (gurdwara_id, message, type) VALUES (?,?,?)",
               (gid, "☬ RAGI JATHA ARRIVED — Drop-off zone cleared. Resume normal ops.", "system"))
    db.commit()
    flash("☬ Ragi Jatha arrived — drop-off zone cleared", "success")
    return redirect(url_for("dashboard", gid=gid))

# ===== AAR =====
@app.route("/g/<int:gid>/aar")
def aar(gid):
    db = get_db()
    gurdwara = db.execute("SELECT * FROM gurdwaras WHERE id=?", (gid,)).fetchone()
    day = request.args.get("day")

    if day:
        incidents = db.execute("SELECT i.*, c.name as ic_name FROM incidents i LEFT JOIN ics c ON i.ic_id=c.id WHERE i.gurdwara_id=? AND i.day=? ORDER BY i.timestamp", (gid, day)).fetchall()
    else:
        incidents = db.execute("SELECT i.*, c.name as ic_name FROM incidents i LEFT JOIN ics c ON i.ic_id=c.id WHERE i.gurdwara_id=? ORDER BY i.timestamp", (gid,)).fetchall()

    # Group by type
    grouped = {}
    for inc in incidents:
        t = inc["type"]
        if t not in grouped: grouped[t] = []
        grouped[t].append(inc)

    severity = {s: sum(1 for i in incidents if i["severity"]==s) for s in ["low","medium","high","critical"]}
    days_available = db.execute("SELECT DISTINCT day FROM incidents WHERE gurdwara_id=? AND day IS NOT NULL ORDER BY day", (gid,)).fetchall()

    return render_template("aar.html", gurdwara=gurdwara, incidents=incidents,
                           grouped=grouped, severity=severity,
                           days_available=days_available, selected_day=day, gid=gid)

# ===== ICS =====
@app.route("/g/<int:gid>/ics/<int:ic_id>/dnd", methods=["POST"])
def toggle_dnd(gid, ic_id):
    db = get_db()
    current = db.execute("SELECT dnd FROM ics WHERE id=?", (ic_id,)).fetchone()["dnd"]
    db.execute("UPDATE ics SET dnd=? WHERE id=?", (0 if current else 1, ic_id))
    db.commit()
    return redirect(url_for("dashboard", gid=gid))

# ===== PLATE LOOKUP (AJAX) =====
@app.route("/api/lookup/<plate>")
def api_lookup(plate):
    db = get_db()
    row = db.execute("""
        SELECT b.*, l.label as lot_label FROM bookings b
        JOIN lots l ON b.lot_id=l.id
        WHERE b.plate=? AND b.status='confirmed'
    """, (plate.upper(),)).fetchone()
    return jsonify(dict(row) if row else None)

if __name__ == "__main__":
    print("SewaPark-AI starting → http://localhost:5000")
    app.run(debug=True, port=5000, host="0.0.0.0")
