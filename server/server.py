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
    search_users,
    get_user_chats,
    save_message,
    get_chat_history,
    mark_messages_as_read,
    delete_message,
    clear_chat
)


HOST = "127.0.0.1"
PORT = 5000


def send_json(client_socket, data):
    message = json.dumps(
        data,
        ensure_ascii=False
    ) + "\n"

    client_socket.sendall(
        message.encode("utf-8")
    )


def handle_client(client_socket, client_address):
    print(f"Client connected: {client_address}")

    buffer = ""

    try:
        while True:
            data = client_socket.recv(4096)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)

                if not message.strip():
                    continue

                try:
                    request = json.loads(message)

                    print(
                        f"Request from {client_address}:",
                        request
                    )

                    request_type = request.get("type")

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
                            username=request.get("username"),
                            display_name=request.get("display_name"),
                            password=request.get("password")
                        )

                        send_json(
                            client_socket,
                            {
                                "status": (
                                    "OK"
                                    if result["success"]
                                    else "ERROR"
                                ),
                                "message": result["message"]
                            }
                        )

                    elif request_type == "LOGIN":
                        result = authenticate_user(
                            username=request.get("username"),
                            password=request.get("password")
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
                        token = request.get("token")

                        if not token:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Token is required."
                                }
                            )
                            continue

                        logout_result = close_session(token)

                        if logout_result:
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
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        users = search_users(
                            search_text=request.get("query", ""),
                            current_user_id=session["UserId"]
                        )

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "users": users
                            }
                        )

                    elif request_type == "GET_CHATS":
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        chats = get_user_chats(
                            session["UserId"]
                        )

                        send_json(
                            client_socket,
                            {
                                "status": "OK",
                                "chats": chats
                            }
                        )

                    elif request_type == "SEND_MESSAGE":
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = save_message(
                            sender_id=session["UserId"],
                            recipient_id=request.get("recipient_id"),
                            text=request.get("text")
                        )

                        if result["success"]:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": result["message"],
                                    "message_data": result["message_data"]
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

                    elif request_type == "GET_HISTORY":
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = get_chat_history(
                            user_id=session["UserId"],
                            chat_id=request.get("chat_id")
                        )

                        if result["success"]:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "messages": result["messages"]
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

                    elif request_type == "MARK_AS_READ":
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = mark_messages_as_read(
                            user_id=session["UserId"],
                            chat_id=request.get("chat_id")
                        )

                        if result["success"]:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": result["message"],
                                    "updated_count": result["updated_count"],
                                    "read_at": result["read_at"]
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

                    elif request_type == "DELETE_MESSAGE":
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = delete_message(
                            user_id=session["UserId"],
                            message_id=request.get("message_id")
                        )

                        if result["success"]:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": result["message"],
                                    "message_id": result["message_id"],
                                    "chat_id": result["chat_id"]
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

                    elif request_type == "CLEAR_CHAT":
                        token = request.get("token")
                        session = get_session(token)

                        if session is None:
                            send_json(
                                client_socket,
                                {
                                    "status": "ERROR",
                                    "message": "Недійсна або завершена сесія."
                                }
                            )
                            continue

                        result = clear_chat(
                            user_id=session["UserId"],
                            chat_id=request.get("chat_id")
                        )

                        if result["success"]:
                            send_json(
                                client_socket,
                                {
                                    "status": "OK",
                                    "message": result["message"],
                                    "chat_id": result["chat_id"],
                                    "cleared_at": result["cleared_at"]
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
        print(f"Connection lost: {client_address}")

    finally:
        client_socket.close()
        print(f"Client disconnected: {client_address}")


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

    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Server started on {HOST}:{PORT}")
    print("Waiting for clients...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()

            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )

            client_thread.start()

    except KeyboardInterrupt:
        print("\nServer stopped.")

    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()