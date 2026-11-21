import socket
import json


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
            message, _ = buffer.split("\n", 1)

            return json.loads(message)


def connect_to_server():
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client_socket.connect((HOST, PORT))

    return client_socket


def login(client_socket, username, password):
    send_json(
        client_socket,
        {
            "type": "LOGIN",
            "username": username,
            "password": password
        }
    )

    return receive_json(client_socket)


def logout(client_socket, token):
    send_json(
        client_socket,
        {
            "type": "LOGOUT",
            "token": token
        }
    )

    return receive_json(client_socket)


def main():
    # ==================================================
    # USER2 SENDS NEW MESSAGE TO USER1
    # ==================================================

    user2_socket = connect_to_server()

    print("USER2 CONNECTED")

    user2_login = login(
        user2_socket,
        "user2",
        "123456"
    )

    print("\nUSER2 LOGIN:")
    print(user2_login)

    if user2_login.get("status") != "OK":
        user2_socket.close()
        return

    user2_token = user2_login["token"]

    send_json(
        user2_socket,
        {
            "type": "SEND_MESSAGE",
            "token": user2_token,
            "recipient_id": 1,
            "text": "Нове повідомлення перед очищенням."
        }
    )

    send_response = receive_json(user2_socket)

    print("\nSEND MESSAGE:")
    print(send_response)

    if send_response.get("status") != "OK":
        user2_socket.close()
        return

    chat_id = send_response["message_data"]["chat_id"]

    user2_logout = logout(
        user2_socket,
        user2_token
    )

    print("\nUSER2 LOGOUT:")
    print(user2_logout)

    user2_socket.close()

    # ==================================================
    # USER1 OPENS CHAT
    # ==================================================

    user1_socket = connect_to_server()

    print("\nUSER1 CONNECTED")

    user1_login = login(
        user1_socket,
        "user1",
        "123456"
    )

    print("\nUSER1 LOGIN:")
    print(user1_login)

    if user1_login.get("status") != "OK":
        user1_socket.close()
        return

    user1_token = user1_login["token"]

    # HISTORY BEFORE CLEAR
    send_json(
        user1_socket,
        {
            "type": "GET_HISTORY",
            "token": user1_token,
            "chat_id": chat_id
        }
    )

    history_before = receive_json(user1_socket)

    print("\nUSER1 HISTORY BEFORE CLEAR:")
    print(history_before)

    # CLEAR CHAT
    send_json(
        user1_socket,
        {
            "type": "CLEAR_CHAT",
            "token": user1_token,
            "chat_id": chat_id
        }
    )

    clear_response = receive_json(user1_socket)

    print("\nCLEAR CHAT RESPONSE:")
    print(clear_response)

    # HISTORY AFTER CLEAR
    send_json(
        user1_socket,
        {
            "type": "GET_HISTORY",
            "token": user1_token,
            "chat_id": chat_id
        }
    )

    history_after = receive_json(user1_socket)

    print("\nUSER1 HISTORY AFTER CLEAR:")
    print(history_after)

    user1_logout = logout(
        user1_socket,
        user1_token
    )

    print("\nUSER1 LOGOUT:")
    print(user1_logout)

    user1_socket.close()

    # ==================================================
    # USER2 CHECKS THAT HIS HISTORY STILL EXISTS
    # ==================================================

    user2_socket = connect_to_server()

    user2_login = login(
        user2_socket,
        "user2",
        "123456"
    )

    print("\nUSER2 SECOND LOGIN:")
    print(user2_login)

    if user2_login.get("status") != "OK":
        user2_socket.close()
        return

    user2_token = user2_login["token"]

    send_json(
        user2_socket,
        {
            "type": "GET_HISTORY",
            "token": user2_token,
            "chat_id": chat_id
        }
    )

    user2_history = receive_json(user2_socket)

    print("\nUSER2 HISTORY AFTER USER1 CLEARED CHAT:")
    print(user2_history)

    user2_logout = logout(
        user2_socket,
        user2_token
    )

    print("\nUSER2 FINAL LOGOUT:")
    print(user2_logout)

    user2_socket.close()


if __name__ == "__main__":
    main()