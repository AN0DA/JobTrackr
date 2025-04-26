from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Input, DirectoryTree, DataTable
from textual.binding import Binding
from pathlib import Path
import os
from typing import Callable


class FileDialog(ModalScreen):
    """File dialog for selecting files or directories."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str = "Select File",
        path: str = "~",
        file_filter: Callable[[Path], bool] = None,
        mode: str = "open",  # "open", "save", "directory"
        callback: Callable[[str], None] = None,
    ):
        """Initialize file dialog.

        Args:
            title: Dialog title
            path: Initial path
            file_filter: Function to filter files (returns True to include)
            mode: Dialog mode ('open', 'save', or 'directory')
            callback: Function to call with selected path
        """
        super().__init__()
        self.title_text = title
        self.initial_path = os.path.expanduser(path)
        self.file_filter = file_filter or (lambda p: True)
        self.mode = mode
        self.callback = callback
        self.current_path = self.initial_path

    def compose(self) -> ComposeResult:
        """Compose the file dialog."""
        with Container(id="file-dialog"):
            yield Label(self.title_text, id="dialog-title")

            with Horizontal(id="file-path"):
                yield Label("Location:", classes="field-label")
                yield Input(id="path-input", value=self.initial_path)
                yield Button("↑", id="parent-dir")

            # When saving, we need a filename input
            if self.mode == "save":
                with Horizontal(id="file-name"):
                    yield Label("Filename:", classes="field-label")
                    yield Input(id="name-input")

            # File listing area
            if self.mode == "directory":
                # Show directory tree
                yield DirectoryTree(self.initial_path, id="directory-tree")
            else:
                # Show file table
                yield DataTable(id="file-table")

            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", id="cancel-dialog")
                if self.mode == "open":
                    yield Button("Open", variant="primary", id="confirm-dialog")
                elif self.mode == "save":
                    yield Button("Save", variant="primary", id="confirm-dialog")
                elif self.mode == "directory":
                    yield Button(
                        "Select Directory", variant="primary", id="confirm-dialog"
                    )

    def on_mount(self) -> None:
        """Load files when mounted."""
        if self.mode != "directory":
            # Set up file table
            table = self.query_one("#file-table", DataTable)
            table.add_columns("Name", "Type", "Size")
            table.cursor_type = "row"

            # Load files
            self.load_files(self.initial_path)

    def load_files(self, path: str) -> None:
        """Load files from the given path."""
        try:
            path = os.path.expanduser(path)
            if not os.path.isdir(path):
                path = os.path.dirname(path) or "."

            self.current_path = path
            self.query_one("#path-input", Input).value = path

            table = self.query_one("#file-table", DataTable)
            table.clear()

            # Add parent directory option
            parent = os.path.dirname(path)
            if parent != path:
                table.add_row("..", "Directory", "")

            # Add directories first
            for item in sorted(Path(path).iterdir()):
                if item.is_dir():
                    table.add_row(f"{item.name}/", "Directory", "")

            # Then add files
            for item in sorted(Path(path).iterdir()):
                if item.is_file() and self.file_filter(item):
                    size_str = self._format_size(item.stat().st_size)
                    file_type = item.suffix[1:].upper() if item.suffix else "File"
                    table.add_row(item.name, file_type, size_str)

        except Exception as e:
            self.app.sub_title = f"Error loading files: {str(e)}"

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable form."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0 or unit == "GB":
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in file table."""
        table = self.query_one("#file-table", DataTable)
        row = table.get_row_at(event.row_key)
        item_name = row[0]
        item_type = row[1]

        if item_type == "Directory":
            # Handle directory navigation
            if item_name == "..":
                path = os.path.dirname(self.current_path)
            else:
                path = os.path.join(self.current_path, item_name.rstrip("/"))

            self.load_files(path)

        elif self.mode == "open":
            # For open mode, select file and return immediately
            full_path = os.path.join(self.current_path, item_name)
            if self.callback:
                self.callback(full_path)
            self.app.pop_screen()

        elif self.mode == "save":
            # For save mode, just fill in the filename
            self.query_one("#name-input", Input).value = item_name

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle directory selection in directory tree."""
        if self.mode == "directory":
            self.current_path = str(event.path)
            self.query_one("#path-input", Input).value = self.current_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-dialog":
            self.app.pop_screen()

        elif button_id == "parent-dir":
            # Navigate to parent directory
            parent = os.path.dirname(self.current_path)

            if self.mode == "directory":
                tree = self.query_one("#directory-tree", DirectoryTree)
                tree.path = parent
                self.current_path = parent
                self.query_one("#path-input", Input).value = parent
            else:
                self.load_files(parent)

        elif button_id == "confirm-dialog":
            # Return selected path based on mode
            result_path = None

            if self.mode == "open":
                table = self.query_one("#file-table", DataTable)
                if table.cursor_row is not None:
                    row = table.get_row_at(table.cursor_row)
                    item_name = row[0]
                    item_type = row[1]

                    if item_type != "Directory":
                        result_path = os.path.join(self.current_path, item_name)

            elif self.mode == "save":
                filename = self.query_one("#name-input", Input).value
                if filename:
                    result_path = os.path.join(self.current_path, filename)

            elif self.mode == "directory":
                result_path = self.current_path

            # Call callback with result
            if result_path and self.callback:
                self.callback(result_path)

            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Handle escape key."""
        self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle path input submission."""
        if event.input.id == "path-input":
            path = event.input.value
            if os.path.isdir(path):
                if self.mode == "directory":
                    tree = self.query_one("#directory-tree", DirectoryTree)
                    tree.path = path
                    self.current_path = path
                else:
                    self.load_files(path)
