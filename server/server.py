import socket
import threading
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))


from database.db import (
    create_user,
    authenticate_user,
    close_session,
    get_session,
    get_user_by_id,
    search_users,
    get_user_chats,
    save_message,
    get_chat_history,
    mark_messages_as_read,
    delete_message,
    clear_chat,
    get_all_users,
    block_user,
    unblock_user,
    delete_user,
    get_audit_log
)


HOST = "127.0.0.1"
PORT = 5000


# =========================================================
# ONLINE CLIENTS
# =========================================================

active_clients = {}
active_clients_lock = threading.Lock()

socket_send_locks = {}
socket_send_locks_lock = threading.Lock()


def register_socket(client_socket):
    with socket_send_locks_lock:
        socket_send_locks[client_socket] = threading.Lock()


def unregister_socket(client_socket):
    with socket_send_locks_lock:
        socket_send_locks.pop(
            client_socket,
            None
        )


def get_socket_lock(client_socket):
    with socket_send_locks_lock:
        lock = socket_send_locks.get(
            client_socket
        )

        if lock is None:
            lock = threading.Lock()

            socket_send_locks[
                client_socket
            ] = lock

        return lock


def register_online_user(
    user_id,
    client_socket
):
    with active_clients_lock:
        active_clients[user_id] = (
            client_socket
        )

    print(
        f"User {user_id} is ONLINE."
    )


def unregister_online_user(
    user_id,
    client_socket=None
):
    if user_id is None:
        return

    with active_clients_lock:
        current_socket = (
            active_clients.get(user_id)
        )

        if current_socket is None:
            return

        if (
            client_socket is None
            or current_socket
            is client_socket
        ):
            active_clients.pop(
                user_id,
                None
            )

            print(
                f"User {user_id} is OFFLINE."
            )


def get_online_socket(user_id):
    with active_clients_lock:
        return active_clients.get(
            user_id
        )


# =========================================================
# NETWORK HELPERS
# =========================================================

def send_json(
    client_socket,
    data
):
    message = json.dumps(
        data,
        ensure_ascii=False
    ) + "\n"

    encoded_message = (
        message.encode("utf-8")
    )

    lock = get_socket_lock(
        client_socket
    )

    with lock:
        client_socket.sendall(
            encoded_message
        )


def push_to_user(
    user_id,
    data
):
    client_socket = get_online_socket(
        user_id
    )

    if client_socket is None:
        return False

    try:
        send_json(
            client_socket,
            data
        )

        return True

    except (
        OSError,
        ConnectionError
    ):
        unregister_online_user(
            user_id,
            client_socket
        )

        return False


def terminate_online_user(
    user_id,
    reason
):
    client_socket = get_online_socket(
        user_id
    )

    if client_socket is None:
        return

    try:
        send_json(
            client_socket,
            {
                "type": "SESSION_TERMINATED",
                "reason": reason
            }
        )

    except (
        OSError,
        ConnectionError
    ):
        pass

    unregister_online_user(
        user_id,
        client_socket
    )


# =========================================================
# AUTH HELPERS
# =========================================================

def get_authenticated_user(token):
    session = get_session(token)

    if session is None:
        return None

    user = get_user_by_id(
        session["UserId"]
    )

    if user is None:
        return None

    if user["IsDeleted"] == 1:
        return None

    if user["IsBlocked"] == 1:
        return None

    return user


def get_admin_user(token):
    user = get_authenticated_user(
        token
    )

    if user is None:
        return (
            None,
            "Недійсна або завершена сесія."
        )

    if user["Role"] != "ADMIN":
        return (
            None,
            "Недостатньо прав доступу."
        )

    return user, None


def send_result(
    client_socket,
    result
):
    send_json(
        client_socket,
        {
            "status": (
                "OK"
                if result["success"]
                else "ERROR"
            ),
            **{
                key: value
                for key, value
                in result.items()
                if key != "success"
            }
        }
    )


# =========================================================
# CLIENT HANDLER
# =========================================================

