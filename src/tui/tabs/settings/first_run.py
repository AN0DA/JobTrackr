import os

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from src.db.database import init_db
from src.db.settings import Settings


class FirstRunScreen(Screen):
    """First run experience for new users."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings()

    def compose(self) -> ComposeResult:
        with Container(id="welcome-screen"):
            yield Static("Welcome to Job Tracker!", id="welcome-title")

            with Vertical(id="welcome-content"):
                yield Static(
                    "This appears to be your first time running the application. "
                    "Let's set up a few things to get you started.",
                    id="welcome-text",
                )

                yield Static("Database Location", classes="settings-section-title")
                yield Static(
                    "Choose where to store your job application data. The default location is in your home directory.",
                    classes="settings-help-text",
                )

                with Horizontal(id="db-path-row"):
                    yield Label("Database Path:", classes="field-label")
                    yield Input(id="db-path", classes="path-input")
                    yield Button("Browse...", id="browse-db")

                yield Static(
                    "You can change this location later in the Settings menu.",
                    classes="settings-note",
                )

            with Horizontal(id="welcome-buttons"):
                yield Button("Use Default Location", variant="primary", id="use-default")
                yield Button("Continue with Selected Path", id="use-custom")

    def on_mount(self) -> None:
        """Set initial values when screen is mounted."""
        # Set default database path
        db_path = self.settings.get("database_path")
        self.query_one("#db-path", Input).value = db_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "browse-db":
            self.select_database_path()

        elif button_id == "use-default":
            self.save_settings(use_default=True)

        elif button_id == "use-custom":
            self.save_settings(use_default=False)

    def select_database_path(self) -> None:
        """Open file dialog to select database path."""
        from src.tui.widgets.file_dialog import FileDialog

        def on_file_selected(path: str) -> None:
            if path:
                self.query_one("#db-path", Input).value = path

        # Use home directory as starting point
        home_dir = os.path.expanduser("~")

        # Use FileDialog to select path
        self.app.push_screen(
            FileDialog(
                title="Select Database Location",
                path=home_dir,
                file_filter=lambda path: path.suffix == ".db" or path.is_dir(),
                mode="save",
                callback=on_file_selected,
            )
        )

    def save_settings(self, use_default: bool) -> None:
        """Save settings and initialize database."""
        try:
            db_path = self.settings.get("database_path") if use_default else self.query_one("#db-path", Input).value

            # Expand user path if needed
            if db_path.startswith("~"):
                db_path = os.path.expanduser(db_path)

            # Ensure directory exists
            db_dir = os.path.dirname(db_path)
            os.makedirs(db_dir, exist_ok=True)

            # Save to settings
            self.settings.set("database_path", db_path)

            # Initialize database
            if init_db(db_path):
                self.app.sub_title = f"Database initialized at {db_path}"
            else:
                self.app.sub_title = "Failed to initialize database"

            # Continue to main application
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error setting up database: {str(e)}"
