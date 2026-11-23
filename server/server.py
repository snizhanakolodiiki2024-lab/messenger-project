# -*- coding: utf-8 -*-

import socket
import threading
import json
import codecs
import sys
from pathlib import Path


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))


# =========================================================
# DATABASE
# =========================================================

from database.db import (
    get_connection,
    create_user,
    authenticate_user,
    is_username_available
)


# =========================================================
# SERVER SETTINGS
# =========================================================

HOST = "127.0.0.1"
PORT = 5000


# =========================================================
# ONLINE USERS
# =========================================================

online_clients = {}
online_clients_lock = threading.Lock()

socket_send_locks = {}
socket_send_locks_lock = threading.Lock()


# =========================================================
# JSON
# =========================================================

def get_socket_lock(client_socket):
    with socket_send_locks_lock:
        if client_socket not in socket_send_locks:
            socket_send_locks[
                client_socket
            ] = threading.Lock()

        return socket_send_locks[
            client_socket
        ]


def send_json(client_socket, data):
    """
    Надсилає JSON-пакет клієнту.
    """

    message = (
        json.dumps(
            data,
            ensure_ascii=False
        )
        + "\n"
    )

    encoded = message.encode(
        "utf-8"
    )

    lock = get_socket_lock(
        client_socket
    )

    with lock:
        client_socket.sendall(
            encoded
        )


# =========================================================
# SESSION
# =========================================================

def get_session_user(token):
    """
    Повертає користувача активної сесії.
    """

    if not token:
        return None

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                u.UserId,
                u.Username,
                u.DisplayName,
                u.Role,
                u.IsBlocked,
                u.IsDeleted
            FROM Sessions s
            JOIN Users u
                ON u.UserId = s.UserId
            WHERE
                s.Token = ?
                AND s.IsActive = 1
            LIMIT 1
            """,
            (token,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)


def end_session(token):
    """
    Завершує активну сесію.
    """

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE Sessions
            SET IsActive = 0
            WHERE
                Token = ?
                AND IsActive = 1
            """,
            (token,)
        )

        return cursor.rowcount > 0


# =========================================================
# AUDIT LOG
# =========================================================

