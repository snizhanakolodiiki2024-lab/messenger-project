from network_client import NetworkClient


def main():
    client = NetworkClient()

    print("CONNECT:")
    print(client.connect())

    print("\nLOGIN:")
    login_response = client.login(
        "snizhana",
        "123456"
    )

    print(login_response)

    if login_response.get("status") != "OK":
        client.disconnect()
        return

    print("\nUSER DATA:")
    print("ID:", client.user_id)
    print("Username:", client.username)
    print("Display name:", client.display_name)
    print("Role:", client.role)

    print("\nCHATS:")
    chats_response = client.get_chats()
    print(chats_response)

    print("\nLOGOUT:")
    logout_response = client.logout()
    print(logout_response)

    client.disconnect()


if __name__ == "__main__":
    main()