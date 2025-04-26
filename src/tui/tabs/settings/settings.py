from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Grid
from textual.widgets import Static, Button, Input, Label, Switch, RadioSet, RadioButton
from textual.widgets import Footer, Header
from textual.binding import Binding
import os

from src.db.settings import Settings
from src.db.database import change_database
from src.tui.widgets.file_dialog import FileDialog


class SettingsScreen(Screen):
    """Screen for application settings."""

    BINDINGS = [Binding("escape", "cancel", "Back"), Binding("f1", "help", "Help")]

    def __init__(self):
        super().__init__()
        self.settings = Settings()

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with Container():
            yield Header(show_clock=True)

            yield Static("Settings", id="settings-title")

            with Container(id="settings-content"):
                # Database Settings
                yield Static("Database Settings", classes="settings-section-title")

                with Grid(id="db-settings-grid"):
                    yield Label("Database Path:")

                    with Horizontal():
                        yield Input(id="db-path", classes="path-input")
                        yield Button("Browse...", id="browse-db")

                    yield Label("Current Status:")
                    yield Static("", id="db-status")

                    yield Label("")
                    yield Button("Apply Database Changes", id="apply-db-changes")

                # Export Settings
                yield Static("Export Settings", classes="settings-section-title")

                with Grid(id="export-settings-grid"):
                    yield Label("Export Directory:")

                    with Horizontal():
                        yield Input(id="export-dir", classes="path-input")
                        yield Button("Browse...", id="browse-export")

                    yield Label("")
                    yield Button("Export Applications", id="export-now")

                # General Settings
                yield Static("General Settings", classes="settings-section-title")

                with Grid(id="general-settings-grid"):
                    yield Label("Theme:")
                    with RadioSet(id="theme-setting"):
                        yield RadioButton("Light")
                        yield RadioButton("Dark")

                    yield Label("Check for updates:")
                    yield Switch(id="updates-switch")

                    yield Label("Save window size:")
                    yield Switch(id="window-size-switch")

            # Action buttons
            with Horizontal(id="settings-actions"):
                yield Button("Save Settings", variant="primary", id="save-settings")
                yield Button("Cancel", id="cancel-settings")

            yield Footer()

    def on_mount(self) -> None:
        """Load settings when the screen is mounted."""
        # Load database path
        db_path = self.settings.get("database_path")
        self.query_one("#db-path", Input).value = db_path

        # Set database status
        if self.settings.database_exists():
            self.query_one("#db-status", Static).update("Database file exists")
            self.query_one("#db-status").styles.color = "green"
        else:
            self.query_one("#db-status", Static).update("Database file does not exist")
            self.query_one("#db-status").styles.color = "red"

        # Load export directory
        export_dir = self.settings.get("export_directory")
        self.query_one("#export-dir", Input).value = export_dir

        # Load other settings
        # theme = self.settings.get("theme", "dark") # FIXME!
        # theme_idx = 1 if theme == "dark" else 0  # 0 for light, 1 for dark
        # self.query_one("#theme-setting", RadioSet).pressed_index = theme_idx

        self.query_one("#updates-switch", Switch).value = self.settings.get(
            "check_updates", True
        )
        self.query_one("#window-size-switch", Switch).value = self.settings.get(
            "save_window_size", True
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "browse-db":
            self.select_database_path()

        elif button_id == "browse-export":
            self.select_export_directory()

        elif button_id == "apply-db-changes":
            self.apply_database_changes()

        elif button_id == "export-now":
            self.export_applications()

        elif button_id == "save-settings":
            self.save_all_settings()

        elif button_id == "cancel-settings":
            self.app.pop_screen()

    def select_database_path(self) -> None:
        """Open file dialog to select database path."""

        def on_file_selected(path: str) -> None:
            if path:
                self.query_one("#db-path", Input).value = path

        # Get initial directory from current path
        current_path = self.query_one("#db-path", Input).value
        initial_dir = os.path.dirname(os.path.expanduser(current_path))

        # Use FileDialog to select path
        self.app.push_screen(
            FileDialog(
                title="Select Database Location",
                path=initial_dir,
                file_filter=lambda path: path.suffix == ".db" or path.is_dir(),
                mode="save",
                callback=on_file_selected,
            )
        )

    def select_export_directory(self) -> None:
        """Open file dialog to select export directory."""

        def on_directory_selected(path: str) -> None:
            if path:
                self.query_one("#export-dir", Input).value = path

        # Get initial directory from current path
        current_path = self.query_one("#export-dir", Input).value
        initial_dir = os.path.expanduser(current_path)

        # Use FileDialog to select directory
        self.app.push_screen(
            FileDialog(
                title="Select Export Directory",
                path=initial_dir,
                file_filter=lambda path: path.is_dir(),
                mode="directory",
                callback=on_directory_selected,
            )
        )

    def apply_database_changes(self) -> None:
        """Apply database path changes."""
        new_db_path = self.query_one("#db-path", Input).value

        # Expand user path if needed
        if new_db_path.startswith("~"):
            new_db_path = os.path.expanduser(new_db_path)

        try:
            # Check if directory exists or can be created
            db_dir = os.path.dirname(new_db_path)
            os.makedirs(db_dir, exist_ok=True)

            # Change database path
            if change_database(new_db_path):
                self.app.sub_title = f"Database changed to {new_db_path}"

                # Update status
                if os.path.exists(new_db_path):
                    self.query_one("#db-status", Static).update("Database file exists")
                    self.query_one("#db-status").styles.color = "green"
                else:
                    self.query_one("#db-status", Static).update("New database created")
                    self.query_one("#db-status").styles.color = "green"
            else:
                self.app.sub_title = "Failed to change database"
                self.query_one("#db-status", Static).update("Error changing database")
                self.query_one("#db-status").styles.color = "red"

        except Exception as e:
            self.app.sub_title = f"Error: {str(e)}"
            self.query_one("#db-status", Static).update(f"Error: {str(e)}")
            self.query_one("#db-status").styles.color = "red"

    def export_applications(self) -> None:
        """Open the export dialog."""
        from src.tui.tabs.settings.export import ExportDialog

        # Update export directory in settings first
        export_dir = self.query_one("#export-dir", Input).value
        if export_dir.startswith("~"):
            export_dir = os.path.expanduser(export_dir)

        # Set export directory in settings
        self.settings.set("export_directory", export_dir)

        # Open export dialog
        self.app.push_screen(ExportDialog())

    def save_all_settings(self) -> None:
        """Save all settings."""
        try:
            # Get values from form
            db_path = self.query_one("#db-path", Input).value
            export_dir = self.query_one("#export-dir", Input).value

            theme_idx = self.query_one("#theme-setting", RadioSet).pressed_index
            theme = "dark" if theme_idx == 1 else "light"

            check_updates = self.query_one("#updates-switch", Switch).value
            save_window_size = self.query_one("#window-size-switch", Switch).value

            # Save all settings
            self.settings.set("database_path", db_path)
            self.settings.set("export_directory", export_dir)
            self.settings.set("theme", theme)
            self.settings.set("check_updates", check_updates)
            self.settings.set("save_window_size", save_window_size)

            self.app.sub_title = "Settings saved"
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error saving settings: {str(e)}"

    def action_cancel(self) -> None:
        """Handle escape key to go back."""
        self.app.pop_screen()