def add_audit_log(
    user_id,
    event_type,
    description
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO AuditLog (
                UserId,
                EventType,
                Description,
                CreatedAt
            )
            VALUES (?, ?, ?, datetime('now'))
            """,
            (
                user_id,
                event_type,
                description
            )
        )


# =========================================================
# ONLINE CLIENTS
# =========================================================

def set_user_online(
    user_id,
    client_socket
):
    with online_clients_lock:
        online_clients[
            user_id
        ] = client_socket

    print(
        f"User {user_id} is ONLINE."
    )


def set_user_offline(
    user_id,
    client_socket=None
):
    if user_id is None:
        return

    with online_clients_lock:
        current_socket = (
            online_clients.get(
                user_id
            )
        )

        if (
            client_socket is None
            or current_socket
            is client_socket
        ):
            online_clients.pop(
                user_id,
                None
            )

    print(
        f"User {user_id} is OFFLINE."
    )


def get_online_socket(user_id):
    with online_clients_lock:
        return online_clients.get(
            user_id
        )


def send_event_to_user(
    user_id,
    event
):
    client_socket = get_online_socket(
        user_id
    )

    if client_socket is None:
        return False

    try:
        send_json(
            client_socket,
            event
        )

        return True

    except OSError:
        set_user_offline(
            user_id,
            client_socket
        )

        return False


# =========================================================
# SEARCH USERS
# =========================================================

def search_users(
    search_text,
    current_user_id
):
    search_text = (
        search_text
        .strip()
    )

    if not search_text:
        return []

    pattern = (
        f"%{search_text}%"
    )

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
                pattern,
                pattern
            )
        )

        users = []

        for row in cursor.fetchall():
            users.append(
                {
                    "user_id": row[
                        "UserId"
                    ],
                    "username": row[
                        "Username"
                    ],
                    "display_name": row[
                        "DisplayName"
                    ]
                }
            )

        return users


# =========================================================
# CHAT HELPERS
# =========================================================

def get_chat_between_users(
    first_user_id,
    second_user_id
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT c.ChatId
            FROM Chats c
            JOIN ChatMembers cm1
                ON cm1.ChatId = c.ChatId
            JOIN ChatMembers cm2
                ON cm2.ChatId = c.ChatId
            WHERE
                cm1.UserId = ?
                AND cm2.UserId = ?
            LIMIT 1
            """,
            (
                first_user_id,
                second_user_id
            )
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row[
            "ChatId"
        ]


def create_chat(
    first_user_id,
    second_user_id
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO Chats (
                CreatedAt
            )
            VALUES (
                datetime('now')
            )
            """
        )

        chat_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO ChatMembers (
                ChatId,
                UserId,
                ClearedAt
            )
            VALUES (?, ?, NULL)
            """,
            (
                chat_id,
                first_user_id
            )
        )

        connection.execute(
            """
            INSERT INTO ChatMembers (
                ChatId,
                UserId,
                ClearedAt
            )
            VALUES (?, ?, NULL)
            """,
            (
                chat_id,
                second_user_id
            )
        )

        return chat_id


def user_is_chat_member(
    user_id,
    chat_id
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT 1
            FROM ChatMembers
            WHERE
                ChatId = ?
                AND UserId = ?
            LIMIT 1
            """,
            (
                chat_id,
                user_id
            )
        )

        return (
            cursor.fetchone()
            is not None
        )


# =========================================================
# GET CHATS
# =========================================================

def get_user_chats(user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                c.ChatId,
                other.UserId,
                other.Username,
                other.DisplayName,
                mine.ClearedAt
            FROM Chats c

            JOIN ChatMembers mine
                ON mine.ChatId = c.ChatId
                AND mine.UserId = ?

            JOIN ChatMembers other_member
                ON other_member.ChatId = c.ChatId
                AND other_member.UserId != ?

            JOIN Users other
                ON other.UserId =
                   other_member.UserId

            WHERE
                other.IsDeleted = 0

            ORDER BY c.CreatedAt DESC
            """,
            (
                user_id,
                user_id
            )
        )

        chat_rows = cursor.fetchall()

        chats = []

        for chat_row in chat_rows:
            chat_id = chat_row[
                "ChatId"
            ]

            cleared_at = chat_row[
                "ClearedAt"
            ]

            if cleared_at:
                last_cursor = (
                    connection.execute(
                        """
                        SELECT
                            Text,
                            SentAt
                        FROM Messages
                        WHERE
                            ChatId = ?
                            AND IsDeleted = 0
                            AND SentAt > ?
                        ORDER BY
                            SentAt DESC,
                            MessageId DESC
                        LIMIT 1
                        """,
                        (
                            chat_id,
                            cleared_at
                        )
                    )
                )

            else:
                last_cursor = (
                    connection.execute(
                        """
                        SELECT
                            Text,
                            SentAt
                        FROM Messages
                        WHERE
                            ChatId = ?
                            AND IsDeleted = 0
                        ORDER BY
                            SentAt DESC,
                            MessageId DESC
                        LIMIT 1
                        """,
                        (chat_id,)
                    )
                )

            last_message_row = (
                last_cursor.fetchone()
            )

            if last_message_row:
                last_message = (
                    last_message_row[
                        "Text"
                    ]
                )

                last_message_at = (
                    last_message_row[
                        "SentAt"
                    ]
                )

            else:
                last_message = None
                last_message_at = None

            if cleared_at:
                unread_cursor = (
                    connection.execute(
                        """
                        SELECT COUNT(*) AS CountValue
                        FROM Messages
                        WHERE
                            ChatId = ?
                            AND SenderId != ?
                            AND ReadAt IS NULL
                            AND IsDeleted = 0
                            AND SentAt > ?
                        """,
                        (
                            chat_id,
                            user_id,
                            cleared_at
                        )
                    )
                )

            else:
                unread_cursor = (
                    connection.execute(
                        """
                        SELECT COUNT(*) AS CountValue
                        FROM Messages
                        WHERE
                            ChatId = ?
                            AND SenderId != ?
                            AND ReadAt IS NULL
                            AND IsDeleted = 0
                        """,
                        (
                            chat_id,
                            user_id
                        )
                    )
                )

            unread_row = (
                unread_cursor.fetchone()
            )

            unread_count = (
                unread_row[
                    "CountValue"
                ]
            )

            chats.append(
                {
                    "chat_id": chat_id,
                    "user_id": chat_row[
                        "UserId"
                    ],
                    "username": chat_row[
                        "Username"
                    ],
                    "display_name": chat_row[
                        "DisplayName"
                    ],
                    "last_message": (
                        last_message
                    ),
                    "last_message_at": (
                        last_message_at
                    ),
                    "unread_count": (
                        unread_count
                    )
                }
            )

        chats.sort(
            key=lambda chat: (
                chat[
                    "last_message_at"
                ]
                or ""
            ),
            reverse=True
        )

        return chats


# =========================================================
# HISTORY
# =========================================================

def get_chat_history(
    user_id,
    chat_id
):
    if not user_is_chat_member(
        user_id,
        chat_id
    ):
        return None

    with get_connection() as connection:
        member_cursor = (
            connection.execute(
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
            )
        )

        member = (
            member_cursor.fetchone()
        )

        cleared_at = (
            member["ClearedAt"]
            if member
            else None
        )

        if cleared_at:
            cursor = connection.execute(
                """
                SELECT
                    m.MessageId,
                    m.ChatId,
                    m.SenderId,
                    u.Username,
                    u.DisplayName,
                    m.Text,
                    m.SentAt,
                    m.ReadAt
                FROM Messages m
                JOIN Users u
                    ON u.UserId = m.SenderId
                WHERE
                    m.ChatId = ?
                    AND m.IsDeleted = 0
                    AND m.SentAt > ?
                ORDER BY
                    m.SentAt ASC,
                    m.MessageId ASC
                """,
                (
                    chat_id,
                    cleared_at
                )
            )

        else:
            cursor = connection.execute(
                """
                SELECT
                    m.MessageId,
                    m.ChatId,
                    m.SenderId,
                    u.Username,
                    u.DisplayName,
                    m.Text,
                    m.SentAt,
                    m.ReadAt
                FROM Messages m
                JOIN Users u
                    ON u.UserId = m.SenderId
                WHERE
                    m.ChatId = ?
                    AND m.IsDeleted = 0
                ORDER BY
                    m.SentAt ASC,
                    m.MessageId ASC
                """,
                (chat_id,)
            )

        messages = []

        for row in cursor.fetchall():
            messages.append(
                {
                    "message_id": row[
                        "MessageId"
                    ],
                    "chat_id": row[
                        "ChatId"
                    ],
                    "sender_id": row[
                        "SenderId"
                    ],
                    "sender_username": row[
                        "Username"
                    ],
                    "sender_display_name": row[
                        "DisplayName"
                    ],
                    "text": row[
                        "Text"
                    ],
                    "sent_at": row[
                        "SentAt"
                    ],
                    "read_at": row[
                        "ReadAt"
                    ]
                }
            )

        return messages


# =========================================================
# SEND MESSAGE
# =========================================================

def save_message(
    sender_id,
    recipient_id,
    text
):
    text = (
        text
        .strip()
    )

    if not text:
        return {
            "success": False,
            "message": (
                "Повідомлення не може "
                "бути порожнім."
            )
        }

    if sender_id == recipient_id:
        return {
            "success": False,
            "message": (
                "Неможливо надіслати "
                "повідомлення самому собі."
            )
        }

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                UserId,
                IsBlocked,
                IsDeleted
            FROM Users
            WHERE UserId = ?
            LIMIT 1
            """,
            (recipient_id,)
        )

        recipient = cursor.fetchone()

        if recipient is None:
            return {
                "success": False,
                "message": (
                    "Отримувача не знайдено."
                )
            }

        if recipient[
            "IsDeleted"
        ]:
            return {
                "success": False,
                "message": (
                    "Обліковий запис "
                    "отримувача видалено."
                )
            }

        if recipient[
            "IsBlocked"
        ]:
            return {
                "success": False,
                "message": (
                    "Обліковий запис "
                    "отримувача заблоковано."
                )
            }

    chat_id = get_chat_between_users(
        sender_id,
        recipient_id
    )

    if chat_id is None:
        chat_id = create_chat(
            sender_id,
            recipient_id
        )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO Messages (
                ChatId,
                SenderId,
                Text,
                SentAt,
                ReadAt,
                IsDeleted
            )
            VALUES (
                ?,
                ?,
                ?,
                datetime('now'),
                NULL,
                0
            )
            """,
            (
                chat_id,
                sender_id,
                text
            )
        )

        message_id = (
            cursor.lastrowid
        )

        cursor = connection.execute(
            """
            SELECT
                MessageId,
                ChatId,
                SenderId,
                Text,
                SentAt,
                ReadAt,
                IsDeleted
            FROM Messages
            WHERE MessageId = ?
            """,
            (message_id,)
        )

        row = cursor.fetchone()

        message_data = {
            "message_id": row[
                "MessageId"
            ],
            "chat_id": row[
                "ChatId"
            ],
            "sender_id": row[
                "SenderId"
            ],
            "text": row[
                "Text"
            ],
            "sent_at": row[
                "SentAt"
            ],
            "read_at": row[
                "ReadAt"
            ],
            "is_deleted": row[
                "IsDeleted"
            ]
        }

        return {
            "success": True,
            "message": (
                "Повідомлення успішно "
                "збережено."
            ),
            "message_data": (
                message_data
            )
        }


