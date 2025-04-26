"""Export dialog for saving application data."""

import csv
import os
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, OptionList

from src.db.settings import Settings
from src.services.application_service import ApplicationService


class ExportDialog(ModalScreen):
    """Dialog for exporting job application data."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings()

    def compose(self) -> ComposeResult:
        with Container(id="export-dialog"):
            yield Label("Export Applications", id="dialog-title")

            with Vertical(id="export-form"):
                yield Label("Export Format", classes="field-label")
                yield OptionList("CSV", "JSON", id="export-format")

                yield Label("Output Directory", classes="field-label")
                yield Input("./exports", id="export-dir")

                yield Label("Export Options", classes="field-label")
                yield Checkbox("Include detailed notes", id="include-notes", value=True)
                yield Checkbox("Include interactions", id="include-interactions", value=True)

            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", id="cancel-export")
                yield Button("Export", variant="success", id="perform-export")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-export":
            self.app.pop_screen()

        elif event.button.id == "perform-export":
            self.export_data()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection in the format list."""
        self.export_format = event.option

    def export_data(self) -> None:
        """Export application data to the selected format."""
        try:
            # Get export options
            export_format = getattr(self, "export_format", "CSV")
            export_dir = self.settings.get_export_directory()
            include_notes = self.query_one("#include-notes", Checkbox).value
            include_interactions = self.query_one("#include-interactions", Checkbox).value

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Get data to export
            service = ApplicationService()
            applications = service.get_applications_for_export(
                include_notes=include_notes, include_interactions=include_interactions
            )

            if export_format == "CSV":
                filename = os.path.join(export_dir, f"applications_{timestamp}.csv")
                self.export_to_csv(applications, filename)

            elif export_format == "JSON":
                filename = os.path.join(export_dir, f"applications_{timestamp}.json")
                self.export_to_json(applications, filename)

            self.app.sub_title = f"Data exported to {filename}"
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Export error: {str(e)}"

    def export_to_csv(self, applications, filename):
        """Export data to CSV format."""
        if not applications:
            raise ValueError("No data to export")

        # Get all possible field names from all applications
        fieldnames = set()
        for app in applications:
            fieldnames.update(app.keys())

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(fieldnames))
            writer.writeheader()
            writer.writerows(applications)

    def export_to_json(self, applications, filename):
        """Export data to JSON format."""
        import json

        if not applications:
            raise ValueError("No data to export")

        with open(filename, "w", encoding="utf-8") as jsonfile:
            json.dump(applications, jsonfile, indent=2)
