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


def send_json(
    client_socket,
    data
):
    message = json.dumps(
        data,
        ensure_ascii=False
    ) + "\n"

    client_socket.sendall(
        message.encode("utf-8")
    )


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
    user = get_authenticated_user(token)

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


def handle_client(
    client_socket,
    client_address
):
    print(
        f"Client connected: {client_address}"
    )

    buffer = ""

    try:
        while True:
            data = client_socket.recv(4096)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split(
                    "\n",
                    1
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

                    request_type = request.get(
                        "type"
                    )

                    if request_type == "PING":
                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "message": "PONG"
                            }
                        )

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
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": result["message"],
                                    "user_id": result["user_id"],
                                    "username": result["username"],
                                    "display_name": result["display_name"],
                                    "role": result["role"],
                                    "token": result["token"]
                                }
                            )

                        else:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": result["message"]
                                }
                            )

                    elif request_type == "LOGOUT":
                        token = request.get(
                            "token"
                        )

                        if close_session(token):
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

                    elif request_type == "SEARCH_USER":
                        user = get_authenticated_user(
                            request.get("token")
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

                    elif request_type == "GET_CHATS":
                        user = get_authenticated_user(
                            request.get("token")
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
                                    user["UserId"]
                                )
                            }
                        )

                    elif request_type == "SEND_MESSAGE":
                        user = get_authenticated_user(
                            request.get("token")
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

                        result = save_message(
                            sender_id=user["UserId"],
                            recipient_id=request.get(
                                "recipient_id"
                            ),
                            text=request.get(
                                "text"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    elif request_type == "GET_HISTORY":
                        user = get_authenticated_user(
                            request.get("token")
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

                        result = get_chat_history(
                            user["UserId"],
                            request.get(
                                "chat_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    elif request_type == "MARK_AS_READ":
                        user = get_authenticated_user(
                            request.get("token")
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

                        result = mark_messages_as_read(
                            user["UserId"],
                            request.get(
                                "chat_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    elif request_type == "DELETE_MESSAGE":
                        user = get_authenticated_user(
                            request.get("token")
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

                    elif request_type == "CLEAR_CHAT":
                        user = get_authenticated_user(
                            request.get("token")
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

                    elif request_type == "GET_USERS":
                        admin, error = get_admin_user(
                            request.get("token")
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
                                "users": get_all_users()
                            }
                        )

                    elif request_type == "BLOCK_USER":
                        admin, error = get_admin_user(
                            request.get("token")
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

                        result = block_user(
                            admin_user_id=admin["UserId"],
                            target_user_id=request.get(
                                "user_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    elif request_type == "UNBLOCK_USER":
                        admin, error = get_admin_user(
                            request.get("token")
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
                            admin_user_id=admin["UserId"],
                            target_user_id=request.get(
                                "user_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    elif request_type == "DELETE_USER":
                        admin, error = get_admin_user(
                            request.get("token")
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
                            admin_user_id=admin["UserId"],
                            target_user_id=request.get(
                                "user_id"
                            )
                        )

                        send_result(
                            client_socket,
                            result
                        )

                    elif request_type == "GET_AUDIT_LOG":
                        admin, error = get_admin_user(
                            request.get("token")
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
            f"Connection lost: {client_address}"
        )

    finally:
        client_socket.close()

        print(
            f"Client disconnected: {client_address}"
        )


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
        f"Server started on {HOST}:{PORT}"
    )

    print(
        "Waiting for clients..."
    )

    try:
        while True:
            client_socket, client_address = (
                server_socket.accept()
            )

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