# =========================================================
# MARK AS READ
# =========================================================

def mark_chat_as_read(
    user_id,
    chat_id
):
    if not user_is_chat_member(
        user_id,
        chat_id
    ):
        return {
            "success": False,
            "message": (
                "Немає доступу до діалогу."
            )
        }

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                MessageId,
                SenderId
            FROM Messages
            WHERE
                ChatId = ?
                AND SenderId != ?
                AND ReadAt IS NULL
                AND IsDeleted = 0
            """,
            (
                chat_id,
                user_id
            )
        )

        rows = cursor.fetchall()

        message_ids = [
            row[
                "MessageId"
            ]
            for row in rows
        ]

        sender_ids = list(
            {
                row[
                    "SenderId"
                ]
                for row in rows
            }
        )

        if not message_ids:
            return {
                "success": True,
                "message": (
                    "Непрочитаних "
                    "повідомлень немає."
                ),
                "updated_count": 0,
                "read_at": None,
                "message_ids": [],
                "sender_ids": []
            }

        connection.execute(
            """
            UPDATE Messages
            SET ReadAt = datetime('now')
            WHERE
                ChatId = ?
                AND SenderId != ?
                AND ReadAt IS NULL
                AND IsDeleted = 0
            """,
            (
                chat_id,
                user_id
            )
        )

        cursor = connection.execute(
            """
            SELECT datetime('now')
            AS ReadTime
            """
        )

        read_at = cursor.fetchone()[
            "ReadTime"
        ]

        return {
            "success": True,
            "message": (
                "Повідомлення позначено "
                "як прочитані."
            ),
            "updated_count": len(
                message_ids
            ),
            "read_at": read_at,
            "message_ids": message_ids,
            "sender_ids": sender_ids
        }


# =========================================================
# DELETE MESSAGE
# =========================================================

def delete_own_message(
    user_id,
    message_id
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                MessageId,
                ChatId,
                SenderId,
                IsDeleted
            FROM Messages
            WHERE MessageId = ?
            LIMIT 1
            """,
            (message_id,)
        )

        message = cursor.fetchone()

        if message is None:
            return {
                "success": False,
                "message": (
                    "Повідомлення не знайдено."
                )
            }

        if (
            message[
                "SenderId"
            ]
            != user_id
        ):
            return {
                "success": False,
                "message": (
                    "Можна видаляти тільки "
                    "власні повідомлення."
                )
            }

        connection.execute(
            """
            UPDATE Messages
            SET IsDeleted = 1
            WHERE MessageId = ?
            """,
            (message_id,)
        )

        return {
            "success": True,
            "message": (
                "Повідомлення успішно "
                "видалено."
            ),
            "message_id": (
                message_id
            ),
            "chat_id": message[
                "ChatId"
            ]
        }


