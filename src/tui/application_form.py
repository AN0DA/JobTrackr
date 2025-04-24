from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Input, Button, Label, TextArea, Select, Static
from datetime import datetime

from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService


class TagInput(Static):
    """Custom widget for handling tags."""
    
    def __init__(self, id=None, tags=None):
        super().__init__(id=id)
        self.tags = tags or []
    
    def compose(self) -> ComposeResult:
        """Compose the tag input widget."""
        yield Input(placeholder="Type a tag and press Enter", id=f"{self.id}-input")
        yield Horizontal(id=f"{self.id}-tags")
        yield Button("Add Tag", id=f"{self.id}-add")
    
    def on_mount(self):
        """Initialize tags when mounted."""
        self._refresh_tags()
    
    def on_input_submitted(self, event: Input.Submitted):
        """Handle Enter key to add a tag."""
        if event.input.id == f"{self.id}-input":
            self._add_tag(event.value)
            event.input.value = ""
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle Add Tag button press."""
        if event.button.id == f"{self.id}-add":
            input = self.query_one(f"#{self.id}-input", Input)
            if input.value.strip():
                self._add_tag(input.value)
                input.value = ""
    
    def _add_tag(self, tag):
        """Add a tag to the list."""
        tag = tag.strip()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self._refresh_tags()
    
    def _refresh_tags(self):
        """Refresh the tags display."""
        tags_container = self.query_one(f"#{self.id}-tags", Horizontal)
        tags_container.remove_children()
        
        for tag in self.tags:
            # Create a mini button for each tag
            tag_btn = Button(f"{tag} ×", classes="tag-button", id=f"tag-{len(tags_container.children)}")
            tags_container.mount(tag_btn)
    
    def get_tags(self):
        """Get the current list of tags."""
        return self.tags
    
    def set_tags(self, tags):
        """Set tags from a list."""
        self.tags = list(tags) if tags else []
        if self.is_mounted:
            self._refresh_tags()


class ApplicationForm(Screen):
    """Form for creating or editing a job application."""

    def __init__(self, app_id: str = None, readonly: bool = False):
        """Initialize the form.

        Args:
            app_id: If provided, the form will edit the existing application
            readonly: If True, the form will be displayed in read-only mode
        """
        super().__init__()
        self.app_id = app_id
        self.readonly = readonly
        self.companies = []

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(id="app-form"):
            yield Label(
                "View Application" if self.readonly else
                "Edit Application" if self.app_id else
                "New Application",
                id="form-title"
            )

            # Use ScrollableContainer to ensure all fields are accessible
            with ScrollableContainer(id="form-container"):
                with Vertical(id="form-fields"):
                    # Essential fields section
                    yield Label("Essential Information", classes="section-header")
                    
                    yield Label("Job Title *", classes="field-label")
                    yield Input(id="job-title", disabled=self.readonly)

                    yield Label("Company *", classes="field-label")
                    with Vertical(id="company-field"):
                        yield Select([], id="company-select", disabled=self.readonly)
                        if not self.readonly:
                            yield Button("+ New Company", id="new-company", variant="primary")

                    yield Label("Position *", classes="field-label")
                    yield Input(id="position", disabled=self.readonly)

                    yield Label("Status *", classes="field-label")
                    yield Select(
                        [(status, status) for status in [
                            "SAVED", "APPLIED", "PHONE_SCREEN", "INTERVIEW",
                            "TECHNICAL_INTERVIEW", "OFFER", "ACCEPTED", "REJECTED", "WITHDRAWN"
                        ]],
                        id="status",
                        disabled=self.readonly
                    )

                    yield Label("Applied Date *", classes="field-label")
                    yield Input(
                        id="applied-date",
                        placeholder="YYYY-MM-DD",
                        disabled=self.readonly,
                        value=datetime.now().strftime("%Y-%m-%d") if not self.app_id and not self.readonly else ""
                    )
                    
                    # Additional details section
                    yield Label("Additional Details", classes="section-header")

                    yield Label("Location", classes="field-label")
                    yield Input(id="location", placeholder="City, State or Remote", disabled=self.readonly)

                    yield Label("Salary", classes="field-label")
                    yield Input(id="salary", placeholder="e.g. $100,000/year", disabled=self.readonly)

                    yield Label("Link", classes="field-label")
                    yield Input(id="link", placeholder="https://...", disabled=self.readonly)

                    # Description and notes section
                    yield Label("Content", classes="section-header")
                    
                    yield Label("Description", classes="field-label")
                    yield TextArea(id="description", disabled=self.readonly)

                    yield Label("Notes", classes="field-label")
                    yield TextArea(id="notes", disabled=self.readonly)

                    yield Label("Tags", classes="field-label")
                    yield TagInput(id="tag-input")
            
            yield Label("* Required fields", id="required-fields-note")

            with Horizontal(id="form-actions"):
                if not self.readonly:
                    yield Button("Save", variant="primary", id="save-app")
                yield Button("Close", id="close-form")

    def on_mount(self) -> None:
        """Load data when the form is mounted."""
        self.load_companies()
        if self.app_id:
            self.load_application()
    
    # def on_resize(self) -> None:
    #     """Handle resize events by adjusting the form container."""
    #     form_container = self.query_one("#form-container", ScrollableContainer)
    #     form_actions = self.query_one("#form-actions", Horizontal)
    #
    #     # Make sure the form container adjusts to leave space for actions
    #     # This helps on smaller screens
    #     action_height = form_actions.region.height
    #     form_container.styles.height = f"100vh - {action_height}px"

    def load_companies(self) -> None:
        """Load companies for the dropdown."""
        try:
            service = CompanyService()
            self.companies = service.get_companies()

            company_select = self.query_one("#company-select", Select)
            company_select.set_options([
                (company["name"], str(company["id"])) for company in self.companies
            ])
            
            # Set default selection for new applications
            if not self.app_id and self.companies:
                company_select.value = str(self.companies[0]["id"])
            
        except Exception as e:
            self.app.sub_title = f"Error loading companies: {str(e)}"

    def load_application(self) -> None:
        """Load application data for editing."""
        try:
            service = ApplicationService()
            app_data = service.get_application(int(self.app_id))
            
            if not app_data:
                self.app.sub_title = f"Application {self.app_id} not found"
                return

            # Populate the form fields
            self.query_one("#job-title", Input).value = app_data["job_title"]
            self.query_one("#position", Input).value = app_data["position"]

            if app_data.get("location"):
                self.query_one("#location", Input).value = app_data["location"]

            if app_data.get("salary"):
                self.query_one("#salary", Input).value = app_data["salary"]

            self.query_one("#status", Select).value = app_data["status"]

            # Format the date
            applied_date = datetime.fromisoformat(app_data["applied_date"]).strftime("%Y-%m-%d")
            self.query_one("#applied-date", Input).value = applied_date

            if app_data.get("link"):
                self.query_one("#link", Input).value = app_data["link"]

            if app_data.get("description"):
                self.query_one("#description", TextArea).text = app_data["description"]

            if app_data.get("notes"):
                self.query_one("#notes", TextArea).text = app_data["notes"]

            # Set company if available
            if app_data.get("company"):
                self.query_one("#company-select", Select).value = str(app_data["company"]["id"])
                
            # Handle tags
            if app_data.get("tags"):
                tag_input = self.query_one("#tag-input", TagInput)
                tag_input.set_tags(app_data["tags"])

        except Exception as e:
            self.app.sub_title = f"Error loading application: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "new-company":
            from src.tui.company_form import CompanyForm
            self.app.push_screen(CompanyForm(on_saved=self.load_companies))

        elif button_id == "save-app":
            self.save_application()

        elif button_id == "close-form":
            self.app.pop_screen()

    def save_application(self) -> None:
        """Save the application data."""
        try:
            # Get values from form
            job_title = self.query_one("#job-title", Input).value
            company_id = self.query_one("#company-select", Select).value
            position = self.query_one("#position", Input).value
            location = self.query_one("#location", Input).value
            salary = self.query_one("#salary", Input).value
            status = self.query_one("#status", Select).value
            applied_date = self.query_one("#applied-date", Input).value
            link = self.query_one("#link", Input).value
            description = self.query_one("#description", TextArea).text
            notes = self.query_one("#notes", TextArea).text
            tags = self.query_one("#tag-input", TagInput).get_tags()

            # Validate required fields
            if not job_title:
                self.app.sub_title = "Job title is required"
                return

            if not company_id:
                self.app.sub_title = "Company is required"
                return

            if not position:
                self.app.sub_title = "Position is required"
                return

            if not status:
                self.app.sub_title = "Status is required"
                return

            if not applied_date:
                self.app.sub_title = "Applied date is required"
                return

            # Prepare data
            app_data = {
                "job_title": job_title,
                "company_id": int(company_id),
                "position": position,
                "location": location or None,
                "salary": salary or None,
                "status": status,
                "applied_date": applied_date,
                "link": link or None,
                "description": description or None,
                "notes": notes or None,
                "tags": tags or None
            }

            service = ApplicationService()

            if self.app_id:
                # Update existing application
                result = service.update_application(int(self.app_id), app_data)
                self.app.sub_title = "Application updated successfully"
            else:
                # Create new application
                result = service.create_application(app_data)
                self.app.sub_title = "Application created successfully"

            # Return to the previous screen
            self.app.pop_screen()

            # Refresh the applications list if it's visible
            from src.tui.applications import ApplicationsList
            app_list = self.app.query_one(ApplicationsList, default=None)
            if app_list:
                app_list.load_applications()

        except Exception as e:
            self.app.sub_title = f"Error saving application: {str(e)}"
