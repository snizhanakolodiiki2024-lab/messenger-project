import shutil
from datetime import datetime
from pathlib import Path

from db import get_connection, hash_password


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "messenger.db"


def backup_database():
    """
    Створює резервну копію поточної бази даних.
    """

    if not DB_PATH.exists():
        return

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = BASE_DIR / (
        f"messenger_backup_{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path
    )

    print(
        f"Backup created: {backup_path.name}"
    )


def clear_database(connection):
    """
    Очищає демонстраційні таблиці.
    """

    connection.execute(
        "DELETE FROM AuditLog"
    )

    connection.execute(
        "DELETE FROM Sessions"
    )

    connection.execute(
        "DELETE FROM Messages"
    )

    connection.execute(
        "DELETE FROM ChatMembers"
    )

    connection.execute(
        "DELETE FROM Chats"
    )

    connection.execute(
        "DELETE FROM Users"
    )

    connection.execute(
        """
        DELETE FROM sqlite_sequence
        WHERE name IN (
            'Users',
            'Chats',
            'Messages',
            'Sessions',
            'AuditLog'
        )
        """
    )


def get_datetime(connection, modifier):
    parts = modifier.split()

    sqlite_modifiers = []

    index = 0

    while index < len(parts):
        value = parts[index]
        unit = parts[index + 1]

        if index == 0 and value.startswith("-"):
            sign = "-"
            number = value[1:]
        elif index == 0 and value.startswith("+"):
            sign = "+"
            number = value[1:]
        else:
            sign = "-"
            number = value

        sqlite_modifiers.append(
            f"{sign}{number} {unit}"
        )

        index += 2

    placeholders = ", ".join(
        ["?"] * len(sqlite_modifiers)
    )

    query = (
        f"SELECT datetime('now', {placeholders})"
    )

    return connection.execute(
        query,
        sqlite_modifiers
    ).fetchone()[0]


def insert_user(
    connection,
    username,
    display_name,
    password,
    role="USER"
):
    password_hash, password_salt = (
        hash_password(password)
    )

    cursor = connection.execute(
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
        VALUES (?, ?, ?, ?, ?, 0, 0)
        """,
        (
            username,
            display_name,
            password_hash,
            password_salt,
            role
        )
    )

    return cursor.lastrowid


def create_chat(
    connection,
    first_user_id,
    second_user_id,
    created_modifier
):
    created_at = get_datetime(
        connection,
        created_modifier
    )

    cursor = connection.execute(
        """
        INSERT INTO Chats (
            CreatedAt
        )
        VALUES (?)
        """,
        (created_at,)
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


def insert_message(
    connection,
    chat_id,
    sender_id,
    text,
    sent_modifier,
    read_modifier=None
):
    sent_at = get_datetime(
        connection,
        sent_modifier
    )

    if read_modifier is None:
        read_at = None
    else:
        read_at = get_datetime(
            connection,
            read_modifier
        )

    connection.execute(
        """
        INSERT INTO Messages (
            ChatId,
            SenderId,
            Text,
            SentAt,
            ReadAt,
            IsDeleted
        )
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (
            chat_id,
            sender_id,
            text,
            sent_at,
            read_at
        )
    )


