"""
database.py
SQLite database layer with aligned schema columns and auto-migration.
"""

import sqlite3
import hashlib
from typing import List, Dict, Any, Optional, Tuple

DB_NAME = "placement_copilot.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Scans History Table (Standardized Column Names)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_role TEXT NOT NULL,
            overall_score REAL NOT NULL,
            cosine_similarity REAL DEFAULT 0.0,
            jaccard_similarity REAL DEFAULT 0.0,
            matched_skills_count INTEGER DEFAULT 0,
            missing_skills_count INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Auto-migration check
    cursor.execute("PRAGMA table_info(scans_history)")
    cols = {row["name"] for row in cursor.fetchall()}
    if "cosine_similarity" not in cols and "cosine_sim" in cols:
        cursor.execute("ALTER TABLE scans_history RENAME COLUMN cosine_sim TO cosine_similarity")
    if "jaccard_similarity" not in cols and "jaccard_sim" in cols:
        cursor.execute("ALTER TABLE scans_history RENAME COLUMN jaccard_sim TO jaccard_similarity")
    if "matched_skills_count" not in cols and "matched_count" in cols:
        cursor.execute("ALTER TABLE scans_history RENAME COLUMN matched_count TO matched_skills_count")
    if "missing_skills_count" not in cols and "missing_count" in cols:
        cursor.execute("ALTER TABLE scans_history RENAME COLUMN missing_count TO missing_skills_count")

    # 3. Interview Sessions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_role TEXT NOT NULL,
            average_score REAL NOT NULL,
            questions_count INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # 4. Roadmap Task Progress Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roadmap_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, skill_name),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


def register_user(username: str, password: str) -> Tuple[bool, str]:
    if not username.strip() or not password.strip():
        return False, "Username and password cannot be empty."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.strip(), hash_password(password))
        )
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def verify_user(username: str, password: str) -> Tuple[bool, Optional[int]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username.strip(),)
    )
    user = cursor.fetchone()
    conn.close()

    if user and user["password_hash"] == hash_password(password):
        return True, user["id"]
    return False, None


def save_scan_record(user_id: int, target_role: str, overall_score: float,
                     cosine_sim: float, jaccard_sim: float, matched_count: int, missing_count: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scans_history (
            user_id, target_role, overall_score,
            cosine_similarity, jaccard_similarity,
            matched_skills_count, missing_skills_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, target_role, overall_score, cosine_sim, jaccard_sim, matched_count, missing_count))
    conn.commit()
    conn.close()


def get_user_scan_history(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_role, overall_score, cosine_similarity AS cosine_sim,
               jaccard_similarity AS jaccard_sim, matched_skills_count AS matched_count,
               missing_skills_count AS missing_count, timestamp
        FROM scans_history
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_interview_history(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_role, average_score, questions_count, timestamp
        FROM interview_sessions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def set_roadmap_task_status(user_id: int, skill_name: str, is_completed: bool):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_roadmap_progress (user_id, skill_name, is_completed, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, skill_name) DO UPDATE SET
            is_completed = excluded.is_completed,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, skill_name, 1 if is_completed else 0))
    conn.commit()
    conn.close()


def get_user_completed_roadmap_skills(user_id: int) -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT skill_name FROM user_roadmap_progress
        WHERE user_id = ? AND is_completed = 1
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row["skill_name"] for row in rows]


init_database()