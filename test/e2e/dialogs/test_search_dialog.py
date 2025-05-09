import pytest
from PyQt6.QtCore import Qt
from src.gui.search import SearchDialog


class TestSearchDialog:
    """Test suite for the Search dialog functionality."""

    def test_dialog_initialization(self, main_window):
        """Test that the Search dialog initializes correctly."""
        dialog = SearchDialog(main_window)
        assert dialog.windowTitle() == "Search Applications"
        assert dialog.isVisible()

    def test_dialog_accept(self, main_window):
        """Test that the dialog can be accepted."""
        dialog = SearchDialog(main_window)
        dialog.accept()
        assert not dialog.isVisible()

    def test_dialog_reject(self, main_window):
        """Test that the dialog can be rejected."""
        dialog = SearchDialog(main_window)
        dialog.reject()
        assert not dialog.isVisible() 