import sqlite3
import hashlib
import secrets
import hmac
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "messenger.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    with get_connection() as connection:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)

    print("Database initialized successfully.")


def hash_password(password, salt=None):
    if salt is None:
        salt_bytes = secrets.token_bytes(16)
    else:
        salt_bytes = bytes.fromhex(salt)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        200000
    )

    return password_hash.hex(), salt_bytes.hex()


def get_user_by_login(username):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM Users
            WHERE Username = ?
            """,
            (username,)
        )

        return cursor.fetchone()


def create_user(username, display_name, password):
    if not username or not display_name or not password:
        return {
            "success": False,
            "message": "Усі поля повинні бути заповнені."
        }

    if get_user_by_login(username) is not None:
        return {
            "success": False,
            "message": "Користувач з таким логіном уже існує."
        }

    password_hash, password_salt = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO Users (
                    Username,
                    DisplayName,
                    PasswordHash,
                    PasswordSalt,
                    Role,
                    IsBlocked,
                    IsDeleted
                )
                VALUES (?, ?, ?, ?, 'USER', 0, 0)
                """,
                (
                    username,
                    display_name,
                    password_hash,
                    password_salt
                )
            )

        return {
            "success": True,
            "message": "Користувача успішно зареєстровано."
        }

    except sqlite3.IntegrityError:
        return {
            "success": False,
            "message": "Не вдалося створити користувача."
        }


def authenticate_user(username, password):
    user = get_user_by_login(username)

    if user is None:
        return {
            "success": False,
            "message": "Користувача не знайдено."
        }

    if user["IsDeleted"] == 1:
        return {
            "success": False,
            "message": "Обліковий запис видалено."
        }

    if user["IsBlocked"] == 1:
        return {
            "success": False,
            "message": "Обліковий запис заблоковано."
        }

    entered_hash, _ = hash_password(
        password,
        user["PasswordSalt"]
    )

    if not hmac.compare_digest(
        entered_hash,
        user["PasswordHash"]
    ):
        return {
            "success": False,
            "message": "Неправильний пароль."
        }

    session_token = create_session(user["UserId"])

    return {
        "success": True,
        "message": "Автентифікація успішна.",
        "user_id": user["UserId"],
        "username": user["Username"],
        "display_name": user["DisplayName"],
        "role": user["Role"],
        "token": session_token
    }


def create_session(user_id):
    token = secrets.token_hex(32)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO Sessions (
                UserId,
                Token,
                IsActive
            )
            VALUES (?, ?, 1)
            """,
            (user_id, token)
        )

    return token


def get_session(token):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM Sessions
            WHERE Token = ?
              AND IsActive = 1
            """,
            (token,)
        )

        return cursor.fetchone()


def close_session(token):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE Sessions
            SET IsActive = 0
            WHERE Token = ?
              AND IsActive = 1
            """,
            (token,)
        )

    return cursor.rowcount > 0


def search_users(search_text, current_user_id):
    """
    Шукає користувачів за логіном або відображуваним ім'ям.
    Поточний користувач не включається у результати.
    """

    if not search_text:
        return []

    search_pattern = f"%{search_text}%"

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                UserId,
                Username,
                DisplayName
            FROM Users
            WHERE
                UserId != ?
                AND IsDeleted = 0
                AND IsBlocked = 0
                AND (
                    Username LIKE ?
                    OR DisplayName LIKE ?
                )
            ORDER BY DisplayName
            LIMIT 20
            """,
            (
                current_user_id,
                search_pattern,
                search_pattern
            )
        )

        users = cursor.fetchall()

    return [
        {
            "user_id": user["UserId"],
            "username": user["Username"],
            "display_name": user["DisplayName"]
        }
        for user in users
    ]


if __name__ == "__main__":
    initialize_database()