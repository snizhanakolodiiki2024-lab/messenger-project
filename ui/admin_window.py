# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
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

        users_layout.setSpacing(
            10
        )

        # =================================================
        # SEARCH
        # =================================================

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Пошук користувача..."
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        users_layout.addWidget(
            self.search_input
        )

        # =================================================
        # USERS TABLE
        # =================================================

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

        # =================================================
        # ACTION BUTTONS
        # =================================================

        actions_layout = QHBoxLayout()

        actions_layout.setSpacing(
            8
        )

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

        self.block_button.setCursor(
            Qt.PointingHandCursor
        )

        self.unblock_button.setCursor(
            Qt.PointingHandCursor
        )

        self.delete_button.setCursor(
            Qt.PointingHandCursor
        )

        # Поки користувач не вибраний,
        # усі дії недоступні.
        self.block_button.setEnabled(
            False
        )

        self.unblock_button.setEnabled(
            False
        )

        self.delete_button.setEnabled(
            False
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

        audit_layout.setSpacing(
            10
        )

        audit_title = QLabel(
            "Журнал системних подій"
        )

        audit_title.setObjectName(
            "sectionTitle"
        )

        audit_layout.addWidget(
            audit_title
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

        self.users_table.itemSelectionChanged.connect(
            self._update_action_buttons
        )

        # Дані автоматично оновлюються,
        # коли адміністратор переходить
        # між вкладками.
        self.tabs.currentChanged.connect(
            self._on_tab_changed
        )

    # =====================================================
    # INITIAL LOAD
    # =====================================================

    def load_data(self):
        # Заголовок завжди однаковий.
        self.admin_label.setText(
            "Панель адміністратора"
        )

        self.search_input.clear()

        # При кожному новому вході
        # відкриваємо вкладку користувачів.
        self.tabs.setCurrentIndex(
            0
        )

        self.load_users()

    # =====================================================
    # TAB CHANGED
    # =====================================================

    def _on_tab_changed(
        self,
        index
    ):
        if index == 0:
            self.load_users()

        elif index == 1:
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

            users = response.get(
                "users",
                []
            )

            # Видалені акаунти залишаються
            # доступними адміністратору,
            # але відображаються внизу.
            self._users = sorted(
                users,
                key=lambda user: (
                    bool(
                        user.get(
                            "is_deleted"
                        )
                    ),
                    int(
                        user.get(
                            "user_id",
                            0
                        )
                    )
                )
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

    # =====================================================
    # DISPLAY USERS
    # =====================================================

    def _display_users(
        self,
        users
    ):
        self.users_table.clearSelection()

        self.users_table.setRowCount(
            len(users)
        )

        for row, user in enumerate(
            users
        ):
            is_deleted = bool(
                user.get(
                    "is_deleted"
                )
            )

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
                    if is_deleted
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

                # Видалені акаунти не зникають
                # з історії адміністратора.
                # Вони просто виглядають
                # приглушеними.
                if is_deleted:
                    item.setForeground(
                        QBrush(
                            QColor(
                                "#82778F"
                            )
                        )
                    )

                    item.setBackground(
                        QBrush(
                            QColor(
                                "#211927"
                            )
                        )
                    )

                self.users_table.setItem(
                    row,
                    column,
                    item
                )

        self._update_action_buttons()

    # =====================================================
    # FILTER USERS
    # =====================================================

    def _filter_users(
        self,
        text
    ):
        search_text = (
            text
            .strip()
            .lower()
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

            role = str(
                user.get(
                    "role",
                    ""
                )
            ).lower()

            if (
                search_text in username
                or search_text in display_name
                or search_text in role
            ):
                filtered.append(
                    user
                )

        self._display_users(
            filtered
        )

    # =====================================================
    # SELECTED USER
    # =====================================================

    def _get_selected_user(
        self,
        show_message=True
    ):
        row = (
            self.users_table
            .currentRow()
        )

        if row < 0:
            if show_message:
                QMessageBox.information(
                    self,
                    "Користувач",
                    (
                        "Спочатку виберіть "
                        "користувача."
                    )
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
    # ACTION BUTTON STATES
    # =====================================================

    def _update_action_buttons(self):
        user = self._get_selected_user(
            show_message=False
        )

        if user is None:
            self.block_button.setEnabled(
                False
            )

            self.unblock_button.setEnabled(
                False
            )

            self.delete_button.setEnabled(
                False
            )

            return

        role = user.get(
            "role"
        )

        is_deleted = bool(
            user.get(
                "is_deleted"
            )
        )

        is_blocked = bool(
            user.get(
                "is_blocked"
            )
        )

        # Адміністративний акаунт
        # не можна блокувати,
        # розблоковувати чи видаляти.
        if role == "ADMIN":
            self.block_button.setEnabled(
                False
            )

            self.unblock_button.setEnabled(
                False
            )

            self.delete_button.setEnabled(
                False
            )

            return

        # Якщо акаунт уже видалений,
        # жодні подальші дії не потрібні.
        if is_deleted:
            self.block_button.setEnabled(
                False
            )

            self.unblock_button.setEnabled(
                False
            )

            self.delete_button.setEnabled(
                False
            )

            return

        if is_blocked:
            self.block_button.setEnabled(
                False
            )

            self.unblock_button.setEnabled(
                True
            )

        else:
            self.block_button.setEnabled(
                True
            )

            self.unblock_button.setEnabled(
                False
            )

        self.delete_button.setEnabled(
            True
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
                (
                    "Адміністратора "
                    "блокувати не можна."
                )
            )

            return

        if user.get(
            "is_deleted"
        ):
            QMessageBox.warning(
                self,
                "Операція недоступна",
                (
                    "Видалений обліковий запис "
                    "блокувати не можна."
                )
            )

            return

        if user.get(
            "is_blocked"
        ):
            QMessageBox.information(
                self,
                "Блокування",
                (
                    "Цей користувач уже "
                    "заблокований."
                )
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

                # Журнал теж синхронізуємо
                # автоматично після операції.
                self.load_audit_log()

            else:
                QMessageBox.warning(
                    self,
                    "Помилка",
                    response.get(
                        "message",
                        (
                            "Не вдалося "
                            "заблокувати користувача."
                        )
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

        if (
            user.get("role")
            == "ADMIN"
        ):
            QMessageBox.warning(
                self,
                "Операція недоступна",
                (
                    "Для адміністратора "
                    "ця операція недоступна."
                )
            )

            return

        if user.get(
            "is_deleted"
        ):
            QMessageBox.warning(
                self,
                "Операція недоступна",
                (
                    "Видалений обліковий запис "
                    "розблокувати не можна."
                )
            )

            return

        if not user.get(
            "is_blocked"
        ):
            QMessageBox.information(
                self,
                "Розблокування",
                (
                    "Цей користувач "
                    "не заблокований."
                )
            )

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
                        (
                            "Користувача "
                            "розблоковано."
                        )
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
                        (
                            "Не вдалося "
                            "розблокувати користувача."
                        )
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
                (
                    "Обліковий запис "
                    "адміністратора видаляти "
                    "не можна."
                )
            )

            return

        if user.get(
            "is_deleted"
        ):
            QMessageBox.information(
                self,
                "Видалення",
                (
                    "Цей обліковий запис "
                    "уже видалено."
                )
            )

            return

        answer = QMessageBox.warning(
            self,
            "Видалення облікового запису",
            (
                "Ви дійсно хочете видалити "
                f"обліковий запис "
                f"'{user['username']}'?\n\n"
                "Користувач більше не зможе "
                "увійти до системи."
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
                        (
                            "Обліковий запис "
                            "видалено."
                        )
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
                        (
                            "Не вдалося видалити "
                            "обліковий запис."
                        )
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
                        (
                            "Не вдалося "
                            "завантажити журнал."
                        )
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
                    (
                        "Журнал системних "
                        "подій порожній."
                    )
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