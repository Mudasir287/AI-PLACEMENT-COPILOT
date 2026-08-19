import sqlite3
import hashlib
from typing import Tuple, Optional, List, Dict, Any

DB_FILE = "placement_copilot.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Computes a secure SHA-256 hash for a given password string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    """Initializes the required SQLite tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Scans History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_role TEXT NOT NULL,
            overall_score REAL NOT NULL,
            cosine_similarity REAL NOT NULL,
            jaccard_similarity REAL NOT NULL,
            matched_skills_count INTEGER NOT NULL,
            missing_skills_count INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """)

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
        );
    """)

    conn.commit()
    conn.close()


def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Registers a new user with hashed credentials."""
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password cannot be empty."

    hashed = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
        return True, "Registration successful! You can now log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please pick another one."
    finally:
        conn.close()


def verify_user(username: str, password: str) -> Tuple[bool, Optional[int]]:
    """Validates login credentials against stored hashes."""
    username = username.strip().lower()
    hashed = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND password_hash = ?",
        (username, hashed)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return True, user["id"]
    return False, None


def save_scan_record(
    user_id: int,
    target_role: str,
    overall_score: float,
    cosine_sim: float,
    jaccard_sim: float,
    matched_count: int,
    missing_count: int
):
    """Logs an ATS scan record into history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scans_history 
        (user_id, target_role, overall_score, cosine_similarity, jaccard_similarity, matched_skills_count, missing_skills_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, target_role, overall_score, cosine_sim, jaccard_sim, matched_count, missing_count))
    conn.commit()
    conn.close()


def get_user_scan_history(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all past scan records for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM scans_history WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# Initialize database on module load
init_db()


# --- Day 10 Verification Pipeline ---
if __name__ == "__main__":
    print("\n🚀 Initializing and Testing SQLite Database...")
    init_db()
    print("✅ Tables 'users', 'scans_history', and 'interview_sessions' verified.")

    test_user = "demo_engineer"
    test_pass = "SecurePass123"

    print(f"\n🔐 Testing user registration for: '{test_user}'")
    success, msg = register_user(test_user, test_pass)
    print(f"Result: {msg}")

    print("\n🔑 Testing login authentication...")
    valid, user_id = verify_user(test_user, test_pass)
    print(f"Auth Success: {valid} (User ID: {user_id})")

    invalid, _ = verify_user(test_user, "WrongPassword")
    print(f"Auth Reject on bad password: {not invalid}")
    print("=" * 55)