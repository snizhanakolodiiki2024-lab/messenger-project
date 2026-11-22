# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QMessageBox
)


class RegisterWindow(QWidget):
    # Ці сигнали використовує main.py
    registration_successful = Signal(str)
    back_requested = Signal()

    def __init__(self, network_client):
        super().__init__()

        self._network_client = network_client

        self._password_visible = False
        self._confirm_password_visible = False

        self._username_available = None

        # Затримка перед live-перевіркою логіна
        self._username_timer = QTimer(
            self
        )

        self._username_timer.setSingleShot(
            True
        )

        self._username_timer.setInterval(
            500
        )

        self._username_timer.timeout.connect(
            self._check_username
        )

        self.setObjectName(
            "authRoot"
        )

        self.setWindowTitle(
            "Messenger — Реєстрація"
        )

        self.setMinimumSize(
            620,
            820
        )

        self.resize(
            620,
            820
        )

        self._create_ui()
        self._connect_signals()

    # =====================================================
    # NETWORK CLIENT
    # =====================================================

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
    # UI
    # =====================================================

    def _create_ui(self):
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            45,
            30,
            45,
            25
        )

        main_layout.setSpacing(
            0
        )

        main_layout.addStretch()

        # =================================================
        # CARD
        # =================================================

        card = QFrame()

        card.setObjectName(
            "loginCard"
        )

        card.setMaximumWidth(
            500
        )

        card.setMinimumWidth(
            500
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            48,
            32,
            48,
            30
        )

        card_layout.setSpacing(
            10
        )

        # =================================================
        # TITLE
        # =================================================

        title_label = QLabel(
            "Messenger"
        )

        title_label.setObjectName(
            "titleLabel"
        )

        title_label.setAlignment(
            Qt.AlignCenter
        )

        # Змінено лише текст.
        subtitle_label = QLabel(
            "Створення нового акаунту"
        )

        subtitle_label.setObjectName(
            "subtitleLabel"
        )

        subtitle_label.setAlignment(
            Qt.AlignCenter
        )

        # Один рядок.
        subtitle_label.setWordWrap(
            False
        )

        card_layout.addWidget(
            title_label
        )

        card_layout.addWidget(
            subtitle_label
        )

        card_layout.addSpacing(
            20
        )

        # =================================================
        # FULL NAME
        # =================================================

        display_name_label = QLabel(
            "Ім'я та прізвище"
        )

        display_name_label.setObjectName(
            "fieldLabel"
        )

        self.display_name_input = QLineEdit()

        # Без "Наприклад..."
        self.display_name_input.setPlaceholderText(
            ""
        )

        self.display_name_input.setClearButtonEnabled(
            True
        )

        card_layout.addWidget(
            display_name_label
        )

        card_layout.addWidget(
            self.display_name_input
        )

        # =================================================
        # USERNAME
        # =================================================

        username_label = QLabel(
            "Логін"
        )

        username_label.setObjectName(
            "fieldLabel"
        )

        self.username_input = QLineEdit()

        # Без "Придумайте..."
        self.username_input.setPlaceholderText(
            ""
        )

        self.username_input.setClearButtonEnabled(
            True
        )

        card_layout.addWidget(
            username_label
        )

        card_layout.addWidget(
            self.username_input
        )

        # Статус live-перевірки логіна
        self.username_status_label = QLabel()

        self.username_status_label.setObjectName(
            "usernameStatus"
        )

        self.username_status_label.setWordWrap(
            True
        )

        self.username_status_label.hide()

        card_layout.addWidget(
            self.username_status_label
        )

        # =================================================
        # PASSWORD
        # =================================================

        password_label = QLabel(
            "Пароль"
        )

        password_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            password_label
        )

        password_layout = QHBoxLayout()

        password_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        password_layout.setSpacing(
            8
        )

        self.password_input = QLineEdit()

        # Без "Введіть пароль"
        self.password_input.setPlaceholderText(
            ""
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        self.show_password_button = QPushButton(
            "👁"
        )

        self.show_password_button.setObjectName(
            "eyeButton"
        )

        self.show_password_button.setCursor(
            Qt.PointingHandCursor
        )

        password_layout.addWidget(
            self.password_input,
            1
        )

        password_layout.addWidget(
            self.show_password_button
        )

        card_layout.addLayout(
            password_layout
        )

        # =================================================
        # CONFIRM PASSWORD
        # =================================================

        confirm_label = QLabel(
            "Підтвердження пароля"
        )

        confirm_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            confirm_label
        )

        confirm_layout = QHBoxLayout()

        confirm_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        confirm_layout.setSpacing(
            8
        )

        self.confirm_password_input = QLineEdit()

        # Без "Повторіть пароль"
        self.confirm_password_input.setPlaceholderText(
            ""
        )

        self.confirm_password_input.setEchoMode(
            QLineEdit.Password
        )

        self.show_confirm_button = QPushButton(
            "👁"
        )

        self.show_confirm_button.setObjectName(
            "eyeButton"
        )

        self.show_confirm_button.setCursor(
            Qt.PointingHandCursor
        )

        confirm_layout.addWidget(
            self.confirm_password_input,
            1
        )

        confirm_layout.addWidget(
            self.show_confirm_button
        )

        card_layout.addLayout(
            confirm_layout
        )

        # =================================================
        # GENERAL ERROR
        # =================================================

        self.error_label = QLabel()

        self.error_label.setObjectName(
            "errorLabel"
        )

        self.error_label.setWordWrap(
            True
        )

        self.error_label.hide()

        card_layout.addWidget(
            self.error_label
        )

        # =================================================
        # REGISTER BUTTON
        # =================================================

        self.register_button = QPushButton(
            "Створити акаунт"
        )

        self.register_button.setObjectName(
            "primaryButton"
        )

        self.register_button.setCursor(
            Qt.PointingHandCursor
        )

        self.register_button.setMinimumHeight(
            48
        )

        card_layout.addSpacing(
            8
        )

        card_layout.addWidget(
            self.register_button
        )

        main_layout.addWidget(
            card,
            alignment=Qt.AlignCenter
        )

        # =================================================
        # BOTTOM LOGIN LINK
        # =================================================
        #
        # Прибрали великий stretch між карткою
        # та "Уже маєш акаунт?"
        # =================================================

        main_layout.addSpacing(
            20
        )

        bottom_layout = QHBoxLayout()

        bottom_layout.setAlignment(
            Qt.AlignCenter
        )

        bottom_layout.setSpacing(
            4
        )

        bottom_text = QLabel(
            "Уже маєш акаунт?"
        )

        bottom_text.setObjectName(
            "bottomText"
        )

        self.back_button = QPushButton(
            "Увійти"
        )

        self.back_button.setObjectName(
            "linkButton"
        )

        self.back_button.setCursor(
            Qt.PointingHandCursor
        )

        bottom_layout.addWidget(
            bottom_text
        )

        bottom_layout.addWidget(
            self.back_button
        )

        main_layout.addLayout(
            bottom_layout
        )

        main_layout.addStretch()

    # =====================================================
    # SIGNALS
    # =====================================================

    def _connect_signals(self):
        self.register_button.clicked.connect(
            self._register
        )

        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.show_password_button.clicked.connect(
            self._toggle_password
        )

        self.show_confirm_button.clicked.connect(
            self._toggle_confirm_password
        )

        self.username_input.textChanged.connect(
            self._username_changed
        )

        self.display_name_input.returnPressed.connect(
            self.username_input.setFocus
        )

        self.username_input.returnPressed.connect(
            self.password_input.setFocus
        )

        self.password_input.returnPressed.connect(
            self.confirm_password_input.setFocus
        )

        self.confirm_password_input.returnPressed.connect(
            self._register
        )

    # =====================================================
    # PASSWORD VISIBILITY
    # =====================================================

    def _toggle_password(self):
        self._password_visible = (
            not self._password_visible
        )

        if self._password_visible:
            self.password_input.setEchoMode(
                QLineEdit.Normal
            )

            self.show_password_button.setText(
                "🙈"
            )

        else:
            self.password_input.setEchoMode(
                QLineEdit.Password
            )

            self.show_password_button.setText(
                "👁"
            )

    def _toggle_confirm_password(self):
        self._confirm_password_visible = (
            not self._confirm_password_visible
        )

        if self._confirm_password_visible:
            self.confirm_password_input.setEchoMode(
                QLineEdit.Normal
            )

            self.show_confirm_button.setText(
                "🙈"
            )

        else:
            self.confirm_password_input.setEchoMode(
                QLineEdit.Password
            )

            self.show_confirm_button.setText(
                "👁"
            )

    # =====================================================
    # LIVE USERNAME CHECK
    # =====================================================

    def _username_changed(
        self,
        text
    ):
        self._username_timer.stop()

        username = text.strip()

        self._username_available = None

        if not username:
            self.username_status_label.clear()

            self.username_status_label.hide()

            return

        if len(username) < 3:
            self._set_username_status(
                "Логін повинен містити щонайменше 3 символи.",
                "error"
            )

            return

        self._set_username_status(
            "Перевірка...",
            "checking"
        )

        self._username_timer.start()

    def _check_username(self):
        username = (
            self.username_input
            .text()
            .strip()
        )

        if len(username) < 3:
            return

        try:
            if not self._network_client.connected:
                if not self._network_client.connect():
                    self._username_available = None

                    self._set_username_status(
                        "Не вдалося підключитися до сервера.",
                        "error"
                    )

                    return

            response = (
                self._network_client
                .check_username(
                    username
                )
            )

            # Якщо користувач змінив логін,
            # поки сервер формував відповідь,
            # стару відповідь не показуємо.
            if (
                username
                != self.username_input
                .text()
                .strip()
            ):
                return

            if (
                response.get("status")
                != "OK"
            ):
                self._username_available = None

                self._set_username_status(
                    response.get(
                        "message",
                        "Не вдалося перевірити логін."
                    ),
                    "error"
                )

                return

            available = response.get(
                "available",
                False
            )

            self._username_available = (
                available
            )

            if available:
                self._set_username_status(
                    "✓ Логін вільний",
                    "available"
                )

            else:
                self._set_username_status(
                    "Користувач з таким логіном уже існує.",
                    "error"
                )

        except Exception as error:
            print(
                "Username check error:",
                error
            )

            self._username_available = None

            self._set_username_status(
                "Не вдалося перевірити логін.",
                "error"
            )

    def _set_username_status(
        self,
        text,
        state
    ):
        self.username_status_label.setText(
            text
        )

        if state == "available":
            color = "#8FE3B1"

        elif state == "checking":
            color = "#B7A7CF"

        else:
            color = "#FF7D9C"

        self.username_status_label.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                color: {color};
                font-size: 12px;
                font-weight: 500;
            }}
            """
        )

        self.username_status_label.show()

    # =====================================================
    # ERRORS
    # =====================================================

    def _show_error(
        self,
        message
    ):
        self.error_label.setText(
            message
        )

        self.error_label.show()

    def _clear_error(self):
        self.error_label.clear()

        self.error_label.hide()

    # =====================================================
    # CLEAR FORM
    # =====================================================

    def clear_form(self):
        """
        Викликається з main.py
        перед відкриттям реєстрації.
        """

        self._username_timer.stop()

        self._username_available = None

        self.display_name_input.clear()

        self.username_input.clear()

        self.password_input.clear()

        self.confirm_password_input.clear()

        self.username_status_label.clear()

        self.username_status_label.hide()

        self._clear_error()

        self._password_visible = False

        self._confirm_password_visible = False

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        self.confirm_password_input.setEchoMode(
            QLineEdit.Password
        )

        self.show_password_button.setText(
            "👁"
        )

        self.show_confirm_button.setText(
            "👁"
        )

        self.display_name_input.setFocus()

    # =====================================================
    # REGISTER
    # =====================================================

    def _register(self):
        self._clear_error()

        display_name = (
            self.display_name_input
            .text()
            .strip()
        )

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        confirm_password = (
            self.confirm_password_input
            .text()
        )

        # =================================================
        # VALIDATION
        # =================================================

        if not display_name:
            self._show_error(
                "Введіть ім'я та прізвище."
            )

            self.display_name_input.setFocus()

            return

        if not username:
            self._show_error(
                "Введіть логін."
            )

            self.username_input.setFocus()

            return

        if len(username) < 3:
            self._show_error(
                "Логін повинен містити щонайменше 3 символи."
            )

            self.username_input.setFocus()

            return

        if self._username_available is False:
            self._show_error(
                "Користувач з таким логіном уже існує."
            )

            self.username_input.setFocus()

            return

        if self._username_available is None:
            self._show_error(
                "Зачекайте, поки буде перевірено доступність логіна."
            )

            self.username_input.setFocus()

            return

        if not password:
            self._show_error(
                "Введіть пароль."
            )

            self.password_input.setFocus()

            return

        if len(password) < 6:
            self._show_error(
                "Пароль повинен містити щонайменше 6 символів."
            )

            self.password_input.setFocus()

            return

        if password != confirm_password:
            self._show_error(
                "Паролі не співпадають."
            )

            self.confirm_password_input.setFocus()

            return

        # =================================================
        # REGISTER REQUEST
        # =================================================

        self.register_button.setEnabled(
            False
        )

        self.register_button.setText(
            "Створення..."
        )

        try:
            if not self._network_client.connected:
                if not self._network_client.connect():
                    self._show_error(
                        "Не вдалося підключитися до сервера."
                    )

                    return

            response = (
                self._network_client.register(
                    username=username,
                    display_name=display_name,
                    password=password
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                QMessageBox.information(
                    self,
                    "Реєстрація",
                    (
                        "Обліковий запис успішно створено.\n\n"
                        "Тепер ви можете увійти до системи."
                    )
                )

                self.registration_successful.emit(
                    username
                )

            else:
                message = response.get(
                    "message",
                    "Не вдалося виконати реєстрацію."
                )

                if "логін" in message.lower():
                    self._username_available = False

                    self._set_username_status(
                        message,
                        "error"
                    )

                else:
                    self._show_error(
                        message
                    )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Під час реєстрації виникла помилка:\n"
                    f"{error}"
                )
            )

        finally:
            self.register_button.setEnabled(
                True
            )

            self.register_button.setText(
                "Створити акаунт"
            )