# =========================================================
# CLEAR CHAT
# =========================================================

def clear_chat_for_user(
    user_id,
    chat_id
):
    if not user_is_chat_member(
        user_id,
        chat_id
    ):
        return {
            "success": False,
            "message": (
                "Немає доступу до діалогу."
            )
        }

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE ChatMembers
            SET ClearedAt = datetime('now')
            WHERE
                ChatId = ?
                AND UserId = ?
            """,
            (
                chat_id,
                user_id
            )
        )

        cursor = connection.execute(
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
        )

        row = cursor.fetchone()

        return {
            "success": True,
            "message": (
                "Переписку успішно очищено."
            ),
            "chat_id": chat_id,
            "cleared_at": row[
                "ClearedAt"
            ]
        }


# =========================================================
# ADMIN HELPERS
# =========================================================

def is_admin(user):
    return (
        user is not None
        and user.get(
            "Role"
        )
        == "ADMIN"
    )


def get_all_users():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                UserId,
                Username,
                DisplayName,
                Role,
                IsBlocked,
                IsDeleted,
                CreatedAt
            FROM Users
            ORDER BY UserId
            """
        )

        users = []

        for row in cursor.fetchall():
            users.append(
                {
                    "user_id": row[
                        "UserId"
                    ],
                    "username": row[
                        "Username"
                    ],
                    "display_name": row[
                        "DisplayName"
                    ],
                    "role": row[
                        "Role"
                    ],
                    "is_blocked": row[
                        "IsBlocked"
                    ],
                    "is_deleted": row[
                        "IsDeleted"
                    ],
                    "created_at": row[
                        "CreatedAt"
                    ]
                }
            )

        return users


def get_user_by_id(user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                UserId,
                Username,
                DisplayName,
                Role,
                IsBlocked,
                IsDeleted
            FROM Users
            WHERE UserId = ?
            LIMIT 1
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)


def deactivate_user_sessions(
    user_id
):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE Sessions
            SET IsActive = 0
            WHERE
                UserId = ?
                AND IsActive = 1
            """,
            (user_id,)
        )


def block_user_account(
    admin_user,
    target_user_id
):
    target = get_user_by_id(
        target_user_id
    )

    if target is None:
        return {
            "success": False,
            "message": (
                "Користувача не знайдено."
            )
        }

    if target[
        "Role"
    ] == "ADMIN":
        return {
            "success": False,
            "message": (
                "Адміністратора "
                "блокувати не можна."
            )
        }

    if target[
        "IsDeleted"
    ]:
        return {
            "success": False,
            "message": (
                "Обліковий запис "
                "вже видалено."
            )
        }

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE Users
            SET IsBlocked = 1
            WHERE UserId = ?
            """,
            (target_user_id,)
        )

    deactivate_user_sessions(
        target_user_id
    )

    add_audit_log(
        admin_user[
            "UserId"
        ],
        "USER_BLOCKED",
        (
            "Адміністратор заблокував "
            f"користувача "
            f"'{target['Username']}' "
            f"(ID {target_user_id})."
        )
    )

    return {
        "success": True,
        "message": (
            "Користувача успішно "
            "заблоковано."
        ),
        "user_id": target_user_id,
        "username": target[
            "Username"
        ]
    }


