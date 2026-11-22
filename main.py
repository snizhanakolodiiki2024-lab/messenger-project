# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from client.network_client import NetworkClient

from ui.login_window import LoginWindow
from ui.register_window import RegisterWindow
from ui.main_window import MainWindow
from ui.admin_window import AdminWindow


BASE_DIR = Path(
    __file__
).resolve().parent


def load_styles(
    application
):
    styles_path = (
        BASE_DIR
        / "ui"
        / "styles.qss"
    )

    try:
        with open(
            styles_path,
            "r",
            encoding="utf-8"
        ) as file:

            application.setStyleSheet(
                file.read()
            )

    except OSError as error:
        print(
            "Styles loading error:",
            error
        )


# =========================================================
# WINDOW POSITION
# =========================================================

def move_to_same_center(
    source_window,
    target_window
):
    """
    Розташовує target_window так,
    щоб його центр був у тому самому місці,
    де знаходиться центр source_window.
    """

    source_center = (
        source_window
        .frameGeometry()
        .center()
    )

    target_geometry = (
        target_window
        .frameGeometry()
    )

    target_geometry.moveCenter(
        source_center
    )

    target_window.move(
        target_geometry.topLeft()
    )


def main():
    application = QApplication(
        sys.argv
    )

    application.setApplicationName(
        "Messenger"
    )

    load_styles(
        application
    )

    network_client = NetworkClient()

    login_window = LoginWindow(
        network_client
    )

    register_window = RegisterWindow(
        network_client
    )

    main_window = MainWindow(
        network_client
    )

    admin_window = AdminWindow(
        network_client
    )

    # =====================================================
    # LOGIN SUCCESS
    # =====================================================

    def handle_login_success(
        response
    ):
        login_window.hide()

        role = response.get(
            "role"
        )

        if role == "ADMIN":
            admin_window.load_data()

            admin_window.show()

            admin_window.raise_()

            admin_window.activateWindow()

        else:
            main_window.load_data()

            main_window.show()

            main_window.raise_()

            main_window.activateWindow()

    # =====================================================
    # REGISTER
    # =====================================================

    def open_register_window():
        # Спочатку очищаємо форму.
        register_window.clear_form()

        # Центр реєстрації буде точно
        # в тому самому місці,
        # де зараз знаходиться вхід.
        move_to_same_center(
            login_window,
            register_window
        )

        login_window.hide()

        register_window.show()

        register_window.raise_()

        register_window.activateWindow()

    def back_to_login():
        # Повертаємо вхід у той самий центр,
        # де зараз знаходиться реєстрація.
        move_to_same_center(
            register_window,
            login_window
        )

        register_window.hide()

        login_window.show()

        login_window.raise_()

        login_window.activateWindow()

    def handle_registration_success(
        username
    ):
        # Після успішної реєстрації
        # вхід також відкривається
        # у тому самому місці.
        move_to_same_center(
            register_window,
            login_window
        )

        register_window.hide()

        login_window.username_input.setText(
            username
        )

        login_window.password_input.clear()

        login_window.show()

        login_window.raise_()

        login_window.activateWindow()

        login_window.password_input.setFocus()

    # =====================================================
    # LOGOUT
    # =====================================================

    def show_login_after_logout():
        main_window.hide()

        admin_window.hide()

        login_window.password_input.clear()

        login_window.show()

        login_window.raise_()

        login_window.activateWindow()

    # =====================================================
    # SIGNALS
    # =====================================================

    login_window.login_successful.connect(
        handle_login_success
    )

    login_window.register_requested.connect(
        open_register_window
    )

    register_window.back_requested.connect(
        back_to_login
    )

    register_window.registration_successful.connect(
        handle_registration_success
    )

    main_window.logout_requested.connect(
        show_login_after_logout
    )

    admin_window.logout_requested.connect(
        show_login_after_logout
    )

    application.aboutToQuit.connect(
        network_client.disconnect
    )

    login_window.show()

    sys.exit(
        application.exec()
    )


if __name__ == "__main__":
    main()