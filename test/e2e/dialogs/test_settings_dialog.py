import pytest
from PyQt6.QtCore import Qt
from src.gui.dialogs.settings import SettingsDialog


class TestSettingsDialog:
    """Test suite for the Settings dialog functionality."""

    def test_dialog_initialization(self, main_window):
        """Test that the Settings dialog initializes correctly."""
        dialog = SettingsDialog(main_window)
        assert dialog.windowTitle() == "Settings"
        dialog.show()
        dialog.close()

    def test_dialog_accept(self, main_window):
        """Test that the dialog can be accepted."""
        dialog = SettingsDialog(main_window)
        dialog.accept()
        # Accepting a dialog should not raise

    def test_dialog_reject(self, main_window):
        """Test that the dialog can be rejected."""
        dialog = SettingsDialog(main_window)
        dialog.reject()
        # Rejecting a dialog should not raise 