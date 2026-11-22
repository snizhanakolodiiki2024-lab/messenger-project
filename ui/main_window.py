# -*- coding: utf-8 -*-

from datetime import datetime, timezone

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QFrame,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QMenu
)


# =========================================================
# TIME HELPERS
# =========================================================

def parse_server_datetime(value):
    if not value:
        return None

    try:
        server_time = datetime.fromisoformat(
            value
        )

        if server_time.tzinfo is None:
            server_time = server_time.replace(
                tzinfo=timezone.utc
            )

        return server_time.astimezone()

    except (ValueError, TypeError):
        return None


def format_message_time(value):
    local_time = parse_server_datetime(
        value
    )

    if local_time is None:
        if value and len(value) >= 16:
            return value[11:16]

        return ""

    return local_time.strftime(
        "%H:%M"
    )


def format_chat_time(value):
    local_time = parse_server_datetime(
        value
    )

    if local_time is None:
        return ""

    now = datetime.now().astimezone()

    if local_time.date() == now.date():
        return local_time.strftime(
            "%H:%M"
        )

    return local_time.strftime(
        "%d.%m"
    )


# =========================================================
# CHAT ITEM
# =========================================================

class ChatItemWidget(QWidget):
    def __init__(
        self,
        name,
        preview="",
        time_text="",
        unread_count=0
    ):
        super().__init__()

        self.setObjectName(
            "chatItemWidget"
        )

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        layout.setSpacing(
            12
        )

        # Avatar
        avatar = QLabel(
            self._get_initials(name)
        )

        avatar.setObjectName(
            "avatarLabel"
        )

        avatar.setAlignment(
            Qt.AlignCenter
        )

        avatar.setFixedSize(
            46,
            46
        )

        # Center
        center_layout = QVBoxLayout()

        center_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        center_layout.setSpacing(
            3
        )

        name_label = QLabel(
            name
        )

        name_label.setObjectName(
            "chatItemName"
        )

        preview_label = QLabel(
            preview or "Немає повідомлень"
        )

        preview_label.setObjectName(
            "chatItemPreview"
        )

        preview_label.setMaximumWidth(
            190
        )

        center_layout.addWidget(
            name_label
        )

        center_layout.addWidget(
            preview_label
        )

        # Right
        right_layout = QVBoxLayout()

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(
            4
        )

        time_label = QLabel(
            time_text
        )

        time_label.setObjectName(
            "chatItemTime"
        )

        time_label.setAlignment(
            Qt.AlignRight
        )

        right_layout.addWidget(
            time_label
        )

        if unread_count > 0:
            unread_label = QLabel(
                str(unread_count)
            )

            unread_label.setObjectName(
                "unreadBadge"
            )

            unread_label.setAlignment(
                Qt.AlignCenter
            )

            unread_label.setFixedSize(
                24,
                24
            )

            right_layout.addWidget(
                unread_label,
                alignment=Qt.AlignRight
            )

        else:
            right_layout.addStretch()

        layout.addWidget(
            avatar
        )

        layout.addLayout(
            center_layout,
            1
        )

        layout.addLayout(
            right_layout
        )

    @staticmethod
    def _get_initials(name):
        words = name.split()

        if not words:
            return "?"

        if len(words) == 1:
            return words[0][0].upper()

        return (
            words[0][0]
            + words[1][0]
        ).upper()


# =========================================================
# MESSAGE BUBBLE
# =========================================================

