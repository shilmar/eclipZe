"""
Punto de entrada de la aplicación eclipZe.
Lanza la interfaz gráfica multiplataforma en PySide6.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("eclipZe")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
