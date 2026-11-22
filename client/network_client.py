# -*- coding: utf-8 -*-

import socket
import json
import threading


class NetworkClient:
    def __init__(
        self,
        host="127.0.0.1",
        port=5000
    ):
        self._host = host
        self._port = port

        self._socket = None
        self._connected = False
        self._running = False

        self._token = None
        self._user_id = None
        self._username = None
        self._display_name = None
        self._role = None

        self._receiver_thread = None
        self._buffer = ""

        self._response_condition = (
            threading.Condition()
        )

        self._pending_response = None

        self._event_handlers = {}

        self._send_lock = threading.Lock()
        self._request_lock = threading.Lock()
        self._connection_lock = threading.Lock()

    # =====================================================
    # PROPERTIES
    # =====================================================

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = int(value)

    @property
    def connected(self):
        return self._connected

    @property
    def token(self):
        return self._token

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @property
    def display_name(self):
        return self._display_name

    @property
    def role(self):
        return self._role

    # =====================================================
    # CONNECTION
    # =====================================================

    def connect(self):
        with self._connection_lock:
            if (
                self._connected
                and self._socket is not None
            ):
                return True

            self._close_socket()

            try:
                self._socket = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM
                )

                self._socket.connect(
                    (
                        self._host,
                        self._port
                    )
                )

                self._buffer = ""
                self._connected = True
                self._running = True

                self._receiver_thread = (
                    threading.Thread(
                        target=self._receive_loop,
                        daemon=True
                    )
                )

                self._receiver_thread.start()

                print(
                    f"Connected to "
                    f"{self._host}:{self._port}"
                )

                return True

            except OSError as error:
                self._connected = False
                self._running = False

                self._close_socket()

                print(
                    "Connection error:",
                    error
                )

                return False

    def disconnect(self):
        self._running = False
        self._connected = False

        self._close_socket()

    def _close_socket(self):
        if self._socket is None:
            return

        try:
            self._socket.shutdown(
                socket.SHUT_RDWR
            )
        except OSError:
            pass

        try:
            self._socket.close()
        except OSError:
            pass

        self._socket = None

    def _ensure_connection(self):
        if (
            self._connected
            and self._socket is not None
        ):
            return True

        return self.connect()

    # =====================================================
    # SEND
    # =====================================================

    def _send_json(
        self,
        data
    ):
        if (
            not self._connected
            or self._socket is None
        ):
            raise ConnectionError(
                "Немає з'єднання із сервером."
            )

        message = (
            json.dumps(
                data,
                ensure_ascii=False
            )
            + "\n"
        )

        encoded_message = (
            message.encode(
                "utf-8"
            )
        )

        with self._send_lock:
            self._socket.sendall(
                encoded_message
            )

    # =====================================================
    # RECEIVE
    # =====================================================

    def _receive_loop(self):
        current_socket = self._socket

        try:
            while self._running:
                data = current_socket.recv(
                    4096
                )

                if not data:
                    break

                self._buffer += data.decode(
                    "utf-8"
                )

                while "\n" in self._buffer:
                    (
                        message,
                        self._buffer
                    ) = self._buffer.split(
                        "\n",
                        1
                    )

                    if not message.strip():
                        continue

                    try:
                        packet = json.loads(
                            message
                        )

                        self._process_packet(
                            packet
                        )

                    except json.JSONDecodeError:
                        print(
                            "Invalid JSON received:"
                        )

                        print(
                            message
                        )

        except (
            OSError,
            ConnectionError
        ):
            pass

        finally:
            # Важливо:
            # старий receiver не повинен
            # вимкнути нове підключення,
            # якщо reconnect вже відбувся.
            if (
                self._socket
                is current_socket
            ):
                self._connected = False
                self._running = False

                with self._response_condition:
                    self._response_condition.notify_all()

    def _process_packet(
        self,
        packet
    ):
        packet_type = packet.get(
            "type"
        )

        # Події від сервера без запиту клієнта.
        if packet_type in (
            "NEW_MESSAGE",
            "MESSAGE_READ",
            "SESSION_TERMINATED"
        ):
            self._handle_event(
                packet_type,
                packet
            )

            return

        # Звичайна відповідь на запит.
        with self._response_condition:
            self._pending_response = packet

            self._response_condition.notify_all()

    # =====================================================
    # REQUEST
    # =====================================================

    def _request(
        self,
        data,
        timeout=5
    ):
        # В один момент часу виконуємо
        # лише один звичайний request-response.
        with self._request_lock:

            # Якщо socket впав —
            # автоматично перепідключаємося.
            if not self._ensure_connection():
                return {
                    "status": "ERROR",
                    "message": (
                        "Не вдалося підключитися "
                        "до сервера."
                    )
                }

            with self._response_condition:
                self._pending_response = None

                try:
                    self._send_json(
                        data
                    )

                except (
                    OSError,
                    ConnectionError
                ):
                    # Сокет міг померти між
                    # ensure_connection та sendall.
                    self._connected = False

                    if not self.connect():
                        return {
                            "status": "ERROR",
                            "message": (
                                "Немає з'єднання "
                                "із сервером."
                            )
                        }

                    try:
                        self._send_json(
                            data
                        )

                    except (
                        OSError,
                        ConnectionError
                    ) as error:
                        return {
                            "status": "ERROR",
                            "message": str(
                                error
                            )
                        }

                received = (
                    self._response_condition
                    .wait_for(
                        lambda:
                        (
                            self._pending_response
                            is not None
                        )
                        or (
                            not self._connected
                        ),
                        timeout=timeout
                    )
                )

                if not received:
                    return {
                        "status": "ERROR",
                        "message": (
                            "Сервер не відповідає."
                        )
                    }

                if (
                    self._pending_response
                    is None
                ):
                    return {
                        "status": "ERROR",
                        "message": (
                            "З'єднання із сервером "
                            "було втрачено."
                        )
                    }

                response = (
                    self._pending_response
                )

                self._pending_response = None

                return response

    # =====================================================
    # EVENTS
    # =====================================================

    def set_event_handler(
        self,
        event_type,
        handler
    ):
        self._event_handlers[
            event_type
        ] = handler

    def remove_event_handler(
        self,
        event_type
    ):
        self._event_handlers.pop(
            event_type,
            None
        )

    def _handle_event(
        self,
        event_type,
        data
    ):
        if (
            event_type
            == "SESSION_TERMINATED"
        ):
            self._token = None
            self._user_id = None
            self._username = None
            self._display_name = None
            self._role = None

        handler = (
            self._event_handlers.get(
                event_type
            )
        )

        if handler is not None:
            try:
                handler(
                    data
                )

            except Exception as error:
                print(
                    "Event handler error:",
                    error
                )

    # =====================================================
    # AUTH
    # =====================================================

    def register(
        self,
        username,
        display_name,
        password
    ):
        return self._request(
            {
                "type": "REGISTER",
                "username": username,
                "display_name": display_name,
                "password": password
            }
        )

    def login(
        self,
        username,
        password
    ):
        response = self._request(
            {
                "type": "LOGIN",
                "username": username,
                "password": password
            }
        )

        if (
            response.get("status")
            == "OK"
        ):
            self._token = response.get(
                "token"
            )

            self._user_id = response.get(
                "user_id"
            )

            self._username = response.get(
                "username"
            )

            self._display_name = response.get(
                "display_name"
            )

            self._role = response.get(
                "role"
            )

        return response

    def logout(self):
        if not self._token:
            return {
                "status": "ERROR",
                "message": (
                    "Активна сесія відсутня."
                )
            }

        response = self._request(
            {
                "type": "LOGOUT",
                "token": self._token
            }
        )

        if (
            response.get("status")
            == "OK"
        ):
            self._token = None
            self._user_id = None
            self._username = None
            self._display_name = None
            self._role = None

        return response

    # =====================================================
    # USERS
    # =====================================================

    def check_username(
        self,
        username
    ):
        return self._request(
            {
                "type": "CHECK_USERNAME",
                "username": username
            }
        )

    def search_users(
        self,
        query
    ):
        return self._request(
            {
                "type": "SEARCH_USER",
                "token": self._token,
                "query": query
            }
        )

    # =====================================================
    # CHATS
    # =====================================================

    def get_chats(self):
        return self._request(
            {
                "type": "GET_CHATS",
                "token": self._token
            }
        )

    def get_history(
        self,
        chat_id
    ):
        return self._request(
            {
                "type": "GET_HISTORY",
                "token": self._token,
                "chat_id": chat_id
            }
        )

    def clear_chat(
        self,
        chat_id
    ):
        return self._request(
            {
                "type": "CLEAR_CHAT",
                "token": self._token,
                "chat_id": chat_id
            }
        )

    # =====================================================
    # MESSAGES
    # =====================================================

    def send_message(
        self,
        recipient_id,
        text
    ):
        return self._request(
            {
                "type": "SEND_MESSAGE",
                "token": self._token,
                "recipient_id": recipient_id,
                "text": text
            }
        )

    def mark_as_read(
        self,
        chat_id
    ):
        return self._request(
            {
                "type": "MARK_AS_READ",
                "token": self._token,
                "chat_id": chat_id
            }
        )

    def delete_message(
        self,
        message_id
    ):
        return self._request(
            {
                "type": "DELETE_MESSAGE",
                "token": self._token,
                "message_id": message_id
            }
        )

    # =====================================================
    # ADMIN
    # =====================================================

    def get_users(self):
        return self._request(
            {
                "type": "GET_USERS",
                "token": self._token
            }
        )

    def block_user(
        self,
        user_id
    ):
        return self._request(
            {
                "type": "BLOCK_USER",
                "token": self._token,
                "user_id": user_id
            }
        )

    def unblock_user(
        self,
        user_id
    ):
        return self._request(
            {
                "type": "UNBLOCK_USER",
                "token": self._token,
                "user_id": user_id
            }
        )

    def delete_user(
        self,
        user_id
    ):
        return self._request(
            {
                "type": "DELETE_USER",
                "token": self._token,
                "user_id": user_id
            }
        )

    def get_audit_log(
        self,
        limit=100
    ):
        return self._request(
            {
                "type": "GET_AUDIT_LOG",
                "token": self._token,
                "limit": limit
            }
        )