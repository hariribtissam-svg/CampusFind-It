import sqlite3
import hashlib
import hmac
import secrets

from database.connection import get_connection
def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL
        )
    """)
def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return salt.hex() + "$" + password_hash.hex()

def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split("$")

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False

def add_user(full_name, email, password):
    full_name = full_name.strip()
    email = email.strip()

    if not full_name or not email or not password:
        raise ValueError("Tous les champs sont obligatoires.")

    password_hash = hash_password(password)

    try:
        with get_connection() as connection:
            cursor = connection.execute("""
                INSERT INTO users (full_name, email, password_hash)
                VALUES (?, ?, ?)
            """, (full_name, email, password_hash))

            return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed: users.email" in str(error):
            raise ValueError("Cet email est déjà utilisé.") from error
        raise

def get_user_by_email(email):
    with get_connection() as connection:
        return connection.execute("""
            SELECT id, full_name, email, password_hash
            FROM users
            WHERE email = ?
        """, (email.strip(),)).fetchone()



def get_user_by_full_name(full_name):
    with get_connection() as connection:
        return connection.execute("""
            SELECT id, full_name, email
            FROM users
            WHERE full_name = ?
            COLLATE NOCASE
            ORDER BY id DESC
        """, (full_name.strip(),)).fetchall()

def search_users(search_text):
    pattern = "%" + search_text.strip() + "%"

    with get_connection() as connection:
        return connection.execute("""
            SELECT id, full_name, email
            FROM users
            WHERE full_name LIKE ? COLLATE NOCASE
               OR email LIKE ? COLLATE NOCASE
            ORDER BY id DESC
        """, (pattern, pattern)).fetchall()

def login(email, password):
    user = get_user_by_email(email)

    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {"id": user["id"], "full_name": user["full_name"], "email": user["email"]}



def get_all_users():
    with get_connection() as connection:
        return connection.execute(""" SELECT id, full_name, email FROM users ORDER BY id DESC """).fetchall()

