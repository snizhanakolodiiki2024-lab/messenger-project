# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QTextBrowser,
    QMessageBox,
    QLineEdit
)


class AdminWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, network_client):
        super().__init__()

        self._network_client = network_client
        self._users = []

        self.setWindowTitle(
            "Messenger — Адміністратор"
        )

        self.setMinimumSize(
            1000,
            650
        )

        self.resize(
            1100,
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
            15,
            15,
            15,
            15
        )

        main_layout.setSpacing(
            12
        )

        # =================================================
        # HEADER
        # =================================================

        header_layout = QHBoxLayout()

        self.admin_label = QLabel(
            "Панель адміністратора"
        )

        self.admin_label.setObjectName(
            "sectionTitle"
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

        header_layout.addWidget(
            self.admin_label
        )

        header_layout.addStretch()

        header_layout.addWidget(
            self.logout_button
        )

        main_layout.addLayout(
            header_layout
        )

        # =================================================
        # TABS
        # =================================================

        self.tabs = QTabWidget()

        main_layout.addWidget(
            self.tabs,
            1
        )

        # =================================================
        # USERS TAB
        # =================================================

        users_tab = QWidget()

        users_layout = QVBoxLayout(
            users_tab
        )

        users_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        # Search
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Пошук користувача..."
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.refresh_users_button = QPushButton(
            "Оновити"
        )

        self.refresh_users_button.setObjectName(
            "smallPrimaryButton"
        )

        search_layout.addWidget(
            self.search_input,
            1
        )

        search_layout.addWidget(
            self.refresh_users_button
        )

        users_layout.addLayout(
            search_layout
        )

        # Table
        self.users_table = QTableWidget()

        self.users_table.setColumnCount(
            7
        )

        self.users_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Логін",
                "Ім'я",
                "Роль",
                "Заблокований",
                "Видалений",
                "Дата створення"
            ]
        )

        self.users_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.users_table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.users_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.users_table.verticalHeader().setVisible(
            False
        )

        header = (
            self.users_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        users_layout.addWidget(
            self.users_table,
            1
        )

        # Buttons
        actions_layout = QHBoxLayout()

        self.block_button = QPushButton(
            "Заблокувати"
        )

        self.unblock_button = QPushButton(
            "Розблокувати"
        )

        self.delete_button = QPushButton(
            "Видалити обліковий запис"
        )

        self.block_button.setObjectName(
            "primaryButton"
        )

        self.unblock_button.setObjectName(
            "primaryButton"
        )

        self.delete_button.setObjectName(
            "logoutButton"
        )

        actions_layout.addWidget(
            self.block_button
        )

        actions_layout.addWidget(
            self.unblock_button
        )

        actions_layout.addWidget(
            self.delete_button
        )

        actions_layout.addStretch()

        users_layout.addLayout(
            actions_layout
        )

        self.tabs.addTab(
            users_tab,
            "Користувачі"
        )

        # =================================================
        # AUDIT LOG TAB
        # =================================================

        audit_tab = QWidget()

        audit_layout = QVBoxLayout(
            audit_tab
        )

        audit_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        audit_top_layout = QHBoxLayout()

        audit_title = QLabel(
            "Журнал системних подій"
        )

        audit_title.setObjectName(
            "sectionTitle"
        )

        self.refresh_audit_button = QPushButton(
            "Оновити журнал"
        )

        self.refresh_audit_button.setObjectName(
            "smallPrimaryButton"
        )

        audit_top_layout.addWidget(
            audit_title
        )

        audit_top_layout.addStretch()

        audit_top_layout.addWidget(
            self.refresh_audit_button
        )

        audit_layout.addLayout(
            audit_top_layout
        )

        self.audit_view = QTextBrowser()

        audit_layout.addWidget(
            self.audit_view,
            1
        )

        self.tabs.addTab(
            audit_tab,
            "Журнал подій"
        )

    # =====================================================
    # SIGNALS
    # =====================================================

    def _connect_signals(self):
        self.logout_button.clicked.connect(
            self._logout
        )

        self.refresh_users_button.clicked.connect(
            self.load_users
        )

        self.refresh_audit_button.clicked.connect(
            self.load_audit_log
        )

        self.block_button.clicked.connect(
            self._block_selected_user
        )

        self.unblock_button.clicked.connect(
            self._unblock_selected_user
        )

        self.delete_button.clicked.connect(
            self._delete_selected_user
        )

        self.search_input.textChanged.connect(
            self._filter_users
        )

    # =====================================================
    # INITIAL LOAD
    # =====================================================

    def load_data(self):
        self.admin_label.setText(
            (
                "Панель адміністратора — "
                f"{self._network_client.display_name}"
            )
        )

        self.search_input.clear()

        self.load_users()
        self.load_audit_log()

    # =====================================================
    # USERS
    # =====================================================

    def load_users(self):
        try:
            response = (
                self._network_client
                .get_users()
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
                        "Не вдалося отримати список користувачів."
                    )
                )

                return

            self._users = response.get(
                "users",
                []
            )

            self._display_users(
                self._users
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Не вдалося отримати "
                    "список користувачів:\n"
                    f"{error}"
                )
            )

    def _display_users(
        self,
        users
    ):
        self.users_table.setRowCount(
            len(users)
        )

        for row, user in enumerate(
            users
        ):
            values = [
                user.get(
                    "user_id",
                    ""
                ),
                user.get(
                    "username",
                    ""
                ),
                user.get(
                    "display_name",
                    ""
                ),
                user.get(
                    "role",
                    ""
                ),
                (
                    "Так"
                    if user.get(
                        "is_blocked"
                    )
                    else "Ні"
                ),
                (
                    "Так"
                    if user.get(
                        "is_deleted"
                    )
                    else "Ні"
                ),
                user.get(
                    "created_at",
                    ""
                )
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                if column == 0:
                    item.setData(
                        Qt.UserRole,
                        user
                    )

                self.users_table.setItem(
                    row,
                    column,
                    item
                )

    def _filter_users(
        self,
        text
    ):
        search_text = (
            text.strip().lower()
        )

        if not search_text:
            self._display_users(
                self._users
            )

            return

        filtered = []

        for user in self._users:
            username = str(
                user.get(
                    "username",
                    ""
                )
            ).lower()

            display_name = str(
                user.get(
                    "display_name",
                    ""
                )
            ).lower()

            if (
                search_text in username
                or search_text
                in display_name
            ):
                filtered.append(
                    user
                )

        self._display_users(
            filtered
        )

    def _get_selected_user(self):
        row = (
            self.users_table
            .currentRow()
        )

        if row < 0:
            QMessageBox.information(
                self,
                "Користувач",
                "Спочатку виберіть користувача."
            )

            return None

        item = (
            self.users_table
            .item(
                row,
                0
            )
        )

        if item is None:
            return None

        return item.data(
            Qt.UserRole
        )

    # =====================================================
    # BLOCK
    # =====================================================

    def _block_selected_user(self):
        user = (
            self._get_selected_user()
        )

        if user is None:
            return

        if (
            user.get("role")
            == "ADMIN"
        ):
            QMessageBox.warning(
                self,
                "Операція недоступна",
                "Адміністратора блокувати не можна."
            )

            return

        answer = QMessageBox.question(
            self,
            "Блокування",
            (
                "Заблокувати користувача "
                f"'{user['username']}'?"
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        try:
            response = (
                self._network_client
                .block_user(
                    user[
                        "user_id"
                    ]
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                QMessageBox.information(
                    self,
                    "Блокування",
                    response.get(
                        "message",
                        "Користувача заблоковано."
                    )
                )

                self.load_users()
                self.load_audit_log()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося заблокувати користувача."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                str(error)
            )

    # =====================================================
    # UNBLOCK
    # =====================================================

    def _unblock_selected_user(self):
        user = (
            self._get_selected_user()
        )

        if user is None:
            return

        try:
            response = (
                self._network_client
                .unblock_user(
                    user[
                        "user_id"
                    ]
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                QMessageBox.information(
                    self,
                    "Розблокування",
                    response.get(
                        "message",
                        "Користувача розблоковано."
                    )
                )

                self.load_users()
                self.load_audit_log()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося розблокувати користувача."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                str(error)
            )

    # =====================================================
    # DELETE USER
    # =====================================================

    def _delete_selected_user(self):
        user = (
            self._get_selected_user()
        )

        if user is None:
            return

        if (
            user.get("role")
            == "ADMIN"
        ):
            QMessageBox.warning(
                self,
                "Операція недоступна",
                "Обліковий запис адміністратора видаляти не можна."
            )

            return

        answer = QMessageBox.warning(
            self,
            "Видалення облікового запису",
            (
                "Ви дійсно хочете видалити "
                f"обліковий запис '{user['username']}'?"
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        try:
            response = (
                self._network_client
                .delete_user(
                    user[
                        "user_id"
                    ]
                )
            )

            if (
                response.get("status")
                == "OK"
            ):
                QMessageBox.information(
                    self,
                    "Видалення",
                    response.get(
                        "message",
                        "Обліковий запис видалено."
                    )
                )

                self.load_users()
                self.load_audit_log()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        "Не вдалося видалити обліковий запис."
                    )
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                str(error)
            )

    # =====================================================
    # AUDIT LOG
    # =====================================================

    def load_audit_log(self):
        try:
            response = (
                self._network_client
                .get_audit_log(
                    100
                )
            )

            if (
                response.get("status")
                != "OK"
            ):
                self.audit_view.setText(
                    response.get(
                        "message",
                        "Не вдалося завантажити журнал."
                    )
                )

                return

            logs = response.get(
                "logs",
                []
            )

            self.audit_view.clear()

            if not logs:
                self.audit_view.setText(
                    "Журнал системних подій порожній."
                )

                return

            for log in logs:
                username = log.get(
                    "username"
                )

                if not username:
                    username = "-"

                text = (
                    "----------------------------------------\n"
                    f"ID: {log.get('log_id', '')}\n"
                    f"Користувач: {username}\n"
                    f"Подія: {log.get('event_type', '')}\n"
                    f"Опис: {log.get('description', '')}\n"
                    f"Час: {log.get('created_at', '')}\n"
                )

                self.audit_view.append(
                    text
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка",
                (
                    "Не вдалося завантажити "
                    "журнал подій:\n"
                    f"{error}"
                )
            )

    # =====================================================
    # LOGOUT
    # =====================================================

    def _logout(self):
        answer = QMessageBox.question(
            self,
            "Вихід",
            "Ви дійсно хочете вийти?",
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self._network_client.logout()

        except Exception as error:
            print(
                "Admin logout error:",
                error
            )

        self.logout_requested.emit()