def unblock_user_account(
    admin_user,
    target_user_id
):
    target = get_user_by_id(
        target_user_id
    )

    if target is None:
        return {
            "success": False,
            "message": (
                "Користувача не знайдено."
            )
        }

    if target[
        "Role"
    ] == "ADMIN":
        return {
            "success": False,
            "message": (
                "Адміністратора "
                "розблоковувати не потрібно."
            )
        }

    if target[
        "IsDeleted"
    ]:
        return {
            "success": False,
            "message": (
                "Обліковий запис видалено."
            )
        }

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE Users
            SET IsBlocked = 0
            WHERE UserId = ?
            """,
            (target_user_id,)
        )

    add_audit_log(
        admin_user[
            "UserId"
        ],
        "USER_UNBLOCKED",
        (
            "Адміністратор розблокував "
            f"користувача "
            f"'{target['Username']}' "
            f"(ID {target_user_id})."
        )
    )

    return {
        "success": True,
        "message": (
            "Користувача успішно "
            "розблоковано."
        ),
        "user_id": target_user_id,
        "username": target[
            "Username"
        ]
    }


def delete_user_account(
    admin_user,
    target_user_id
):
    target = get_user_by_id(
        target_user_id
    )

    if target is None:
        return {
            "success": False,
            "message": (
                "Користувача не знайдено."
            )
        }

    if target[
        "Role"
    ] == "ADMIN":
        return {
            "success": False,
            "message": (
                "Обліковий запис "
                "адміністратора видаляти "
                "не можна."
            )
        }

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE Users
            SET IsDeleted = 1
            WHERE UserId = ?
            """,
            (target_user_id,)
        )

    deactivate_user_sessions(
        target_user_id
    )

    add_audit_log(
        admin_user[
            "UserId"
        ],
        "USER_DELETED",
        (
            "Адміністратор видалив "
            f"обліковий запис "
            f"'{target['Username']}' "
            f"(ID {target_user_id})."
        )
    )

    return {
        "success": True,
        "message": (
            "Обліковий запис користувача "
            "успішно видалено."
        ),
        "user_id": target_user_id,
        "username": target[
            "Username"
        ]
    }


