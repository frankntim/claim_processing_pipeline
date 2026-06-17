"""
db.py — SQLite policy database for Claims Adjudication System
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "claims_policy.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS policy_clauses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_type TEXT NOT NULL,
            clause_name TEXT NOT NULL,
            coverage TEXT NOT NULL,
            exclusions TEXT NOT NULL,
            coverage_limit TEXT NOT NULL,
            auto_approve_limit REAL NOT NULL,
            requires_preauth INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS claims_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_ref TEXT,
            claimant_name TEXT,
            claim_type TEXT,
            estimated_amount REAL,
            policy_number TEXT,
            decision TEXT,
            decision_reason TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed policy data if empty
    c.execute("SELECT COUNT(*) FROM policy_clauses")
    if c.fetchone()[0] == 0:
        policies = [
            (
                "collision",
                "Section 4.2 — Third-Party Collision Coverage",
                "Covers repair or replacement of the insured vehicle when damaged by a third party, "
                "provided a Garda/police report or third-party statement is filed within 14 days of the incident.",
                "Excludes single-vehicle incidents, DUI-related events, racing, and damage to aftermarket modifications.",
                "Up to market value of vehicle at time of incident",
                50000.0, 0
            ),
            (
                "water damage",
                "Section 7.1 — Escape of Water",
                "Covers sudden and accidental escape of water from fixed domestic plumbing, "
                "including resultant structural and contents damage.",
                "Excludes gradual leaks, flooding from external waterways, storm surge, and damage to the pipe itself.",
                "Up to EUR 100,000 per event, subject to EUR 500 excess",
                50000.0, 0
            ),
            (
                "medical procedure",
                "Section 2.4 — Inpatient Surgical Benefits",
                "Covers pre-authorised surgical procedures including surgeon fees, anaesthesia, "
                "and inpatient accommodation up to a semi-private room rate.",
                "Excludes cosmetic procedures, experimental treatments, and procedures outside the policy provider network.",
                "Up to EUR 15,000 per procedure; pre-authorisation required",
                15000.0, 1
            ),
            (
                "fire damage",
                "Section 5.1 — Fire and Smoke Damage",
                "Covers damage to the insured property and its contents caused by fire, smoke, or explosion, "
                "including firefighting-related water damage.",
                "Excludes arson, damage caused by the insured's deliberate act, and unoccupied properties over 60 days.",
                "Up to full rebuild cost as declared on policy schedule",
                75000.0, 0
            ),
            (
                "theft",
                "Section 6.3 — Theft and Attempted Theft",
                "Covers loss or damage resulting from theft, attempted theft, or malicious damage, "
                "provided a police report is filed within 48 hours.",
                "Excludes theft by family members, items left in an unattended vehicle overnight, and cash over EUR 500.",
                "Up to EUR 25,000 for contents; vehicles at market value",
                25000.0, 0
            ),
            (
                "liability",
                "Section 8.1 — Public Liability",
                "Covers legal liability to third parties for bodily injury or property damage "
                "occurring in connection with the insured premises or business activities.",
                "Excludes employer liability, contractual liability, and intentional acts.",
                "Up to EUR 2,000,000 per occurrence",
                100000.0, 0
            ),
        ]
        c.executemany(
            "INSERT INTO policy_clauses "
            "(claim_type, clause_name, coverage, exclusions, coverage_limit, auto_approve_limit, requires_preauth) "
            "VALUES (?,?,?,?,?,?,?)",
            policies
        )

    conn.commit()
    conn.close()


def lookup_policy(claim_type: str) -> dict:
    conn = get_conn()
    c = conn.cursor()
    # Try exact or partial match
    c.execute(
        "SELECT * FROM policy_clauses WHERE LOWER(claim_type) = LOWER(?)", (claim_type,)
    )
    row = c.fetchone()
    if not row:
        c.execute(
            "SELECT * FROM policy_clauses WHERE LOWER(?) LIKE '%' || LOWER(claim_type) || '%'",
            (claim_type,)
        )
        row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "claim_type": claim_type,
        "clause_name": "Section 1.1 — General Claims Coverage",
        "coverage": "Covers losses arising from sudden, unforeseen, and accidental events within the policy period.",
        "exclusions": "Excludes intentional acts, pre-existing conditions, and wear and tear.",
        "coverage_limit": "Subject to policy schedule limits and applicable excess",
        "auto_approve_limit": 10000.0,
        "requires_preauth": 0,
    }


def log_claim(claim_ref, claimant_name, claim_type, estimated_amount,
              policy_number, decision, decision_reason):
    conn = get_conn()
    conn.execute(
        "INSERT INTO claims_log "
        "(claim_ref, claimant_name, claim_type, estimated_amount, policy_number, decision, decision_reason) "
        "VALUES (?,?,?,?,?,?,?)",
        (claim_ref, claimant_name, claim_type, estimated_amount,
         policy_number, decision, decision_reason)
    )
    conn.commit()
    conn.close()


def get_claims_log():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM claims_log ORDER BY processed_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_policies():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM policy_clauses ORDER BY claim_type").fetchall()
    conn.close()
    return [dict(r) for r in rows]
