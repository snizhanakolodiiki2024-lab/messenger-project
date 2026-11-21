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
    if not token:
        return None

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


def get_user_chats(user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                c.ChatId,

                other_user.UserId AS OtherUserId,
                other_user.Username AS OtherUsername,
                other_user.DisplayName AS OtherDisplayName,

                (
                    SELECT m.Text
                    FROM Messages m
                    WHERE
                        m.ChatId = c.ChatId
                        AND m.IsDeleted = 0
                        AND (
                            current_member.ClearedAt IS NULL
                            OR m.SentAt > current_member.ClearedAt
                        )
                    ORDER BY m.SentAt DESC, m.MessageId DESC
                    LIMIT 1
                ) AS LastMessage,

                (
                    SELECT m.SentAt
                    FROM Messages m
                    WHERE
                        m.ChatId = c.ChatId
                        AND m.IsDeleted = 0
                        AND (
                            current_member.ClearedAt IS NULL
                            OR m.SentAt > current_member.ClearedAt
                        )
                    ORDER BY m.SentAt DESC, m.MessageId DESC
                    LIMIT 1
                ) AS LastMessageAt,

                (
                    SELECT COUNT(*)
                    FROM Messages m
                    WHERE
                        m.ChatId = c.ChatId
                        AND m.SenderId != ?
                        AND m.ReadAt IS NULL
                        AND m.IsDeleted = 0
                        AND (
                            current_member.ClearedAt IS NULL
                            OR m.SentAt > current_member.ClearedAt
                        )
                ) AS UnreadCount

            FROM ChatMembers current_member

            JOIN Chats c
                ON c.ChatId = current_member.ChatId

            JOIN ChatMembers other_member
                ON other_member.ChatId = c.ChatId
                AND other_member.UserId != current_member.UserId

            JOIN Users other_user
                ON other_user.UserId = other_member.UserId

            WHERE
                current_member.UserId = ?
                AND other_user.IsDeleted = 0

            ORDER BY
                COALESCE(LastMessageAt, c.CreatedAt) DESC
            """,
            (
                user_id,
                user_id
            )
        )

        chats = cursor.fetchall()

    return [
        {
            "chat_id": chat["ChatId"],
            "user_id": chat["OtherUserId"],
            "username": chat["OtherUsername"],
            "display_name": chat["OtherDisplayName"],
            "last_message": chat["LastMessage"],
            "last_message_at": chat["LastMessageAt"],
            "unread_count": chat["UnreadCount"]
        }
        for chat in chats
    ]


def save_message(sender_id, recipient_id, text):
    if not isinstance(text, str) or not text.strip():
        return {
            "success": False,
            "message": "Текст повідомлення не може бути порожнім."
        }

    try:
        recipient_id = int(recipient_id)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Некоректний отримувач."
        }

    if sender_id == recipient_id:
        return {
            "success": False,
            "message": "Не можна надіслати повідомлення самому собі."
        }

    text = text.strip()

    with get_connection() as connection:
        recipient = connection.execute(
            """
            SELECT UserId
            FROM Users
            WHERE
                UserId = ?
                AND IsDeleted = 0
                AND IsBlocked = 0
            """,
            (recipient_id,)
        ).fetchone()

        if recipient is None:
            return {
                "success": False,
                "message": "Отримувача не знайдено."
            }

        chat = connection.execute(
            """
            SELECT c.ChatId
            FROM Chats c

            JOIN ChatMembers first_member
                ON first_member.ChatId = c.ChatId
                AND first_member.UserId = ?

            JOIN ChatMembers second_member
                ON second_member.ChatId = c.ChatId
                AND second_member.UserId = ?

            WHERE (
                SELECT COUNT(*)
                FROM ChatMembers member_count
                WHERE member_count.ChatId = c.ChatId
            ) = 2

            LIMIT 1
            """,
            (
                sender_id,
                recipient_id
            )
        ).fetchone()

        if chat is None:
            cursor = connection.execute(
                """
                INSERT INTO Chats DEFAULT VALUES
                """
            )

            chat_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO ChatMembers (ChatId, UserId)
                VALUES (?, ?)
                """,
                (chat_id, sender_id)
            )

            connection.execute(
                """
                INSERT INTO ChatMembers (ChatId, UserId)
                VALUES (?, ?)
                """,
                (chat_id, recipient_id)
            )

        else:
            chat_id = chat["ChatId"]

        cursor = connection.execute(
            """
            INSERT INTO Messages (
                ChatId,
                SenderId,
                Text,
                ReadAt,
                IsDeleted
            )
            VALUES (?, ?, ?, NULL, 0)
            """,
            (
                chat_id,
                sender_id,
                text
            )
        )

        message_id = cursor.lastrowid

        message = connection.execute(
            """
            SELECT *
            FROM Messages
            WHERE MessageId = ?
            """,
            (message_id,)
        ).fetchone()

    return {
        "success": True,
        "message": "Повідомлення успішно збережено.",
        "message_data": {
            "message_id": message["MessageId"],
            "chat_id": message["ChatId"],
            "sender_id": message["SenderId"],
            "text": message["Text"],
            "sent_at": message["SentAt"],
            "read_at": message["ReadAt"],
            "is_deleted": message["IsDeleted"]
        }
    }