def get_audit_logs(limit=100):
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 100

    limit = max(
        1,
        min(
            limit,
            500
        )
    )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                a.LogId,
                a.UserId,
                u.Username,
                a.EventType,
                a.Description,
                a.CreatedAt
            FROM AuditLog a
            LEFT JOIN Users u
                ON u.UserId = a.UserId
            ORDER BY
                a.LogId DESC
            LIMIT ?
            """,
            (limit,)
        )

        logs = []

        for row in cursor.fetchall():
            logs.append(
                {
                    "log_id": row[
                        "LogId"
                    ],
                    "user_id": row[
                        "UserId"
                    ],
                    "username": row[
                        "Username"
                    ],
                    "event_type": row[
                        "EventType"
                    ],
                    "description": row[
                        "Description"
                    ],
                    "created_at": row[
                        "CreatedAt"
                    ]
                }
            )

        return logs


# =========================================================
# CLIENT HANDLER
# =========================================================

def handle_client(
    client_socket,
    client_address
):
    print(
        f"Client connected: "
        f"{client_address}"
    )

    buffer = ""

    current_user_id = None

    decoder = codecs.getincrementaldecoder(
        "utf-8"
    )()

    try:
        while True:
            data = client_socket.recv(
                4096
            )

            if not data:
                break

            buffer += decoder.decode(
                data
            )

            while "\n" in buffer:
                message, buffer = (
                    buffer.split(
                        "\n",
                        1
                    )
                )

                if not message.strip():
                    continue

                try:
                    request = json.loads(
                        message
                    )

                except json.JSONDecodeError:
                    send_json(
                        client_socket,
                        {
                            "status": "ERROR",
                            "message": (
                                "Некоректний JSON."
                            )
                        }
                    )

                    continue

                print(
                    f"Request from "
                    f"{client_address}:",
                    request
                )

                request_type = (
                    request.get(
                        "type"
                    )
                )

                # =========================================
                # PING
                # =========================================

                if request_type == "PING":
                    send_json(
                        client_socket,
                        {
                            "status": "OK",
                            "message": "PONG"
                        }
                    )

                # =========================================
                # CHECK USERNAME
                # =========================================

                elif (
                    request_type
                    == "CHECK_USERNAME"
                ):
                    username = (
                        request.get(
                            "username",
                            ""
                        )
                        .strip()
                    )

                    if len(username) < 3:
                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "available": False,
                                "message": (
                                    "Логін повинен "
                                    "містити щонайменше "
                                    "3 символи."
                                )
                            }
                        )

                    else:
                        available = (
                            is_username_available(
                                username
                            )
                        )

                        if available:
                            response_message = (
                                "Логін вільний."
                            )

                        else:
                            response_message = (
                                "Користувач з таким "
                                "логіном уже існує."
                            )

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "available": (
                                    available
                                ),
                                "message": (
                                    response_message
                                )
                            }
                        )

                # =========================================
                # REGISTER
                # =========================================

                elif (
                    request_type
                    == "REGISTER"
                ):
                    result = create_user(
                        username=request.get(
                            "username"
                        ),
                        display_name=request.get(
                            "display_name"
                        ),
                        password=request.get(
                            "password"
                        )
                    )

                    send_json(
                        client_socket,
                        {
                            "status": (
                                "OK"
                                if result[
                                    "success"
                                ]
                                else "ERROR"
                            ),
                            "message": result[
                                "message"
                            ]
                        }
                    )

                # =========================================
                # LOGIN
                # =========================================

                elif (
                    request_type
                    == "LOGIN"
                ):
                    result = (
                        authenticate_user(
                            username=request.get(
                                "username"
                            ),
                            password=request.get(
                                "password"
                            )
                        )
                    )

                    if result[
                        "success"
                    ]:
                        current_user_id = (
                            result[
                                "user_id"
                            ]
                        )

                        set_user_online(
                            current_user_id,
                            client_socket
                        )

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "message": (
                                    result[
                                        "message"
                                    ]
                                ),
                                "user_id": (
                                    result[
                                        "user_id"
                                    ]
                                ),
                                "username": (
                                    result[
                                        "username"
                                    ]
                                ),
                                "display_name": (
                                    result[
                                        "display_name"
                                    ]
                                ),
                                "role": (
                                    result[
                                        "role"
                                    ]
                                ),
                                "token": (
                                    result[
                                        "token"
                                    ]
                                )
                            }
                        )

                    else:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": (
                                    result[
                                        "message"
                                    ]
                                )
                            }
                        )

                # =========================================
                # LOGOUT
                # =========================================

                elif (
                    request_type
                    == "LOGOUT"
                ):
                    token = request.get(
                        "token"
                    )

                    session_user = (
                        get_session_user(
                            token
                        )
                    )

                    if session_user is None:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": (
                                    "Недійсна або "
                                    "завершена сесія."
                                )
                            }
                        )

                    else:
                        user_id = session_user[
                            "UserId"
                        ]

                        username = session_user[
                            "Username"
                        ]

                        end_session(
                            token
                        )

                        set_user_offline(
                            user_id,
                            client_socket
                        )

                        add_audit_log(
                            user_id,
                            "LOGOUT",
                            (
                                f"Користувач "
                                f"'{username}' "
                                f"вийшов із системи."
                            )
                        )

                        current_user_id = None

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "message": (
                                    "Сесію успішно "
                                    "завершено."
                                )
                            }
                        )

                # =========================================
                # PROTECTED REQUESTS
                # =========================================

                else:
                    token = request.get(
                        "token"
                    )

                    user = get_session_user(
                        token
                    )

                    if user is None:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": (
                                    "Недійсна або "
                                    "завершена сесія."
                                )
                            }
                        )

                        continue

                    if user[
                        "IsDeleted"
                    ]:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": (
                                    "Обліковий запис "
                                    "видалено."
                                )
                            }
                        )

                        continue

                    if user[
                        "IsBlocked"
                    ]:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": (
                                    "Обліковий запис "
                                    "заблоковано."
                                )
                            }
                        )

                        continue

                    user_id = user[
                        "UserId"
                    ]

                    # =====================================
                    # SEARCH USER
                    # =====================================

                    if (
                        request_type
                        == "SEARCH_USER"
                    ):
                        users = search_users(
                            request.get(
                                "query",
                                ""
                            ),
                            user_id
                        )

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "users": users
                            }
                        )

                    # =====================================
                    # GET CHATS
                    # =====================================

                    elif (
                        request_type
                        == "GET_CHATS"
                    ):
                        chats = get_user_chats(
                            user_id
                        )

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "chats": chats
                            }
                        )

                    # =====================================
                    # GET HISTORY
                    # =====================================

                    elif (
                        request_type
                        == "GET_HISTORY"
                    ):
                        chat_id = request.get(
                            "chat_id"
                        )

                        messages = (
                            get_chat_history(
                                user_id,
                                chat_id
                            )
                        )

                        if messages is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        "Немає доступу "
                                        "до діалогу."
                                    )
                                }
                            )

                        else:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "messages": (
                                        messages
                                    )
                                }
                            )

                    # =====================================
                    # SEND MESSAGE
                    # =====================================

                    elif (
                        request_type
                        == "SEND_MESSAGE"
                    ):
                        recipient_id = (
                            request.get(
                                "recipient_id"
                            )
                        )

                        text = request.get(
                            "text",
                            ""
                        )

                        result = save_message(
                            user_id,
                            recipient_id,
                            text
                        )

                        if not result[
                            "success"
                        ]:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        result[
                                            "message"
                                        ]
                                    )
                                }
                            )

                        else:
                            message_data = (
                                result[
                                    "message_data"
                                ]
                            )

                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": (
                                        result[
                                            "message"
                                        ]
                                    ),
                                    "message_data": (
                                        message_data
                                    )
                                }
                            )

                            pushed = (
                                send_event_to_user(
                                    recipient_id,
                                    {
                                        "type": (
                                            "NEW_MESSAGE"
                                        ),
                                        "message": (
                                            message_data
                                        )
                                    }
                                )
                            )

                            if pushed:
                                print(
                                    "Message pushed "
                                    "to online user "
                                    f"{recipient_id}."
                                )

                            else:
                                print(
                                    f"Recipient "
                                    f"{recipient_id} "
                                    "is offline. "
                                    "Message remains "
                                    "stored in database."
                                )

                    # =====================================
                    # MARK AS READ
                    # =====================================

                    elif (
                        request_type
                        == "MARK_AS_READ"
                    ):
                        chat_id = request.get(
                            "chat_id"
                        )

                        result = (
                            mark_chat_as_read(
                                user_id,
                                chat_id
                            )
                        )

                        if not result[
                            "success"
                        ]:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        result[
                                            "message"
                                        ]
                                    )
                                }
                            )

                        else:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": (
                                        result[
                                            "message"
                                        ]
                                    ),
                                    "updated_count": (
                                        result[
                                            "updated_count"
                                        ]
                                    ),
                                    "read_at": (
                                        result[
                                            "read_at"
                                        ]
                                    ),
                                    "message_ids": (
                                        result[
                                            "message_ids"
                                        ]
                                    ),
                                    "sender_ids": (
                                        result[
                                            "sender_ids"
                                        ]
                                    )
                                }
                            )

                            if (
                                result[
                                    "message_ids"
                                ]
                            ):
                                for sender_id in (
                                    result[
                                        "sender_ids"
                                    ]
                                ):
                                    send_event_to_user(
                                        sender_id,
                                        {
                                            "type": (
                                                "MESSAGE_READ"
                                            ),
                                            "chat_id": (
                                                chat_id
                                            ),
                                            "message_ids": (
                                                result[
                                                    "message_ids"
                                                ]
                                            ),
                                            "read_at": (
                                                result[
                                                    "read_at"
                                                ]
                                            )
                                        }
                                    )

                    # =====================================
                    # DELETE MESSAGE
                    # =====================================

                    elif (
                        request_type
                        == "DELETE_MESSAGE"
                    ):
                        result = (
                            delete_own_message(
                                user_id,
                                request.get(
                                    "message_id"
                                )
                            )
                        )

                        send_json(
                            client_socket,
                            {
                                "status": (
                                    "OK"
                                    if result[
                                        "success"
                                    ]
                                    else "ERROR"
                                ),
                                **{
                                    key: value
                                    for key, value
                                    in result.items()
                                    if key
                                    != "success"
                                }
                            }
                        )

                    # =====================================
                    # CLEAR CHAT
                    # =====================================

                    elif (
                        request_type
                        == "CLEAR_CHAT"
                    ):
                        result = (
                            clear_chat_for_user(
                                user_id,
                                request.get(
                                    "chat_id"
                                )
                            )
                        )

                        send_json(
                            client_socket,
                            {
                                "status": (
                                    "OK"
                                    if result[
                                        "success"
                                    ]
                                    else "ERROR"
                                ),
                                **{
                                    key: value
                                    for key, value
                                    in result.items()
                                    if key
                                    != "success"
                                }
                            }
                        )

                    # =====================================
                    # GET USERS - ADMIN
                    # =====================================

                    elif (
                        request_type
                        == "GET_USERS"
                    ):
                        if not is_admin(
                            user
                        ):
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        "Недостатньо "
                                        "прав доступу."
                                    )
                                }
                            )

                        else:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "users": (
                                        get_all_users()
                                    )
                                }
                            )

                    # =====================================
                    # BLOCK USER
                    # =====================================

                    elif (
                        request_type
                        == "BLOCK_USER"
                    ):
                        if not is_admin(
                            user
                        ):
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        "Недостатньо "
                                        "прав доступу."
                                    )
                                }
                            )

                        else:
                            target_user_id = (
                                request.get(
                                    "user_id"
                                )
                            )

                            result = (
                                block_user_account(
                                    user,
                                    target_user_id
                                )
                            )

                            send_json(
                                client_socket,
                                {
                                    "status": (
                                        "OK"
                                        if result[
                                            "success"
                                        ]
                                        else "ERROR"
                                    ),
                                    **{
                                        key: value
                                        for key, value
                                        in result.items()
                                        if key
                                        != "success"
                                    }
                                }
                            )

                            if result[
                                "success"
                            ]:
                                send_event_to_user(
                                    target_user_id,
                                    {
                                        "type": (
                                            "SESSION_TERMINATED"
                                        ),
                                        "reason": (
                                            "Ваш обліковий "
                                            "запис заблоковано "
                                            "адміністратором."
                                        )
                                    }
                                )

                                set_user_offline(
                                    target_user_id
                                )

                    # =====================================
                    # UNBLOCK USER
                    # =====================================

                    elif (
                        request_type
                        == "UNBLOCK_USER"
                    ):
                        if not is_admin(
                            user
                        ):
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        "Недостатньо "
                                        "прав доступу."
                                    )
                                }
                            )

                        else:
                            result = (
                                unblock_user_account(
                                    user,
                                    request.get(
                                        "user_id"
                                    )
                                )
                            )

                            send_json(
                                client_socket,
                                {
                                    "status": (
                                        "OK"
                                        if result[
                                            "success"
                                        ]
                                        else "ERROR"
                                    ),
                                    **{
                                        key: value
                                        for key, value
                                        in result.items()
                                        if key
                                        != "success"
                                    }
                                }
                            )

                    # =====================================
                    # DELETE USER
                    # =====================================

                    elif (
                        request_type
                        == "DELETE_USER"
                    ):
                        if not is_admin(
                            user
                        ):
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        "Недостатньо "
                                        "прав доступу."
                                    )
                                }
                            )

                        else:
                            target_user_id = (
                                request.get(
                                    "user_id"
                                )
                            )

                            result = (
                                delete_user_account(
                                    user,
                                    target_user_id
                                )
                            )

                            send_json(
                                client_socket,
                                {
                                    "status": (
                                        "OK"
                                        if result[
                                            "success"
                                        ]
                                        else "ERROR"
                                    ),
                                    **{
                                        key: value
                                        for key, value
                                        in result.items()
                                        if key
                                        != "success"
                                    }
                                }
                            )

                            if result[
                                "success"
                            ]:
                                send_event_to_user(
                                    target_user_id,
                                    {
                                        "type": (
                                            "SESSION_TERMINATED"
                                        ),
                                        "reason": (
                                            "Ваш обліковий "
                                            "запис видалено "
                                            "адміністратором."
                                        )
                                    }
                                )

                                set_user_offline(
                                    target_user_id
                                )

                    # =====================================
                    # AUDIT LOG
                    # =====================================

                    elif (
                        request_type
                        == "GET_AUDIT_LOG"
                    ):
                        if not is_admin(
                            user
                        ):
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": (
                                        "Недостатньо "
                                        "прав доступу."
                                    )
                                }
                            )

                        else:
                            logs = get_audit_logs(
                                request.get(
                                    "limit",
                                    100
                                )
                            )

                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "logs": logs
                                }
                            )

                    # =====================================
                    # UNKNOWN COMMAND
                    # =====================================

                    else:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": (
                                    "Невідома команда."
                                )
                            }
                        )

    except ConnectionResetError:
        print(
            f"Connection lost: "
            f"{client_address}"
        )

    except UnicodeDecodeError:
        print(
            f"Invalid UTF-8 data from "
            f"{client_address}"
        )

    except Exception as error:
        print(
            f"Client error "
            f"{client_address}:",
            error
        )

    finally:
        if current_user_id is not None:
            set_user_offline(
                current_user_id,
                client_socket
            )

        with socket_send_locks_lock:
            socket_send_locks.pop(
                client_socket,
                None
            )

        try:
            client_socket.close()
        except OSError:
            pass

        print(
            f"Client disconnected: "
            f"{client_address}"
        )


# =========================================================
# SERVER
# =========================================================

def start_server():
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (
            HOST,
            PORT
        )
    )

    server_socket.listen()

    print(
        f"Server started on "
        f"{HOST}:{PORT}"
    )

    print(
        "Waiting for clients..."
    )

    try:
        while True:
            (
                client_socket,
                client_address
            ) = server_socket.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(
                    client_socket,
                    client_address
                ),
                daemon=True
            )

            thread.start()

    except KeyboardInterrupt:
        print(
            "\nServer stopped."
        )

    finally:
        server_socket.close()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    start_server()