def insert_audit(
    connection,
    user_id,
    event_type,
    description,
    created_modifier
):
    created_at = get_datetime(
        connection,
        created_modifier
    )

    connection.execute(
        """
        INSERT INTO AuditLog (
            UserId,
            EventType,
            Description,
            CreatedAt
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            event_type,
            description,
            created_at
        )
    )


def populate_database():
    backup_database()

    with get_connection() as connection:
        clear_database(connection)

        # ==========================================
        # USERS
        # ==========================================

        snizhana_id = insert_user(
            connection,
            "snizhana",
            "Сніжана Колодій",
            "123456"
        )

        olena_id = insert_user(
            connection,
            "olena",
            "Олена Коваль",
            "123456"
        )

        maksym_id = insert_user(
            connection,
            "maksym",
            "Максим Бондар",
            "123456"
        )

        andrii_id = insert_user(
            connection,
            "andrii",
            "Андрій Мельник",
            "123456"
        )

        kateryna_id = insert_user(
            connection,
            "kateryna",
            "Катерина Савчук",
            "123456"
        )

        bohdan_id = insert_user(
            connection,
            "bohdan",
            "Богдан Ткачук",
            "123456"
        )

        admin_id = insert_user(
            connection,
            "admin1",
            "Адміністратор",
            "admin123",
            role="ADMIN"
        )

        # ==========================================
        # CHAT 1
        # Сніжана <-> Олена
        # Є непрочитане повідомлення
        # ==========================================

        chat_snizhana_olena = create_chat(
            connection,
            snizhana_id,
            olena_id,
            "-2 days"
        )

        insert_message(
            connection,
            chat_snizhana_olena,
            snizhana_id,
            "Привіт! Ти вже зробила третю лабораторну?",
            "-2 hours",
            "-1 hour 55 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_olena,
            olena_id,
            "Привіт 😊 Майже, ще доробляю клієнт.",
            "-1 hour 50 minutes",
            "-1 hour 45 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_olena,
            snizhana_id,
            "Я теж. Потім можемо звірити результати.",
            "-1 hour 40 minutes",
            "-1 hour 35 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_olena,
            olena_id,
            "Домовились. Напишу ввечері.",
            "-25 minutes",
            None
        )

        # ==========================================
        # CHAT 2
        # Сніжана <-> Максим
        # Усі повідомлення прочитані
        # ==========================================

        chat_snizhana_maksym = create_chat(
            connection,
            snizhana_id,
            maksym_id,
            "-4 days"
        )

        insert_message(
            connection,
            chat_snizhana_maksym,
            maksym_id,
            "Привіт, ти завтра будеш на парі?",
            "-1 day",
            "-23 hours 55 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_maksym,
            snizhana_id,
            "Так, планую бути.",
            "-23 hours 50 minutes",
            "-23 hours 45 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_maksym,
            maksym_id,
            "Супер, тоді до завтра!",
            "-23 hours 40 minutes",
            "-23 hours 35 minutes"
        )

        # ==========================================
        # CHAT 3
        # Сніжана <-> Андрій
        # Порожній чат
        # ==========================================

        create_chat(
            connection,
            snizhana_id,
            andrii_id,
            "-7 days"
        )

        # ==========================================
        # CHAT 4
        # Олена <-> Катерина
        # ==========================================

        chat_olena_kateryna = create_chat(
            connection,
            olena_id,
            kateryna_id,
            "-3 days"
        )

        insert_message(
            connection,
            chat_olena_kateryna,
            kateryna_id,
            "Ти бачила нове завдання?",
            "-3 hours",
            "-2 hours 58 minutes"
        )

        insert_message(
            connection,
            chat_olena_kateryna,
            olena_id,
            "Так, щойно відкрила. Треба буде розібратись.",
            "-2 hours 55 minutes",
            "-2 hours 50 minutes"
        )

        # ==========================================
        # CHAT 5
        # Максим <-> Богдан
        # Порожній чат
        # ==========================================

        create_chat(
            connection,
            maksym_id,
            bohdan_id,
            "-6 days"
        )

        # ==========================================
        # CHAT 6
        # Сніжана <-> Катерина
        # Стара переписка
        # ==========================================

        chat_snizhana_kateryna = create_chat(
            connection,
            snizhana_id,
            kateryna_id,
            "-10 days"
        )

        insert_message(
            connection,
            chat_snizhana_kateryna,
            snizhana_id,
            "Привіт! Можеш скинути конспект з останньої пари?",
            "-4 days",
            "-3 days 23 hours 55 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_kateryna,
            kateryna_id,
            "Так, зараз знайду.",
            "-3 days 23 hours 50 minutes",
            "-3 days 23 hours 45 minutes"
        )

        insert_message(
            connection,
            chat_snizhana_kateryna,
            kateryna_id,
            "Скинула в групу 🙂",
            "-3 days 23 hours 40 minutes",
            "-3 days 23 hours 35 minutes"
        )

        # ==========================================
        # AUDIT LOG
        # ==========================================

        insert_audit(
            connection,
            snizhana_id,
            "LOGIN",
            "Користувач 'snizhana' успішно увійшов до системи.",
            "-1 hour"
        )

        insert_audit(
            connection,
            olena_id,
            "LOGIN",
            "Користувач 'olena' успішно увійшов до системи.",
            "-45 minutes"
        )

        insert_audit(
            connection,
            maksym_id,
            "LOGIN_FAILED",
            "Невдала спроба входу користувача 'maksym': неправильний пароль.",
            "-30 minutes"
        )

        insert_audit(
            connection,
            admin_id,
            "USER_BLOCKED",
            "Адміністратор заблокував користувача 'bohdan'.",
            "-20 minutes"
        )

        insert_audit(
            connection,
            admin_id,
            "USER_UNBLOCKED",
            "Адміністратор розблокував користувача 'bohdan'.",
            "-10 minutes"
        )

        insert_audit(
            connection,
            olena_id,
            "LOGOUT",
            "Користувач 'olena' вийшов із системи.",
            "-5 minutes"
        )

    print()
    print("====================================")
    print("DATABASE POPULATED SUCCESSFULLY")
    print("====================================")
    print()

    print("Users: 7")
    print("Chats: 6")
    print("Messages: 12")

    print()
    print("Main account:")
    print("Username: snizhana")
    print("Password: 123456")

    print()
    print("Other users:")
    print("olena / 123456")
    print("maksym / 123456")
    print("andrii / 123456")
    print("kateryna / 123456")
    print("bohdan / 123456")

    print()
    print("Administrator:")
    print("Username: admin1")
    print("Password: admin123")


if __name__ == "__main__":
    populate_database()