def get_chat_history(user_id, chat_id):
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Некоректний ідентифікатор чату."
        }

    with get_connection() as connection:
        membership = connection.execute(
            """
            SELECT ClearedAt
            FROM ChatMembers
            WHERE
                ChatId = ?
                AND UserId = ?
            """,
            (
                chat_id,
                user_id
            )
        ).fetchone()

        if membership is None:
            return {
                "success": False,
                "message": "Користувач не має доступу до цього чату."
            }

        cleared_at = membership["ClearedAt"]

        cursor = connection.execute(
            """
            SELECT
                m.MessageId,
                m.ChatId,
                m.SenderId,
                u.Username AS SenderUsername,
                u.DisplayName AS SenderDisplayName,
                m.Text,
                m.SentAt,
                m.ReadAt

            FROM Messages m

            JOIN Users u
                ON u.UserId = m.SenderId

            WHERE
                m.ChatId = ?
                AND m.IsDeleted = 0
                AND (
                    ? IS NULL
                    OR m.SentAt > ?
                )

            ORDER BY
                m.SentAt ASC,
                m.MessageId ASC
            """,
            (
                chat_id,
                cleared_at,
                cleared_at
            )
        )

        messages = cursor.fetchall()

    return {
        "success": True,
        "messages": [
            {
                "message_id": message["MessageId"],
                "chat_id": message["ChatId"],
                "sender_id": message["SenderId"],
                "sender_username": message["SenderUsername"],
                "sender_display_name": message["SenderDisplayName"],
                "text": message["Text"],
                "sent_at": message["SentAt"],
                "read_at": message["ReadAt"]
            }
            for message in messages
        ]
    }


def mark_messages_as_read(user_id, chat_id):
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Некоректний ідентифікатор чату."
        }

    with get_connection() as connection:
        membership = connection.execute(
            """
            SELECT 1
            FROM ChatMembers
            WHERE
                ChatId = ?
                AND UserId = ?
            """,
            (
                chat_id,
                user_id
            )
        ).fetchone()

        if membership is None:
            return {
                "success": False,
                "message": "Користувач не має доступу до цього чату."
            }

        read_at = connection.execute(
            """
            SELECT datetime('now')
            """
        ).fetchone()[0]

        cursor = connection.execute(
            """
            UPDATE Messages
            SET ReadAt = ?
            WHERE
                ChatId = ?
                AND SenderId != ?
                AND ReadAt IS NULL
                AND IsDeleted = 0
            """,
            (
                read_at,
                chat_id,
                user_id
            )
        )

        updated_count = cursor.rowcount

    return {
        "success": True,
        "message": "Повідомлення позначено як прочитані.",
        "updated_count": updated_count,
        "read_at": read_at
    }


if __name__ == "__main__":
    initialize_database()