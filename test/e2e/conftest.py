import sys
import pytest
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

# Add imports for SQLAlchemy and patching
def _patch_db(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.db import models, database

    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch SessionLocal and get_session
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "get_session", lambda: TestingSessionLocal())

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for testing."""
    app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture(scope="function", autouse=True)
def _setup_in_memory_db(monkeypatch):
    """Setup in-memory SQLite DB and patch session for each test."""
    _patch_db(monkeypatch)
    yield

@pytest.fixture
def main_window(app):
    """Create and return a MainWindow instance for testing."""
    window = MainWindow()
    window.show()
    return window 