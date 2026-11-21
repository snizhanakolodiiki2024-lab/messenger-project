import socket
import json
import time


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


def receive_json(client_socket):
    buffer = ""

    while True:
        data = client_socket.recv(4096)

        if not data:
            return None

        buffer += data.decode("utf-8")

        if "\n" in buffer:
            message, _ = buffer.split(
                "\n",
                1
            )

            return json.loads(
                message
            )


def connect_to_server():
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client_socket.connect(
        (HOST, PORT)
    )

    return client_socket


def login(
    client_socket,
    username,
    password
):
    send_json(
        client_socket,
        {
            "type": "LOGIN",
            "username": username,
            "password": password
        }
    )

    return receive_json(
        client_socket
    )


def logout(
    client_socket,
    token
):
    send_json(
        client_socket,
        {
            "type": "LOGOUT",
            "token": token
        }
    )

    return receive_json(
        client_socket
    )


def main():
    # ==========================================
    # 1. FAILED LOGIN
    # ==========================================

    failed_socket = connect_to_server()

    failed_login = login(
        failed_socket,
        "user2",
        "wrong_password"
    )

    print(
        "\nFAILED LOGIN:"
    )

    print(
        failed_login
    )

    failed_socket.close()

    # ==========================================
    # 2. NORMAL USER LOGIN
    # ==========================================

    user_socket = connect_to_server()

    user_login = login(
        user_socket,
        "user2",
        "123456"
    )

    print(
        "\nUSER2 LOGIN:"
    )

    print(
        user_login
    )

    if user_login.get("status") != "OK":
        user_socket.close()
        return

    user_token = user_login["token"]

    # ==========================================
    # 3. USER TRIES GET_AUDIT_LOG
    # ==========================================

    send_json(
        user_socket,
        {
            "type": "GET_AUDIT_LOG",
            "token": user_token
        }
    )

    user_audit_response = receive_json(
        user_socket
    )

    print(
        "\nGET_AUDIT_LOG AS USER:"
    )

    print(
        user_audit_response
    )

    # ==========================================
    # 4. USER LOGOUT
    # ==========================================

    print(
        "\nUSER2 LOGOUT:"
    )

    print(
        logout(
            user_socket,
            user_token
        )
    )

    user_socket.close()

    # ==========================================
    # 5. ADMIN LOGIN
    # ==========================================

    admin_socket = connect_to_server()

    admin_login = login(
        admin_socket,
        "admin1",
        "admin123"
    )

    print(
        "\nADMIN LOGIN:"
    )

    print(
        admin_login
    )

    if admin_login.get("status") != "OK":
        admin_socket.close()
        return

    admin_token = admin_login["token"]

    # ==========================================
    # 6. BLOCK USER2
    # ==========================================

    send_json(
        admin_socket,
        {
            "type": "BLOCK_USER",
            "token": admin_token,
            "user_id": 2
        }
    )

    block_response = receive_json(
        admin_socket
    )

    print(
        "\nBLOCK USER2:"
    )

    print(
        block_response
    )

    # ==========================================
    # 7. LOGIN WHILE BLOCKED
    # ==========================================

    blocked_socket = connect_to_server()

    blocked_login = login(
        blocked_socket,
        "user2",
        "123456"
    )

    print(
        "\nUSER2 LOGIN WHILE BLOCKED:"
    )

    print(
        blocked_login
    )

    blocked_socket.close()

    # ==========================================
    # 8. UNBLOCK USER2
    # ==========================================

    send_json(
        admin_socket,
        {
            "type": "UNBLOCK_USER",
            "token": admin_token,
            "user_id": 2
        }
    )

    unblock_response = receive_json(
        admin_socket
    )

    print(
        "\nUNBLOCK USER2:"
    )

    print(
        unblock_response
    )

    # ==========================================
    # 9. CREATE TEMP USER
    # ==========================================

    temporary_username = (
        f"audit_test_{int(time.time())}"
    )

    temporary_password = "123456"

    temporary_socket = connect_to_server()

    send_json(
        temporary_socket,
        {
            "type": "REGISTER",
            "username": temporary_username,
            "display_name": "Audit Test User",
            "password": temporary_password
        }
    )

    register_response = receive_json(
        temporary_socket
    )

    print(
        "\nTEMP USER REGISTER:"
    )

    print(
        register_response
    )

    if register_response.get("status") != "OK":
        temporary_socket.close()
        admin_socket.close()
        return

    # ==========================================
    # 10. TEMP USER LOGIN
    # ==========================================

    temporary_login = login(
        temporary_socket,
        temporary_username,
        temporary_password
    )

    print(
        "\nTEMP USER LOGIN:"
    )

    print(
        temporary_login
    )

    if temporary_login.get("status") != "OK":
        temporary_socket.close()
        admin_socket.close()
        return

    temporary_user_id = (
        temporary_login["user_id"]
    )

    temporary_token = (
        temporary_login["token"]
    )

    # ==========================================
    # 11. ADMIN DELETES TEMP USER
    # ==========================================

    send_json(
        admin_socket,
        {
            "type": "DELETE_USER",
            "token": admin_token,
            "user_id": temporary_user_id
        }
    )

    delete_response = receive_json(
        admin_socket
    )

    print(
        "\nDELETE TEMP USER:"
    )

    print(
        delete_response
    )

    # ==========================================
    # 12. OLD TEMP SESSION MUST FAIL
    # ==========================================

    send_json(
        temporary_socket,
        {
            "type": "GET_CHATS",
            "token": temporary_token
        }
    )

    old_session_response = receive_json(
        temporary_socket
    )

    print(
        "\nTEMP USER OLD SESSION:"
    )

    print(
        old_session_response
    )

    temporary_socket.close()

    # ==========================================
    # 13. ADMIN GETS AUDIT LOG
    # ==========================================

    send_json(
        admin_socket,
        {
            "type": "GET_AUDIT_LOG",
            "token": admin_token,
            "limit": 50
        }
    )

    audit_response = receive_json(
        admin_socket
    )

    print(
        "\nAUDIT LOG:"
    )

    if audit_response.get("status") == "OK":
        logs = audit_response.get(
            "logs",
            []
        )

        for log in logs:
            print(
                "\n--------------------"
            )

            print(
                "Log ID:",
                log["log_id"]
            )

            print(
                "User ID:",
                log["user_id"]
            )

            print(
                "Username:",
                log["username"]
            )

            print(
                "Event:",
                log["event_type"]
            )

            print(
                "Description:",
                log["description"]
            )

            print(
                "Created At:",
                log["created_at"]
            )

    else:
        print(
            audit_response
        )

    # ==========================================
    # 14. ADMIN LOGOUT
    # ==========================================

    print(
        "\nADMIN LOGOUT:"
    )

    print(
        logout(
            admin_socket,
            admin_token
        )
    )

    admin_socket.close()


if __name__ == "__main__":
    main()