from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService


class ApplicationForm(Screen):
    """Form for creating or editing a job application with multiple pages."""

    def __init__(self, app_id=None, readonly=False):
        super().__init__()
        self.app_id = app_id
        self.readonly = readonly
        self.companies = []
        self.current_page = 1
        self.total_pages = 3
        self.application_data = {}

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(id="app-form"):
            yield Label(
                "View Application" if self.readonly else "Edit Application" if self.app_id else "New Application",
                id="form-title",
            )

            # Page indicator
            yield Static(f"Page {self.current_page} of {self.total_pages}", id="page-indicator")

            # Page 1: Essential Information
            with Container(id="page-1", classes="form-page"):
                with Vertical(id="essential-fields"):
                    yield Label("Job Title *", classes="field-label")
                    yield Input(id="job-title", disabled=self.readonly)

                    yield Label("Company *", classes="field-label")
                    with Horizontal(id="company-field"):
                        yield Select([], id="company-select", disabled=self.readonly)
                        if not self.readonly:
                            yield Button("+ New Company", id="new-company", variant="primary")

                    yield Label("Position *", classes="field-label")
                    yield Input(id="position", disabled=self.readonly)

                    yield Label("Status *", classes="field-label")
                    yield Select(
                        [
                            (status, status)
                            for status in [
                                "SAVED",
                                "APPLIED",
                                "PHONE_SCREEN",
                                "INTERVIEW",
                                "TECHNICAL_INTERVIEW",
                                "OFFER",
                                "ACCEPTED",
                                "REJECTED",
                                "WITHDRAWN",
                            ]
                        ],
                        id="status",
                        disabled=self.readonly,
                    )

                    yield Label("Applied Date *", classes="field-label")
                    yield Input(
                        id="applied-date",
                        placeholder="YYYY-MM-DD",
                        disabled=self.readonly,
                        value=datetime.now().strftime("%Y-%m-%d") if not self.app_id and not self.readonly else "",
                    )

            # Page 2: Additional Details
            with Container(id="page-2", classes="form-page hidden"):
                with Vertical(id="details-fields"):
                    yield Label("Location", classes="field-label")
                    yield Input(
                        id="location",
                        placeholder="City, State or Remote",
                        disabled=self.readonly,
                    )

                    yield Label("Salary", classes="field-label")
                    yield Input(
                        id="salary",
                        placeholder="e.g. $100,000/year",
                        disabled=self.readonly,
                    )

                    yield Label("Link", classes="field-label")
                    yield Input(id="link", placeholder="https://...", disabled=self.readonly)

            # Page 3: Content
            with Container(id="page-3", classes="form-page hidden"):
                with Vertical(id="content-fields"):
                    yield Label("Job Description", classes="field-label")
                    yield TextArea(id="description", disabled=self.readonly)

                    yield Label("Notes", classes="field-label")
                    yield TextArea(id="notes", disabled=self.readonly)

            yield Label("* Required fields", id="required-fields-note")

            # Page navigation buttons
            with Horizontal(id="page-navigation"):
                yield Button("← Previous", id="prev-page", disabled=True)
                yield Button("Next →", id="next-page")

            with Horizontal(id="form-actions"):
                if not self.readonly:
                    yield Button("Save", variant="primary", id="save-app")
                yield Button("Close", id="close-form")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "new-company":
            from src.tui.tabs.companies.company_form import CompanyForm

            self.app.push_screen(CompanyForm(on_saved=self.load_companies))

        elif button_id == "next-page":
            self.navigate_to_page(self.current_page + 1)

        elif button_id == "prev-page":
            self.navigate_to_page(self.current_page - 1)

        elif button_id == "save-app":
            self.save_application()

        elif button_id == "close-form":
            self.app.pop_screen()

    def store_current_field_values(self) -> None:
        """Store the current form field values in application_data."""
        try:
            # Page 1: Essential Information
            if self.current_page == 1:
                self.application_data["job_title"] = self.query_one("#job-title", Input).value
                self.application_data["company_id"] = self.query_one("#company-select", Select).value
                self.application_data["position"] = self.query_one("#position", Input).value
                self.application_data["status"] = self.query_one("#status", Select).value
                self.application_data["applied_date"] = self.query_one("#applied-date", Input).value
            
            # Page 2: Additional Details
            elif self.current_page == 2:
                self.application_data["location"] = self.query_one("#location", Input).value
                self.application_data["salary"] = self.query_one("#salary", Input).value
                self.application_data["link"] = self.query_one("#link", Input).value
            
            # Page 3: Content
            elif self.current_page == 3:
                self.application_data["description"] = self.query_one("#description", TextArea).text
                self.application_data["notes"] = self.query_one("#notes", TextArea).text
        except Exception as e:
            self.app.sub_title = f"Error storing field values: {str(e)}"

    def navigate_to_page(self, page_number):
        """Navigate to the specified page of the form."""
        if page_number < 1 or page_number > self.total_pages:
            return

        # Store current field values if not in readonly mode
        if not self.readonly:
            self.store_current_field_values()

        # Hide all pages
        for i in range(1, self.total_pages + 1):
            page = self.query_one(f"#page-{i}", Container)
            if i == page_number:
                page.remove_class("hidden")
            else:
                page.add_class("hidden")

        # Update current page
        self.current_page = page_number

        # Update page indicator
        self.query_one("#page-indicator", Static).update(f"Page {self.current_page} of {self.total_pages}")

        # Update button states
        prev_button = self.query_one("#prev-page", Button)
        next_button = self.query_one("#next-page", Button)

        prev_button.disabled = page_number == 1
        next_button.disabled = page_number == self.total_pages

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
            company_select.set_options([(company["name"], str(company["id"])) for company in self.companies])

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

        except Exception as e:
            self.app.sub_title = f"Error loading application: {str(e)}"

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
            }

            service = ApplicationService()

            if self.app_id:
                # Update existing application
                service.update_application(int(self.app_id), app_data)
                self.app.sub_title = "Application updated successfully"
            else:
                # Create new application
                service.create_application(app_data)
                self.app.sub_title = "Application created successfully"

            # Return to the previous screen
            self.app.pop_screen()

            # Refresh the applications list if it's visible
            from src.tui.tabs.applications.applications import ApplicationsList

            app_list = self.app.query_one(ApplicationsList)
            if app_list:
                app_list.load_applications()

        except Exception as e:
            self.app.sub_title = f"Error saving application: {str(e)}"