def handle_client(
    client_socket,
    client_address
):
    print(
        f"Client connected: {client_address}"
    )

    register_socket(
        client_socket
    )

    buffer = ""

    connected_user_id = None

    try:
        while True:
            data = client_socket.recv(
                4096
            )

            if not data:
                break

            buffer += data.decode(
                "utf-8"
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

                    print(
                        f"Request from {client_address}:",
                        request
                    )

                    request_type = (
                        request.get("type")
                    )

                    # =====================================
                    # PING
                    # =====================================

                    if request_type == "PING":
                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "message": "PONG"
                            }
                        )

                    # =====================================
                    # REGISTER
                    # =====================================

                    elif request_type == "REGISTER":
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

                        send_result(
                            client_socket,
                            result
                        )

                    # =====================================
                    # LOGIN
                    # =====================================

                    elif request_type == "LOGIN":
                        result = authenticate_user(
                            username=request.get(
                                "username"
                            ),
                            password=request.get(
                                "password"
                            )
                        )

                        if result["success"]:
                            if (
                                connected_user_id
                                is not None
                            ):
                                unregister_online_user(
                                    connected_user_id,
                                    client_socket
                                )

                            connected_user_id = (
                                result["user_id"]
                            )

                            register_online_user(
                                connected_user_id,
                                client_socket
                            )

                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": result[
                                        "message"
                                    ],
                                    "user_id": result[
                                        "user_id"
                                    ],
                                    "username": result[
                                        "username"
                                    ],
                                    "display_name": result[
                                        "display_name"
                                    ],
                                    "role": result[
                                        "role"
                                    ],
                                    "token": result[
                                        "token"
                                    ]
                                }
                            )

                        else:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": result[
                                        "message"
                                    ]
                                }
                            )

                    # =====================================
                    # LOGOUT
                    # =====================================

                    elif request_type == "LOGOUT":
                        token = request.get(
                            "token"
                        )

                        session = get_session(
                            token
                        )

                        logout_user_id = (
                            session["UserId"]
                            if session
                            is not None
                            else None
                        )

                        if close_session(token):
                            unregister_online_user(
                                logout_user_id,
                                client_socket
                            )

                            if (
                                connected_user_id
                                == logout_user_id
                            ):
                                connected_user_id = (
                                    None
                                )

                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": "Сесію успішно завершено."
                                }
                            )

                        else:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або вже завершена сесія."
                                }
                            )

                    # =====================================
                    # SEARCH USER
                    # =====================================

                    elif request_type == "SEARCH_USER":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        users = search_users(
                            request.get(
                                "query",
                                ""
                            ),
                            user["UserId"]
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

                    elif request_type == "GET_CHATS":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "chats": get_user_chats(
                                    user[
                                        "UserId"
                                    ]
                                )
                            }
                        )

                    # =====================================
                    # SEND MESSAGE
                    # =====================================

                    elif request_type == "SEND_MESSAGE":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        recipient_id = (
                            request.get(
                                "recipient_id"
                            )
                        )

                        result = save_message(
                            sender_id=user[
                                "UserId"
                            ],
                            recipient_id=(
                                recipient_id
                            ),
                            text=request.get(
                                "text"
                            )
                        )

                        # Спочатку відправник отримує
                        # підтвердження збереження.
                        send_result(
                            client_socket,
                            result
                        )

                        # Якщо повідомлення успішно
                        # збережено — пробуємо
                        # передати отримувачу online.
                        if result["success"]:
                            try:
                                recipient_id = int(
                                    recipient_id
                                )
                            except (
                                TypeError,
                                ValueError
                            ):
                                recipient_id = None

                            if (
                                recipient_id
                                is not None
                            ):
                                delivered = (
                                    push_to_user(
                                        recipient_id,
                                        {
                                            "type": "NEW_MESSAGE",
                                            "message": result[
                                                "message_data"
                                            ]
                                        }
                                    )
                                )

                                if delivered:
                                    print(
                                        "Message pushed "
                                        f"to online user "
                                        f"{recipient_id}."
                                    )

                                else:
                                    print(
                                        "Recipient "
                                        f"{recipient_id} "
                                        "is offline. "
                                        "Message remains "
                                        "stored in database."
                                    )

                    # =====================================
                    # GET HISTORY
                    # =====================================

                    elif request_type == "GET_HISTORY":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = (
                            get_chat_history(
                                user["UserId"],
                                request.get(
                                    "chat_id"
                                )
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    # =====================================
                    # MARK AS READ
                    # =====================================

                    elif request_type == "MARK_AS_READ":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        chat_id = request.get(
                            "chat_id"
                        )

                        result = (
                            mark_messages_as_read(
                                user["UserId"],
                                chat_id
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                        # Якщо щось реально
                        # було прочитано —
                        # повідомляємо відправників.
                        if (
                            result["success"]
                            and result[
                                "updated_count"
                            ] > 0
                        ):
                            for sender_id in (
                                result[
                                    "sender_ids"
                                ]
                            ):
                                push_to_user(
                                    sender_id,
                                    {
                                        "type": "MESSAGE_READ",
                                        "chat_id": int(
                                            chat_id
                                        ),
                                        "message_ids": result[
                                            "message_ids"
                                        ],
                                        "read_at": result[
                                            "read_at"
                                        ]
                                    }
                                )

                    # =====================================
                    # DELETE MESSAGE
                    # =====================================

                    elif request_type == "DELETE_MESSAGE":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = delete_message(
                            user["UserId"],
                            request.get(
                                "message_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    # =====================================
                    # CLEAR CHAT
                    # =====================================

                    elif request_type == "CLEAR_CHAT":
                        user = (
                            get_authenticated_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if user is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = clear_chat(
                            user["UserId"],
                            request.get(
                                "chat_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    # =====================================
                    # GET USERS
                    # =====================================

                    elif request_type == "GET_USERS":
                        admin, error = (
                            get_admin_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if error is not None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": error
                                }
                            )
                            continue

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

                    elif request_type == "BLOCK_USER":
                        admin, error = (
                            get_admin_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if error is not None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": error
                                }
                            )
                            continue

                        target_user_id = (
                            request.get(
                                "user_id"
                            )
                        )

                        result = block_user(
                            admin_user_id=admin[
                                "UserId"
                            ],
                            target_user_id=(
                                target_user_id
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                        if result["success"]:
                            terminate_online_user(
                                result["user_id"],
                                "Ваш обліковий запис заблоковано адміністратором."
                            )

                    # =====================================
                    # UNBLOCK USER
                    # =====================================

                    elif request_type == "UNBLOCK_USER":
                        admin, error = (
                            get_admin_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if error is not None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": error
                                }
                            )
                            continue

                        result = unblock_user(
                            admin_user_id=admin[
                                "UserId"
                            ],
                            target_user_id=request.get(
                                "user_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    # =====================================
                    # DELETE USER
                    # =====================================

                    elif request_type == "DELETE_USER":
                        admin, error = (
                            get_admin_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if error is not None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": error
                                }
                            )
                            continue

                        result = delete_user(
                            admin_user_id=admin[
                                "UserId"
                            ],
                            target_user_id=request.get(
                                "user_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                        if result["success"]:
                            terminate_online_user(
                                result["user_id"],
                                "Ваш обліковий запис видалено адміністратором."
                            )

                    # =====================================
                    # GET AUDIT LOG
                    # =====================================

                    elif request_type == "GET_AUDIT_LOG":
                        admin, error = (
                            get_admin_user(
                                request.get(
                                    "token"
                                )
                            )
                        )

                        if error is not None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": error
                                }
                            )
                            continue

                        logs = get_audit_log(
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
                    # UNKNOWN
                    # =====================================

                    else:
                        send_json(
                            client_socket,
                            {
                                "status": "ERROR",
                                "message": "Unknown command."
                            }
                        )

                except json.JSONDecodeError:
                    send_json(
                        client_socket,
                        {
                            "status": "ERROR",
                            "message": "Invalid JSON."
                        }
                    )

    except ConnectionResetError:
        print(
            f"Connection lost: "
            f"{client_address}"
        )

    except OSError:
        print(
            f"Socket closed: "
            f"{client_address}"
        )

    finally:
        unregister_online_user(
            connected_user_id,
            client_socket
        )

        unregister_socket(
            client_socket
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
        (HOST, PORT)
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

            client_thread = threading.Thread(
                target=handle_client,
                args=(
                    client_socket,
                    client_address
                ),
                daemon=True
            )

            client_thread.start()

    except KeyboardInterrupt:
        print(
            "\nServer stopped."
        )

    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()