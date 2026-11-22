# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, Signal
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


class LoginWindow(QWidget):
    login_successful = Signal(dict)
    register_requested = Signal()

    def __init__(self, network_client):
        super().__init__()

        self._network_client = network_client
        self._password_visible = False

        self.setObjectName(
            "authRoot"
        )

        self.setWindowTitle(
            "Messenger — Вхід"
        )

        # Трохи збільшили саме вікно,
        # щоб картка входу могла бути ширшою.
        self.setMinimumSize(
            560,
            700
        )

        self.resize(
            560,
            700
        )

        self._create_ui()
        self._connect_signals()

    @property
    def network_client(self):
        return self._network_client

    @network_client.setter
    def network_client(self, value):
        self._network_client = value

    # =====================================================
    # UI
    # =====================================================

    def _create_ui(self):
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            40,
            35,
            40,
            30
        )

        main_layout.setSpacing(
            0
        )

        # Верхній відступ
        main_layout.addStretch()

        # =================================================
        # CARD
        # =================================================

        card = QFrame()

        card.setObjectName(
            "loginCard"
        )

        # Було 420.
        # Робимо картку трохи більшою.
        card.setMaximumWidth(
            455
        )

        card.setMinimumWidth(
            455
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            42,
            38,
            42,
            34
        )

        card_layout.setSpacing(
            12
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

        subtitle_label = QLabel(
            "Увійдіть до свого облікового запису"
        )

        subtitle_label.setObjectName(
            "subtitleLabel"
        )

        subtitle_label.setAlignment(
            Qt.AlignCenter
        )

        # ВАЖЛИВО:
        # текст більше не переноситься
        # на два рядки.
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
            25
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

        # Без тексту "Введіть логін"
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

        card_layout.addSpacing(
            6
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

        # Без тексту "Введіть пароль"
        self.password_input.setPlaceholderText(
            ""
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        # Іконка ока
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
        # ERROR
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

        card_layout.addSpacing(
            8
        )

        # =================================================
        # LOGIN
        # =================================================

        self.login_button = QPushButton(
            "Увійти"
        )

        self.login_button.setObjectName(
            "primaryButton"
        )

        self.login_button.setCursor(
            Qt.PointingHandCursor
        )

        self.login_button.setMinimumHeight(
            48
        )

        card_layout.addWidget(
            self.login_button
        )

        main_layout.addWidget(
            card,
            alignment=Qt.AlignCenter
        )

        # =================================================
        # REGISTER LINK
        # =================================================
        #
        # Раніше тут був великий stretch,
        # через який текст ішов далеко вниз.
        # Тепер невеликий фіксований відступ.
        # =================================================

        main_layout.addSpacing(
            22
        )

        bottom_layout = QHBoxLayout()

        bottom_layout.setAlignment(
            Qt.AlignCenter
        )

        bottom_layout.setSpacing(
            4
        )

        bottom_text = QLabel(
            "Ще немає акаунта?"
        )

        bottom_text.setObjectName(
            "bottomText"
        )

        self.register_button = QPushButton(
            "Зареєструватися"
        )

        self.register_button.setObjectName(
            "linkButton"
        )

        self.register_button.setCursor(
            Qt.PointingHandCursor
        )

        bottom_layout.addWidget(
            bottom_text
        )

        bottom_layout.addWidget(
            self.register_button
        )

        main_layout.addLayout(
            bottom_layout
        )

        # Нижній stretch залишаємо,
        # щоб весь блок залишався по центру.
        main_layout.addStretch()

    # =====================================================
    # SIGNALS
    # =====================================================

    def _connect_signals(self):
        self.login_button.clicked.connect(
            self._login
        )

        self.register_button.clicked.connect(
            self.register_requested.emit
        )

        self.show_password_button.clicked.connect(
            self._toggle_password
        )

        self.password_input.returnPressed.connect(
            self._login
        )

        self.username_input.returnPressed.connect(
            self.password_input.setFocus
        )

    # =====================================================
    # PASSWORD
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
    # LOGIN
    # =====================================================

    def _login(self):
        self._clear_error()

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        if not username:
            self._show_error(
                "Введіть логін."
            )

            self.username_input.setFocus()

            return

        if not password:
            self._show_error(
                "Введіть пароль."
            )

            self.password_input.setFocus()

            return

        self.login_button.setEnabled(
            False
        )

        self.login_button.setText(
            "Вхід..."
        )

        try:
            if not self._network_client.connected:
                connected = (
                    self._network_client.connect()
                )

                if not connected:
                    self._show_error(
                        "Не вдалося підключитися до сервера."
                    )

                    return

            response = (
                self._network_client.login(
                    username,
                    password
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                self._clear_error()

                self.login_successful.emit(
                    response
                )

            else:
                self._show_error(
                    response.get(
                        "message",
                        "Не вдалося виконати вхід."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Під час входу виникла "
                    f"помилка:\n{error}"
                )
            )

        finally:
            self.login_button.setEnabled(
                True
            )

            self.login_button.setText(
                "Увійти"
            )