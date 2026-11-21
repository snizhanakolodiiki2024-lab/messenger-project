import socket
import json
import time


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
    test_username = (
        f"delete_test_{int(time.time())}"
    )

    test_password = "123456"

    # ==========================================
    # CREATE TEMPORARY USER
    # ==========================================

    test_socket = connect_to_server()

    send_json(
        test_socket,
        {
            "type": "REGISTER",
            "username": test_username,
            "display_name": "Delete Test User",
            "password": test_password
        }
    )

    register_response = receive_json(
        test_socket
    )

    print(
        "\nTEST USER REGISTER:"
    )

    print(
        register_response
    )

    if (
        register_response is None
        or register_response.get("status")
        != "OK"
    ):
        test_socket.close()
        return

    # ==========================================
    # LOGIN AS TEMPORARY USER
    # ==========================================

    test_login = login(
        test_socket,
        test_username,
        test_password
    )

    print(
        "\nTEST USER LOGIN:"
    )

    print(
        test_login
    )

    if test_login.get("status") != "OK":
        test_socket.close()
        return

    test_user_id = test_login["user_id"]
    test_token = test_login["token"]

    print(
        "\nTEST USER ID:"
    )

    print(
        test_user_id
    )

    # ==========================================
    # ADMIN LOGIN
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
        test_socket.close()
        return

    admin_token = admin_login["token"]

    # ==========================================
    # DELETE TEMPORARY USER
    # ==========================================

    send_json(
        admin_socket,
        {
            "type": "DELETE_USER",
            "token": admin_token,
            "user_id": test_user_id
        }
    )

    delete_response = receive_json(
        admin_socket
    )

    print(
        "\nDELETE USER RESPONSE:"
    )

    print(
        delete_response
    )

    # ==========================================
    # OLD TOKEN MUST NO LONGER WORK
    # ==========================================

    send_json(
        test_socket,
        {
            "type": "GET_CHATS",
            "token": test_token
        }
    )

    old_session_response = receive_json(
        test_socket
    )

    print(
        "\nOLD SESSION AFTER DELETE:"
    )

    print(
        old_session_response
    )

    test_socket.close()

    # ==========================================
    # TRY LOGIN AGAIN
    # ==========================================

    second_test_socket = connect_to_server()

    login_after_delete = login(
        second_test_socket,
        test_username,
        test_password
    )

    print(
        "\nLOGIN AFTER DELETE:"
    )

    print(
        login_after_delete
    )

    second_test_socket.close()

    # ==========================================
    # ADMIN GET USERS
    # ==========================================

    send_json(
        admin_socket,
        {
            "type": "GET_USERS",
            "token": admin_token
        }
    )

    users_response = receive_json(
        admin_socket
    )

    print(
        "\nUSERS AFTER DELETE:"
    )

    print(
        users_response
    )

    # ==========================================
    # ADMIN LOGOUT
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