import sys
import pytest
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for testing."""
    app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def main_window(app):
    """Create and return a MainWindow instance for testing."""
    window = MainWindow()
    window.show()
    return window 