class MessageBubble(QWidget):
    delete_requested = Signal(int)

    def __init__(
        self,
        message,
        current_user_id,
        current_chat_name
    ):
        super().__init__()

        self._message = message
        self._message_id = message.get(
            "message_id"
        )

        sender_id = message.get(
            "sender_id"
        )

        self.is_own = (
            sender_id
            == current_user_id
        )

        self.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.customContextMenuRequested.connect(
            self._show_context_menu
        )

        root_layout = QHBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            18,
            4,
            18,
            4
        )

        bubble = QFrame()

        if self.is_own:
            bubble.setObjectName(
                "ownMessageBubble"
            )
        else:
            bubble.setObjectName(
                "otherMessageBubble"
            )

        bubble.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Preferred
        )

        bubble_layout = QVBoxLayout(
            bubble
        )

        bubble_layout.setContentsMargins(
            13,
            9,
            13,
            7
        )

        bubble_layout.setSpacing(
            4
        )

        # Sender
        if not self.is_own:
            sender_name = message.get(
                "sender_display_name"
            )

            if not sender_name:
                sender_name = (
                    current_chat_name
                    or "Користувач"
                )

            sender_label = QLabel(
                sender_name
            )

            sender_label.setObjectName(
                "messageSender"
            )

            bubble_layout.addWidget(
                sender_label
            )

        # Text
        text_label = QLabel(
            str(
                message.get(
                    "text",
                    ""
                )
            )
        )

        text_label.setObjectName(
            "messageText"
        )

        text_label.setWordWrap(
            True
        )

        text_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        text_label.setMaximumWidth(
            480
        )

        bubble_layout.addWidget(
            text_label
        )

        # Meta
        meta_layout = QHBoxLayout()

        meta_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        meta_layout.setSpacing(
            5
        )

        meta_layout.addStretch()

        time_label = QLabel(
            format_message_time(
                message.get(
                    "sent_at"
                )
            )
        )

        time_label.setObjectName(
            "messageTime"
        )

        meta_layout.addWidget(
            time_label
        )

        self.status_label = None

        if self.is_own:
            self.status_label = QLabel()

            self.status_label.setObjectName(
                "messageStatus"
            )

            if message.get(
                "read_at"
            ):
                self.status_label.setText(
                    "✓✓"
                )
            else:
                self.status_label.setText(
                    "✓"
                )

            meta_layout.addWidget(
                self.status_label
            )

        bubble_layout.addLayout(
            meta_layout
        )

        if self.is_own:
            root_layout.addStretch()

            root_layout.addWidget(
                bubble
            )

        else:
            root_layout.addWidget(
                bubble
            )

            root_layout.addStretch()

    def mark_as_read(self):
        if self.status_label is not None:
            self.status_label.setText(
                "✓✓"
            )

    def _show_context_menu(
        self,
        position
    ):
        # Видаляти можна тільки власні повідомлення.
        if not self.is_own:
            return

        if self._message_id is None:
            return

        menu = QMenu(self)

        delete_action = menu.addAction(
            "Видалити повідомлення"
        )

        selected_action = menu.exec(
            self.mapToGlobal(
                position
            )
        )

        if selected_action == delete_action:
            self.delete_requested.emit(
                int(
                    self._message_id
                )
            )


# =========================================================
# MAIN WINDOW
# =========================================================

