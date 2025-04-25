"""Terminal-based chart widget using plotext."""

import plotext as plt
from textual.widget import Widget
from textual.reactive import reactive
from typing import Dict
from rich.text import Text


class PlotChart(Widget):
    """A widget that displays charts using plotext library."""

    DEFAULT_CSS = """
    PlotChart {
        height: auto;
        min-height: 10;
    }
    """

    # Reactive attributes that will trigger a refresh when changed
    data = reactive({})
    title = reactive("")
    chart_type = reactive("bar")  # bar, line, scatter
    color = reactive("green")

    def __init__(
        self,
        data: Dict[str, float] = None,
        title: str = "",
        chart_type: str = "bar",
        color: str = "green",
        **kwargs,
    ):
        """Initialize the plot chart.

        Args:
            data: Dictionary of x-labels to y-values
            title: Chart title
            chart_type: Type of chart (bar, line, scatter)
            color: Color of the plot
        """
        super().__init__(**kwargs)
        self.data = data or {}
        self.title = title
        self.chart_type = chart_type
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
        # Ensure width and height are at least 1
        width = max(1, self.size.width)
        height = max(1, self.size.height - 2)  # Adjust for potential title/axis space

        plt.plotsize(width, height)

        # Extract data
        x_values = list(self.data.keys())
        y_values = list(self.data.values())

        # Plot based on chart type
        if self.chart_type == "bar":
            plt.bar(x_values, y_values, color=self.color)
        elif self.chart_type == "line":
            # Use numerical indices for x if labels are strings for line/scatter
            indices = range(len(x_values))
            plt.plot(indices, y_values, color=self.color, marker="braille")
            plt.xticks(indices, x_values)  # Set labels for the numerical indices
        elif self.chart_type == "scatter":
            indices = range(len(x_values))
            plt.scatter(indices, y_values, color=self.color, marker="dot")
            plt.xticks(indices, x_values)

        # Set the title
        if self.title:
            plt.title(self.title)

        # Set grid
        plt.grid(True)

        # Build the plot string
        return plt.build()

    def watch_data(self, new_value: Dict[str, float]) -> None:
        """React to data changes."""
        self._cached_plot = None  # Invalidate cache
        self.refresh()

    def watch_title(self, new_value: str) -> None:
        """React to title changes."""
        self._cached_plot = None
        self.refresh()

    def watch_chart_type(self, new_value: str) -> None:
        """React to chart type changes."""
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
