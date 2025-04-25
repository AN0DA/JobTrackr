from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class ProgressBar(Widget):
    """A custom progress bar widget."""

    DEFAULT_CSS = """
    ProgressBar {
        height: 1;
        width: 100%;
    }

    ProgressBar > .progress-background {
        background: $surface-lighten-2;
        color: $text;
        width: 100%;
        height: 100%;
    }

    ProgressBar > .progress-bar {
        background: $success;
        color: $text;
        height: 100%;
    }
    """

    def __init__(self, total=100, value=0, **kwargs):
        super().__init__(**kwargs)
        self.total = max(1, total)  # Prevent division by zero
        self.value = min(max(0, value), total)  # Clamp between 0 and total

    def compose(self) -> ComposeResult:
        yield Static("", classes="progress-background")
        yield Static("", classes="progress-bar")

    def on_mount(self):
        self.update_progress()

    def update_progress(self):
        percentage = min(100, max(0, (self.value / self.total) * 100))
        self.query_one(".progress-bar").styles.width = f"{percentage}%"

    def update(self, value):
        self.value = min(max(0, value), self.total)  # Clamp between 0 and total
        self.update_progress()
