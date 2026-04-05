"""
GurdwarAI — SQLite Database Setup
Run this once: python3 db_init.py
Creates gurdwarai.db with all tables + seeds the 3 Gurdwaras
"""

import sqlite3
from datetime import datetime

DB_PATH = "gurdwarai.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Foreign keys on
    c.execute("PRAGMA foreign_keys = ON")

    # ===== GURDWARAS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS gurdwaras (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            short_name  TEXT NOT NULL,
            address     TEXT,
            total_lots  INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ===== LOTS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS lots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id  INTEGER NOT NULL REFERENCES gurdwaras(id),
            label        TEXT NOT NULL,
            zone         TEXT NOT NULL CHECK(zone IN ('lhs','center','rhs','reserved','slope','bus')),
            status       TEXT NOT NULL DEFAULT 'empty'
                         CHECK(status IN ('empty','occupied','violation','reserved_empty','reserved_booked')),
            plate        TEXT,
            updated_at   TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_lots_gurdwara ON lots(gurdwara_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_lots_zone ON lots(gurdwara_id, zone)")

    # ===== ICS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS ics (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id  INTEGER NOT NULL REFERENCES gurdwaras(id),
            name         TEXT NOT NULL,
            initials     TEXT NOT NULL,
            role         TEXT NOT NULL,
            area         TEXT NOT NULL,
            phone        TEXT,
            dnd          INTEGER DEFAULT 0,
            on_duty      INTEGER DEFAULT 1,
            created_at   TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_ics_gurdwara ON ics(gurdwara_id)")

    # ===== BOOKINGS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id    INTEGER NOT NULL REFERENCES gurdwaras(id),
            lot_id         INTEGER NOT NULL REFERENCES lots(id),
            plate          TEXT NOT NULL,
            owner_name     TEXT NOT NULL,
            type           TEXT NOT NULL CHECK(type IN ('ragi','sewadar','jathedar','vip')),
            event_name     TEXT NOT NULL,
            jathedar_name  TEXT,
            arrival_time   TEXT,
            status         TEXT NOT NULL DEFAULT 'confirmed'
                           CHECK(status IN ('confirmed','arrived','cancelled','no_show')),
            created_at     TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_gurdwara ON bookings(gurdwara_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_plate ON bookings(plate)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(gurdwara_id, status)")

    # ===== WAITLIST =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id    INTEGER NOT NULL REFERENCES gurdwaras(id),
            plate          TEXT NOT NULL,
            driver_name    TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            position       INTEGER NOT NULL,
            status         TEXT NOT NULL DEFAULT 'waiting'
                           CHECK(status IN ('waiting','admitted','left')),
            added_at       TEXT DEFAULT (datetime('now')),
            admitted_at    TEXT,
            admitted_by    INTEGER REFERENCES ics(id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_gurdwara ON waitlist(gurdwara_id, status)")

    # ===== INCIDENTS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id     INTEGER NOT NULL REFERENCES gurdwaras(id),
            ic_id           INTEGER REFERENCES ics(id),
            plate           TEXT,
            type            TEXT NOT NULL CHECK(type IN (
                                'stack_parking','dropoff_violation','reserved_lot_blocked',
                                'rowdy_sangat','manpower_shortage','ragi_lot_issue',
                                'jb_bus_issue','flyer_comms_failure','gate_issue',
                                'elderly_assist','other'
                            )),
            severity        TEXT NOT NULL DEFAULT 'medium'
                            CHECK(severity IN ('low','medium','high','critical')),
            notes           TEXT NOT NULL,
            resolved        INTEGER DEFAULT 0,
            resolved_at     TEXT,
            resolved_notes  TEXT,
            day             INTEGER,
            event_name      TEXT,
            timestamp       TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_gurdwara ON incidents(gurdwara_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_day ON incidents(gurdwara_id, day)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(gurdwara_id, type)")

    # ===== NOTIFICATIONS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id  INTEGER NOT NULL REFERENCES gurdwaras(id),
            ic_id        INTEGER REFERENCES ics(id),
            message      TEXT NOT NULL,
            type         TEXT NOT NULL CHECK(type IN (
                             'alert','ragi_inbound','carpark_full',
                             'manpower','elderly_assist','waitlist','system'
                         )),
            sent_at      TEXT DEFAULT (datetime('now')),
            read_at      TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_notif_gurdwara ON notifications(gurdwara_id)")

    # ===== EVENTS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id        INTEGER NOT NULL REFERENCES gurdwaras(id),
            name               TEXT NOT NULL,
            date               TEXT NOT NULL,
            day                INTEGER,
            ragi_jatha_name    TEXT,
            ragi_arrival_time  TEXT,
            notes              TEXT,
            active             INTEGER DEFAULT 1,
            created_at         TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_gurdwara ON events(gurdwara_id)")

    # ===== RAGI SESSIONS =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS ragi_sessions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            gurdwara_id    INTEGER NOT NULL REFERENCES gurdwaras(id),
            event_id       INTEGER REFERENCES events(id),
            vehicle_plate  TEXT,
            eta_mins       INTEGER NOT NULL,
            triggered_by   INTEGER NOT NULL REFERENCES ics(id),
            triggered_at   TEXT DEFAULT (datetime('now')),
            arrived_at     TEXT,
            status         TEXT NOT NULL DEFAULT 'active'
                           CHECK(status IN ('active','arrived','cancelled'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_ragi_gurdwara ON ragi_sessions(gurdwara_id, status)")

    conn.commit()
    print("✓ All tables created")
    seed(conn)
    conn.close()
    print(f"\n✓ Database ready: {DB_PATH}")


def seed(conn):
    c = conn.cursor()

    # Check if already seeded
    c.execute("SELECT COUNT(*) FROM gurdwaras")
    if c.fetchone()[0] > 0:
        print("⚠ Already seeded — skipping")
        return

    # ===== 1. CENTRAL SIKH TEMPLE =====
    c.execute("""
        INSERT INTO gurdwaras (name, short_name, address, total_lots)
        VALUES (?, ?, ?, ?)
    """, ("Central Sikh Temple", "CST", "2 Towner Road, Singapore 327804", 30))
    cst_id = c.lastrowid

    cst_lots = (
        [("L"+str(i), "lhs") for i in range(1,9)] +
        [("C"+str(i), "center") for i in range(1,9)] +
        [("R"+str(i), "rhs") for i in range(1,9)] +
        [("RAGI-1","reserved"),("RAGI-2","reserved"),
         ("RES-1","reserved"),("RES-2","reserved"),("RES-3","reserved"),
         ("SLOPE-1","slope"),("SLOPE-2","slope"),
         ("JB-BUS","bus")]
    )
    for label, zone in cst_lots:
        status = "reserved_empty" if zone == "reserved" else "empty"
        c.execute(
            "INSERT INTO lots (gurdwara_id, label, zone, status) VALUES (?,?,?,?)",
            (cst_id, label, zone, status)
        )

    cst_ics = [
        ("Jagpreet Singh",  "JS", "Carpark IC",         "FULL CARPARK + SHABEEL"),
        ("Grishwin Singh",  "GS", "Carpark Assistant",  "RHS ZONE + ENTRANCE"),
        ("Manpreet Kaur",   "MK", "Shabeel IC",         "SHABEEL STATION"),
        ("Harjeet Singh",   "HS", "Ragi Coordinator",   "RAGI RESERVED LOTS"),
    ]
    for name, initials, role, area in cst_ics:
        c.execute(
            "INSERT INTO ics (gurdwara_id, name, initials, role, area) VALUES (?,?,?,?,?)",
            (cst_id, name, initials, role, area)
        )

    print("✓ Central Sikh Temple seeded")

    # ===== 2. SILAT ROAD GURDWARA =====
    c.execute("""
        INSERT INTO gurdwaras (name, short_name, address, total_lots)
        VALUES (?, ?, ?, ?)
    """, ("Silat Road Gurdwara", "SRG", "Silat Road, Singapore", 10))
    srg_id = c.lastrowid

    srg_lots = (
        [("S"+str(i), "lhs") for i in range(1,5)] +
        [("S"+str(i), "rhs") for i in range(5,8)] +
        [("RAGI-1","reserved"),("RES-1","reserved"),("JB-BUS","bus")]
    )
    for label, zone in srg_lots:
        status = "reserved_empty" if zone == "reserved" else "empty"
        c.execute(
            "INSERT INTO lots (gurdwara_id, label, zone, status) VALUES (?,?,?,?)",
            (srg_id, label, zone, status)
        )
    c.execute(
        "INSERT INTO ics (gurdwara_id, name, initials, role, area) VALUES (?,?,?,?,?)",
        (srg_id, "Silat IC", "SI", "Carpark IC", "FULL CARPARK")
    )
    print("✓ Silat Road Gurdwara seeded")

    # ===== 3. DHARMAK SABHA GURDWARA =====
    c.execute("""
        INSERT INTO gurdwaras (name, short_name, address, total_lots)
        VALUES (?, ?, ?, ?)
    """, ("Dharmak Sabha Gurdwara", "DSG", "Dharmak Sabha, Singapore", 20))
    dsg_id = c.lastrowid

    dsg_lots = (
        [("D"+str(i), "lhs")    for i in range(1,7)] +
        [("D"+str(i), "rhs")    for i in range(7,11)] +
        [("D"+str(i), "center") for i in range(11,15)] +
        [("RAGI-1","reserved"),("RAGI-2","reserved"),
         ("RES-1","reserved"),("SLOPE-1","slope"),("JB-BUS","bus")]
    )
    for label, zone in dsg_lots:
        status = "reserved_empty" if zone == "reserved" else "empty"
        c.execute(
            "INSERT INTO lots (gurdwara_id, label, zone, status) VALUES (?,?,?,?)",
            (dsg_id, label, zone, status)
        )
    c.execute(
        "INSERT INTO ics (gurdwara_id, name, initials, role, area) VALUES (?,?,?,?,?)",
        (dsg_id, "Dharmak IC", "DI", "Carpark IC", "FULL CARPARK")
    )
    print("✓ Dharmak Sabha Gurdwara seeded")

    conn.commit()


if __name__ == "__main__":
    init_db()
