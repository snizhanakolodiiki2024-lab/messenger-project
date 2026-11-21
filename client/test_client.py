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

        # 1. LOGIN
        send_json(
            client_socket,
            {
                "type": "LOGIN",
                "username": "user2",
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

        # 2. SEARCH USER
        send_json(
            client_socket,
            {
                "type": "SEARCH_USER",
                "token": token,
                "query": "user"
            }
        )

        search_response = receive_json(client_socket)

        print("\nSEARCH RESPONSE:")
        print(search_response)

        # 3. LOGOUT
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