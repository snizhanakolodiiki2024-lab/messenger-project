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


def main():
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        client_socket.connect((HOST, PORT))

        print("Connected to server.")

        # LOGIN AS USER1
        send_json(
            client_socket,
            {
                "type": "LOGIN",
                "username": "user1",
                "password": "123456"
            }
        )

        login_response = receive_json(client_socket)

        print("\nLOGIN RESPONSE:")
        print(login_response)

        if (
            login_response is None
            or login_response.get("status") != "OK"
        ):
            print("Login failed.")
            return

        token = login_response["token"]

        # GET CHATS BEFORE READ
        send_json(
            client_socket,
            {
                "type": "GET_CHATS",
                "token": token
            }
        )

        chats_before = receive_json(client_socket)

        print("\nCHATS BEFORE READ:")
        print(chats_before)

        if (
            chats_before is None
            or chats_before.get("status") != "OK"
            or not chats_before.get("chats")
        ):
            print("No chats found.")
            return

        chat_id = chats_before["chats"][0]["chat_id"]

        # GET HISTORY BEFORE READ
        send_json(
            client_socket,
            {
                "type": "GET_HISTORY",
                "token": token,
                "chat_id": chat_id
            }
        )

        history_before = receive_json(client_socket)

        print("\nHISTORY BEFORE READ:")
        print(history_before)

        # MARK AS READ
        send_json(
            client_socket,
            {
                "type": "MARK_AS_READ",
                "token": token,
                "chat_id": chat_id
            }
        )

        read_response = receive_json(client_socket)

        print("\nMARK AS READ RESPONSE:")
        print(read_response)

        # GET HISTORY AFTER READ
        send_json(
            client_socket,
            {
                "type": "GET_HISTORY",
                "token": token,
                "chat_id": chat_id
            }
        )

        history_after = receive_json(client_socket)

        print("\nHISTORY AFTER READ:")
        print(history_after)

        # GET CHATS AFTER READ
        send_json(
            client_socket,
            {
                "type": "GET_CHATS",
                "token": token
            }
        )

        chats_after = receive_json(client_socket)

        print("\nCHATS AFTER READ:")
        print(chats_after)

        # LOGOUT
        send_json(
            client_socket,
            {
                "type": "LOGOUT",
                "token": token
            }
        )

        logout_response = receive_json(client_socket)

        print("\nLOGOUT RESPONSE:")
        print(logout_response)

    except ConnectionRefusedError:
        print("Could not connect to server.")

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()