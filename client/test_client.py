import socket
import json


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
        data = client_socket.recv(
            4096
        )

        if not data:
            return None

        buffer += data.decode(
            "utf-8"
        )

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
    print(
        "======================================"
    )

    print(
        "TEST 1: REAL-TIME MESSAGE DELIVERY"
    )

    print(
        "======================================"
    )

    # ==================================================
    # USER1 ONLINE
    # ==================================================

    user1_socket = connect_to_server()

    user1_login = login(
        user1_socket,
        "user1",
        "123456"
    )

    print(
        "\nUSER1 LOGIN:"
    )

    print(
        user1_login
    )

    if user1_login.get(
        "status"
    ) != "OK":
        user1_socket.close()
        return

    user1_token = user1_login[
        "token"
    ]

    # ==================================================
    # USER2 ONLINE
    # ==================================================

    user2_socket = connect_to_server()

    user2_login = login(
        user2_socket,
        "user2",
        "123456"
    )

    print(
        "\nUSER2 LOGIN:"
    )

    print(
        user2_login
    )

    if user2_login.get(
        "status"
    ) != "OK":
        user1_socket.close()
        user2_socket.close()
        return

    user2_token = user2_login[
        "token"
    ]

    # ==================================================
    # USER2 SENDS MESSAGE TO ONLINE USER1
    # ==================================================

    send_json(
        user2_socket,
        {
            "type": "SEND_MESSAGE",
            "token": user2_token,
            "recipient_id": 1,
            "text": "Повідомлення в реальному часі."
        }
    )

    send_response = receive_json(
        user2_socket
    )

    print(
        "\nUSER2 SEND RESPONSE:"
    )

    print(
        send_response
    )

    if send_response.get(
        "status"
    ) != "OK":
        return

    chat_id = send_response[
        "message_data"
    ]["chat_id"]

    message_id = send_response[
        "message_data"
    ]["message_id"]

    print(
        "\nMESSAGE SAVED:"
    )

    print(
        "Message ID:",
        message_id
    )

    print(
        "Status: Надіслано (✓)"
    )

    # ==================================================
    # USER1 SHOULD RECEIVE PUSH AUTOMATICALLY
    # ==================================================

    pushed_message = receive_json(
        user1_socket
    )

    print(
        "\nUSER1 REAL-TIME EVENT:"
    )

    print(
        pushed_message
    )

    if (
        pushed_message is None
        or pushed_message.get(
            "type"
        ) != "NEW_MESSAGE"
    ):
        print(
            "ERROR: NEW_MESSAGE was not received."
        )

        return

    print(
        "\nREAL-TIME DELIVERY SUCCESS."
    )

    # ==================================================
    # USER1 MARKS CHAT AS READ
    # ==================================================

    send_json(
        user1_socket,
        {
            "type": "MARK_AS_READ",
            "token": user1_token,
            "chat_id": chat_id
        }
    )

    read_response = receive_json(
        user1_socket
    )

    print(
        "\nUSER1 MARK AS READ RESPONSE:"
    )

    print(
        read_response
    )

    # ==================================================
    # USER2 SHOULD RECEIVE MESSAGE_READ EVENT
    # ==================================================

    read_event = receive_json(
        user2_socket
    )

    print(
        "\nUSER2 REAL-TIME READ EVENT:"
    )

    print(
        read_event
    )

    if (
        read_event is not None
        and read_event.get(
            "type"
        ) == "MESSAGE_READ"
    ):
        print(
            "\nSTATUS: Прочитано (✓✓)"
        )

    else:
        print(
            "\nERROR: MESSAGE_READ was not received."
        )

        return

    # ==================================================
    # USER1 GOES OFFLINE
    # ==================================================

    print(
        "\nUSER1 LOGOUT:"
    )

    print(
        logout(
            user1_socket,
            user1_token
        )
    )

    user1_socket.close()

    print(
        "\n======================================"
    )

    print(
        "TEST 2: OFFLINE MESSAGE STORAGE"
    )

    print(
        "======================================"
    )

    # ==================================================
    # USER2 SENDS MESSAGE WHILE USER1 OFFLINE
    # ==================================================

    send_json(
        user2_socket,
        {
            "type": "SEND_MESSAGE",
            "token": user2_token,
            "recipient_id": 1,
            "text": "Повідомлення для офлайн користувача."
        }
    )

    offline_send_response = (
        receive_json(
            user2_socket
        )
    )

    print(
        "\nUSER2 SEND TO OFFLINE USER:"
    )

    print(
        offline_send_response
    )

    if offline_send_response.get(
        "status"
    ) != "OK":
        return

    offline_chat_id = (
        offline_send_response[
            "message_data"
        ]["chat_id"]
    )

    print(
        "\nMESSAGE STORED IN DATABASE."
    )

    print(
        "USER1 IS OFFLINE."
    )

    # ==================================================
    # USER2 LOGOUT
    # ==================================================

    print(
        "\nUSER2 LOGOUT:"
    )

    print(
        logout(
            user2_socket,
            user2_token
        )
    )

    user2_socket.close()

    # ==================================================
    # USER1 COMES ONLINE LATER
    # ==================================================

    user1_socket = connect_to_server()

    user1_login = login(
        user1_socket,
        "user1",
        "123456"
    )

    print(
        "\nUSER1 LOGIN AGAIN:"
    )

    print(
        user1_login
    )

    if user1_login.get(
        "status"
    ) != "OK":
        user1_socket.close()
        return

    user1_token = user1_login[
        "token"
    ]

    # ==================================================
    # GET HISTORY
    # ==================================================

    send_json(
        user1_socket,
        {
            "type": "GET_HISTORY",
            "token": user1_token,
            "chat_id": offline_chat_id
        }
    )

    history_response = receive_json(
        user1_socket
    )

    print(
        "\nUSER1 HISTORY AFTER COMING ONLINE:"
    )

    print(
        history_response
    )

    offline_message_found = False

    if history_response.get(
        "status"
    ) == "OK":

        for message in (
            history_response.get(
                "messages",
                []
            )
        ):
            if (
                message["text"]
                == "Повідомлення для офлайн користувача."
            ):
                offline_message_found = True

                print(
                    "\nOFFLINE MESSAGE FOUND:"
                )

                print(
                    message
                )

                break

    if offline_message_found:
        print(
            "\nOFFLINE STORAGE TEST SUCCESS."
        )

    else:
        print(
            "\nERROR: Offline message not found."
        )

    # ==================================================
    # FINAL LOGOUT
    # ==================================================

    print(
        "\nUSER1 FINAL LOGOUT:"
    )

    print(
        logout(
            user1_socket,
            user1_token
        )
    )

    user1_socket.close()

    # ==================================================
    # RESULT
    # ==================================================

    print(
        "\n======================================"
    )

    print(
        "REAL-TIME TEST COMPLETED"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()