class MainWindow(QWidget):
    logout_requested = Signal()

    new_message_signal = Signal(
        dict
    )

    message_read_signal = Signal(
        dict
    )

    session_terminated_signal = Signal(
        dict
    )

    def __init__(
        self,
        network_client
    ):
        super().__init__()

        self._network_client = (
            network_client
        )

        self._current_chat_id = None
        self._current_recipient_id = None
        self._current_chat_name = None

        self._chats_by_user_id = {}
        self._message_widgets = {}

        self.setWindowTitle(
            "Messenger"
        )

        self.setMinimumSize(
            1050,
            650
        )

        self.resize(
            1200,
            760
        )

        self._create_ui()
        self._connect_signals()
        self._connect_network_events()

    @property
    def network_client(self):
        return self._network_client

    @network_client.setter
    def network_client(
        self,
        value
    ):
        self._network_client = value

    # =====================================================
    # CREATE UI
    # =====================================================

    def _create_ui(self):
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # =================================================
        # TOP BAR
        # =================================================

        top_bar = QFrame()

        top_bar.setObjectName(
            "topBar"
        )

        top_layout = QHBoxLayout(
            top_bar
        )

        top_layout.setContentsMargins(
            20,
            11,
            15,
            11
        )

        self.user_label = QLabel()

        self.user_label.setObjectName(
            "currentUserLabel"
        )

        self.logout_button = QPushButton(
            "Вийти"
        )

        self.logout_button.setObjectName(
            "logoutButton"
        )

        self.logout_button.setCursor(
            Qt.PointingHandCursor
        )

        top_layout.addWidget(
            self.user_label
        )

        top_layout.addStretch()

        top_layout.addWidget(
            self.logout_button
        )

        main_layout.addWidget(
            top_bar
        )

        # =================================================
        # SPLITTER
        # =================================================

        splitter = QSplitter(
            Qt.Horizontal
        )

        # =================================================
        # LEFT
        # =================================================

        left_panel = QFrame()

        left_panel.setObjectName(
            "leftPanel"
        )

        left_layout = QVBoxLayout(
            left_panel
        )

        left_layout.setContentsMargins(
            14,
            14,
            14,
            14
        )

        left_layout.setSpacing(
            10
        )

        chats_title = QLabel(
            "Чати"
        )

        chats_title.setObjectName(
            "sectionTitle"
        )

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Пошук..."
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_button = QPushButton(
            "Пошук"
        )

        self.search_button.setObjectName(
            "smallPrimaryButton"
        )

        self.search_button.setCursor(
            Qt.PointingHandCursor
        )

        search_layout.addWidget(
            self.search_input,
            1
        )

        search_layout.addWidget(
            self.search_button
        )

        self.chat_list = QListWidget()

        self.chat_list.setObjectName(
            "chatList"
        )

        self.chat_list.setSpacing(
            2
        )

        left_layout.addWidget(
            chats_title
        )

        left_layout.addLayout(
            search_layout
        )

        left_layout.addWidget(
            self.chat_list,
            1
        )

        # =================================================
        # RIGHT
        # =================================================

        right_panel = QFrame()

        right_panel.setObjectName(
            "rightPanel"
        )

        right_layout = QVBoxLayout(
            right_panel
        )

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(
            0
        )

        # =================================================
        # CHAT HEADER
        # =================================================

        chat_header = QFrame()

        chat_header.setObjectName(
            "chatHeader"
        )

        header_layout = QHBoxLayout(
            chat_header
        )

        header_layout.setContentsMargins(
            20,
            11,
            20,
            11
        )

        header_text_layout = QVBoxLayout()

        header_text_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        header_text_layout.setSpacing(
            2
        )

        self.chat_name_label = QLabel(
            "Оберіть чат"
        )

        self.chat_name_label.setObjectName(
            "chatNameLabel"
        )

        self.chat_status_label = QLabel(
            "Виберіть діалог зі списку "
            "або знайдіть користувача"
        )

        self.chat_status_label.setObjectName(
            "chatStatusLabel"
        )

        header_text_layout.addWidget(
            self.chat_name_label
        )

        header_text_layout.addWidget(
            self.chat_status_label
        )

        self.clear_chat_button = QPushButton(
            "Очистити переписку"
        )

        self.clear_chat_button.setEnabled(
            False
        )

        self.clear_chat_button.setCursor(
            Qt.PointingHandCursor
        )

        header_layout.addLayout(
            header_text_layout,
            1
        )

        header_layout.addWidget(
            self.clear_chat_button
        )

        # =================================================
        # MESSAGES
        # =================================================

        self.messages_scroll = QScrollArea()

        self.messages_scroll.setObjectName(
            "messagesScroll"
        )

        self.messages_scroll.setWidgetResizable(
            True
        )

        self.messages_scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.messages_container = QWidget()

        self.messages_container.setObjectName(
            "messagesContainer"
        )

        self.messages_layout = QVBoxLayout(
            self.messages_container
        )

        self.messages_layout.setContentsMargins(
            8,
            14,
            8,
            14
        )

        self.messages_layout.setSpacing(
            2
        )

        self.messages_layout.addStretch()

        self.messages_scroll.setWidget(
            self.messages_container
        )

        # =================================================
        # INPUT
        # =================================================

        message_panel = QFrame()

        message_panel.setObjectName(
            "messagePanel"
        )

        message_layout = QHBoxLayout(
            message_panel
        )

        message_layout.setContentsMargins(
            15,
            11,
            15,
            11
        )

        message_layout.setSpacing(
            10
        )

        self.message_input = QLineEdit()

        self.message_input.setPlaceholderText(
            "Напишіть повідомлення..."
        )

        self.message_input.setEnabled(
            False
        )

        self.send_button = QPushButton(
            "Надіслати"
        )

        self.send_button.setObjectName(
            "primaryButton"
        )

        self.send_button.setCursor(
            Qt.PointingHandCursor
        )

        self.send_button.setEnabled(
            False
        )

        message_layout.addWidget(
            self.message_input,
            1
        )

        message_layout.addWidget(
            self.send_button
        )

        right_layout.addWidget(
            chat_header
        )

        right_layout.addWidget(
            self.messages_scroll,
            1
        )

        right_layout.addWidget(
            message_panel
        )

        # =================================================
        # SPLITTER
        # =================================================

        splitter.addWidget(
            left_panel
        )

        splitter.addWidget(
            right_panel
        )

        splitter.setSizes(
            [
                350,
                850
            ]
        )

        splitter.setStretchFactor(
            0,
            0
        )

        splitter.setStretchFactor(
            1,
            1
        )

        main_layout.addWidget(
            splitter,
            1
        )

    # =====================================================
    # SIGNALS
    # =====================================================

    def _connect_signals(self):
        self.logout_button.clicked.connect(
            self._logout
        )

        self.clear_chat_button.clicked.connect(
            self._clear_current_chat
        )

        self.chat_list.itemClicked.connect(
            self._open_chat
        )

        self.search_button.clicked.connect(
            self._search_users
        )

        self.search_input.returnPressed.connect(
            self._search_users
        )

        self.search_input.textChanged.connect(
            self._search_text_changed
        )

        self.send_button.clicked.connect(
            self._send_message
        )

        self.message_input.returnPressed.connect(
            self._send_message
        )

        self.new_message_signal.connect(
            self._on_new_message
        )

        self.message_read_signal.connect(
            self._on_message_read
        )

        self.session_terminated_signal.connect(
            self._on_session_terminated
        )

    def _connect_network_events(self):
        self._network_client.set_event_handler(
            "NEW_MESSAGE",
            lambda data:
            self.new_message_signal.emit(
                data
            )
        )

        self._network_client.set_event_handler(
            "MESSAGE_READ",
            lambda data:
            self.message_read_signal.emit(
                data
            )
        )

        self._network_client.set_event_handler(
            "SESSION_TERMINATED",
            lambda data:
            self.session_terminated_signal.emit(
                data
            )
        )

    # =====================================================
    # LOAD
    # =====================================================

    def load_data(self):
        self.user_label.setText(
            self._network_client.display_name
            or ""
        )

        self._current_chat_id = None
        self._current_recipient_id = None
        self._current_chat_name = None

        self._message_widgets.clear()

        self.search_input.clear()

        self.chat_name_label.setText(
            "Оберіть чат"
        )

        self.chat_status_label.setText(
            "Виберіть діалог зі списку "
            "або знайдіть користувача"
        )

        self.message_input.clear()

        self.message_input.setEnabled(
            False
        )

        self.send_button.setEnabled(
            False
        )

        self.clear_chat_button.setEnabled(
            False
        )

        self._clear_messages()

        self._show_empty_state(
            "Оберіть чат, щоб почати листування"
        )

        self.load_chats()

    # =====================================================
    # CHATS
    # =====================================================

    def load_chats(self):
        try:
            response = (
                self._network_client
                .get_chats()
            )

            if (
                response.get("status")
                != "OK"
            ):
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося завантажити чати."
                    )
                )

                return

            chats = response.get(
                "chats",
                []
            )

            self._chats_by_user_id = {
                chat["user_id"]: chat
                for chat in chats
            }

            self.chat_list.clear()

            selected_item = None

            for chat in chats:
                item = self._create_chat_item(
                    chat
                )

                if (
                    self._current_chat_id
                    is not None
                    and chat.get(
                        "chat_id"
                    )
                    == self._current_chat_id
                ):
                    selected_item = item

            if selected_item is not None:
                self.chat_list.setCurrentItem(
                    selected_item
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Не вдалося завантажити "
                    "список чатів:\n"
                    f"{error}"
                )
            )

    def _create_chat_item(
        self,
        chat,
        search_result=False
    ):
        name = (
            chat.get("display_name")
            or chat.get(
                "username",
                "Користувач"
            )
        )

        if search_result:
            preview = (
                "@"
                + chat.get(
                    "username",
                    ""
                )
            )

            time_text = ""
            unread_count = 0

        else:
            preview = chat.get(
                "last_message"
            )

            if not preview:
                preview = "Немає повідомлень"

            if len(preview) > 31:
                preview = (
                    preview[:31]
                    + "…"
                )

            time_text = format_chat_time(
                chat.get(
                    "last_message_at"
                )
            )

            unread_count = chat.get(
                "unread_count",
                0
            )

        item = QListWidgetItem()

        item.setData(
            Qt.UserRole,
            chat
        )

        widget = ChatItemWidget(
            name=name,
            preview=preview,
            time_text=time_text,
            unread_count=unread_count
        )

        item.setSizeHint(
            widget.sizeHint()
        )

        self.chat_list.addItem(
            item
        )

        self.chat_list.setItemWidget(
            item,
            widget
        )

        return item

    # =====================================================
    # OPEN CHAT
    # =====================================================

    def _open_chat(
        self,
        item
    ):
        chat = item.data(
            Qt.UserRole
        )

        if not isinstance(
            chat,
            dict
        ):
            return

        user_id = chat.get(
            "user_id"
        )

        existing_chat = (
            self._chats_by_user_id.get(
                user_id
            )
        )

        if (
            chat.get("chat_id")
            is None
            and existing_chat
            is not None
        ):
            chat = existing_chat

        self._current_chat_id = (
            chat.get(
                "chat_id"
            )
        )

        self._current_recipient_id = (
            user_id
        )

        self._current_chat_name = (
            chat.get(
                "display_name"
            )
            or chat.get(
                "username",
                "Користувач"
            )
        )

        self.chat_name_label.setText(
            self._current_chat_name
        )

        username = chat.get(
            "username",
            ""
        )

        self.chat_status_label.setText(
            f"@{username}"
        )

        self.message_input.setEnabled(
            True
        )

        self.send_button.setEnabled(
            True
        )

        self.clear_chat_button.setEnabled(
            self._current_chat_id
            is not None
        )

        self.message_input.setFocus()

        if self._current_chat_id is None:
            self._clear_messages()

            self._show_empty_state(
                "Новий діалог.\n"
                "Напишіть перше повідомлення."
            )

            return

        self._load_history()

    # =====================================================
    # HISTORY
    # =====================================================

    def _load_history(self):
        if self._current_chat_id is None:
            return

        try:
            response = (
                self._network_client
                .get_history(
                    self._current_chat_id
                )
            )

            if (
                response.get("status")
                != "OK"
            ):
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося отримати історію."
                    )
                )

                return

            messages = response.get(
                "messages",
                []
            )

            self._clear_messages()

            if not messages:
                self._show_empty_state(
                    "У цьому чаті поки "
                    "немає повідомлень."
                )

            else:
                for message in messages:
                    self._append_message(
                        message
                    )

            read_response = (
                self._network_client
                .mark_as_read(
                    self._current_chat_id
                )
            )

            if (
                read_response.get(
                    "status"
                )
                == "OK"
            ):
                self.load_chats()

            self._scroll_to_bottom()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Не вдалося завантажити "
                    "переписку:\n"
                    f"{error}"
                )
            )

    # =====================================================
    # MESSAGE AREA
    # =====================================================

    def _clear_messages(self):
        self._message_widgets.clear()

        while (
            self.messages_layout.count()
            > 1
        ):
            item = (
                self.messages_layout
                .takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _show_empty_state(
        self,
        text
    ):
        label = QLabel(
            text
        )

        label.setObjectName(
            "emptyChatLabel"
        )

        label.setAlignment(
            Qt.AlignCenter
        )

        label.setWordWrap(
            True
        )

        self.messages_layout.insertWidget(
            0,
            label,
            alignment=Qt.AlignCenter
        )

    def _append_message(
        self,
        message
    ):
        if (
            self.messages_layout.count()
            > 1
        ):
            first_item = (
                self.messages_layout
                .itemAt(0)
            )

            first_widget = (
                first_item.widget()
            )

            if (
                first_widget is not None
                and first_widget.objectName()
                == "emptyChatLabel"
            ):
                removed = (
                    self.messages_layout
                    .takeAt(0)
                )

                if removed.widget():
                    removed.widget().deleteLater()

        bubble = MessageBubble(
            message=message,
            current_user_id=(
                self._network_client.user_id
            ),
            current_chat_name=(
                self._current_chat_name
            )
        )

        bubble.delete_requested.connect(
            self._delete_message
        )

        self.messages_layout.insertWidget(
            self.messages_layout.count()
            - 1,
            bubble
        )

        message_id = message.get(
            "message_id"
        )

        if message_id is not None:
            self._message_widgets[
                message_id
            ] = bubble

        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        scrollbar = (
            self.messages_scroll
            .verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    # =====================================================
    # SEND
    # =====================================================

    def _send_message(self):
        if (
            self._current_recipient_id
            is None
        ):
            return

        text = (
            self.message_input
            .text()
            .strip()
        )

        if not text:
            return

        self.send_button.setEnabled(
            False
        )

        try:
            response = (
                self._network_client
                .send_message(
                    self._current_recipient_id,
                    text
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                self.message_input.clear()

                message = response.get(
                    "message_data"
                )

                if message:
                    self._current_chat_id = (
                        message.get(
                            "chat_id",
                            self._current_chat_id
                        )
                    )

                    self.clear_chat_button.setEnabled(
                        True
                    )

                    self._append_message(
                        message
                    )

                self.load_chats()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося надіслати повідомлення."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Під час надсилання "
                    "повідомлення виникла "
                    f"помилка:\n{error}"
                )
            )

        finally:
            self.send_button.setEnabled(
                True
            )

            self.message_input.setFocus()

    # =====================================================
    # DELETE OWN MESSAGE
    # =====================================================

    def _delete_message(
        self,
        message_id
    ):
        answer = QMessageBox.question(
            self,
            "Видалення повідомлення",
            (
                "Ви дійсно хочете "
                "видалити це повідомлення?"
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        try:
            response = (
                self._network_client
                .delete_message(
                    message_id
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                self._load_history()
                self.load_chats()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося видалити повідомлення."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Під час видалення "
                    "повідомлення виникла "
                    f"помилка:\n{error}"
                )
            )

    # =====================================================
    # CLEAR CHAT
    # =====================================================

    def _clear_current_chat(self):
        if self._current_chat_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Очищення переписки",
            (
                "Очистити історію цього діалогу?\n\n"
                "Переписка буде очищена тільки "
                "для вашого облікового запису."
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        try:
            response = (
                self._network_client
                .clear_chat(
                    self._current_chat_id
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                self._clear_messages()

                self._show_empty_state(
                    "Історію переписки очищено."
                )

                self.load_chats()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося очистити переписку."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Під час очищення "
                    "переписки виникла "
                    f"помилка:\n{error}"
                )
            )

    # =====================================================
    # SEARCH
    # =====================================================

    def _search_text_changed(
        self,
        text
    ):
        if not text.strip():
            self.load_chats()

    def _search_users(self):
        query = (
            self.search_input
            .text()
            .strip()
        )

        if not query:
            self.load_chats()
            return

        try:
            response = (
                self._network_client
                .search_users(
                    query
                )
            )

            if (
                response.get("status")
                != "OK"
            ):
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Помилка пошуку."
                    )
                )

                return

            users = response.get(
                "users",
                []
            )

            self.chat_list.clear()

            if not users:
                item = QListWidgetItem(
                    "Користувачів не знайдено"
                )

                item.setFlags(
                    Qt.NoItemFlags
                )

                self.chat_list.addItem(
                    item
                )

                return

            for user in users:
                existing_chat = (
                    self._chats_by_user_id
                    .get(
                        user[
                            "user_id"
                        ]
                    )
                )

                if existing_chat:
                    search_data = (
                        existing_chat.copy()
                    )

                else:
                    search_data = {
                        "chat_id": None,
                        "user_id": user[
                            "user_id"
                        ],
                        "username": user[
                            "username"
                        ],
                        "display_name": user[
                            "display_name"
                        ],
                        "last_message": None,
                        "last_message_at": None,
                        "unread_count": 0
                    }

                self._create_chat_item(
                    search_data,
                    search_result=True
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Під час пошуку "
                    "користувачів виникла "
                    f"помилка:\n{error}"
                )
            )

    # =====================================================
    # REAL-TIME NEW MESSAGE
    # =====================================================

    def _on_new_message(
        self,
        event
    ):
        message = event.get(
            "message"
        )

        if not isinstance(
            message,
            dict
        ):
            return

        chat_id = message.get(
            "chat_id"
        )

        if (
            self._current_chat_id
            == chat_id
        ):
            self._append_message(
                message
            )

            try:
                self._network_client.mark_as_read(
                    chat_id
                )

            except Exception:
                pass

        self.load_chats()

    # =====================================================
    # REAL-TIME READ
    # =====================================================

    def _on_message_read(
        self,
        event
    ):
        message_ids = event.get(
            "message_ids",
            []
        )

        for message_id in message_ids:
            bubble = (
                self._message_widgets.get(
                    message_id
                )
            )

            if bubble is not None:
                bubble.mark_as_read()

    # =====================================================
    # SESSION TERMINATED
    # =====================================================

    def _on_session_terminated(
        self,
        event
    ):
        reason = event.get(
            "reason",
            "Сесію завершено сервером."
        )

        QMessageBox.warning(
            self,
            "Сесію завершено",
            reason
        )

        self._current_chat_id = None
        self._current_recipient_id = None
        self._current_chat_name = None

        self.logout_requested.emit()

    # =====================================================
    # LOGOUT
    # =====================================================

    def _logout(self):
        answer = QMessageBox.question(
            self,
            "Вихід",
            "Ви дійсно хочете вийти із системи?",
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self._network_client.logout()

        except Exception as error:
            print(
                "Logout error:",
                error
            )

        self.logout_requested.emit()