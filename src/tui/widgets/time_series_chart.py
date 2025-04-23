"""Time series chart widget using plotext."""

import io
import plotext as plt
from textual.widget import Widget
from textual.reactive import reactive
from typing import Dict, List, Tuple, Any, Optional
from rich.text import Text


class TimeSeriesChart(Widget):
    """A widget that displays time series charts using plotext library."""

    DEFAULT_CSS = """
    TimeSeriesChart {
        height: auto;
        min-height: 10;
    }
    """

    # Reactive attributes that will trigger a refresh when changed
    data = reactive([])
    title = reactive("")
    color = reactive("green")

    def __init__(
            self,
            data: List[Tuple[str, float]] = None,
            title: str = "",
            color: str = "green",
            **kwargs
    ):
        """Initialize the time series chart.

        Args:
            data: List of (date_label, value) tuples
            title: Chart title
            color: Color of the plot
        """
        super().__init__(**kwargs)
        self.data = data or []
        self.title = title
        self.color = color
        self._cached_plot = None

    def render(self) -> Text:
        """Render the chart."""
        if not self.data:
            return Text("No data to display")

        # Only regenerate the plot if necessary
        if self._cached_plot is None:
            self._cached_plot = self._generate_plot()

        return Text(self._cached_plot, no_wrap=True)

    def _generate_plot(self) -> str:
        """Generate the plot using plotext."""
        # Reset the plot
        plt.clear_figure()
        plt.clf()

        # Set theme and figure size
        plt.theme("dark")

        # Get the terminal size approximately
        width = max(60, min(120, self.size.width))
        height = max(10, min(20, self.size.height))

        plt.figure(width, height)

        # Extract data
        dates = [item[0] for item in self.data]
        values = [item[1] for item in self.data]

        # Plot the time series
        plt.plot(dates, values, color=self.color, marker="braille")

        # Set the title
        if self.title:
            plt.title(self.title)

        # Set grid and axes labels
        plt.grid(True)
        plt.xticks(range(len(dates)), dates, rotation=90)

        # Capture the plot output as a string
        buffer = io.StringIO()
        plt.show(buffer=buffer)
        return buffer.getvalue()

    def watch_data(self, new_value: List[Tuple[str, float]]) -> None:
        """React to data changes."""
        self._cached_plot = None  # Invalidate cache
        self.refresh()

    def watch_title(self, new_value: str) -> None:
        """React to title changes."""
        self._cached_plot = None
        self.refresh()

    def watch_color(self, new_value: str) -> None:
        """React to color changes."""
        self._cached_plot = None
        self.refresh()

    def on_resize(self) -> None:
        """Handle resize events."""
        self._cached_plot = None  # Size changed, need to regenerate
        self.refresh()