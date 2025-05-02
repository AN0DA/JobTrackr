from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import networkx as nx

from src.gui.components.data_table import DataTable
from src.gui.dialogs.application_detail import ApplicationDetailDialog
from src.gui.dialogs.company_relationship_form import CompanyRelationshipForm
from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CompanyDetailDialog(QDialog):
    """Dialog for viewing company details."""

    def __init__(self, parent=None, company_id=None) -> None:
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.company_id = company_id
        self.company_data = None

        self.setWindowTitle("Company Details")
        self.resize(700, 500)

        self._init_ui()

        # Load data
        if self.company_id:
            self.load_company_data()

    def _init_ui(self) -> None:
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Header section with company info and buttons
        header_layout = QHBoxLayout()

        # Company identity section
        self.identity_layout = QVBoxLayout()
        self.company_name = QLabel("")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.company_name.setFont(name_font)

        self.company_type = QLabel("")
        self.identity_layout.addWidget(self.company_name)
        self.identity_layout.addWidget(self.company_type)

        # Header actions
        actions_layout = QVBoxLayout()
        self.edit_button = QPushButton("Edit Company")
        self.edit_button.clicked.connect(self.on_edit_company)

        self.add_relationship_button = QPushButton("Add Relationship")
        self.add_relationship_button.clicked.connect(self.on_add_relationship)

        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.add_relationship_button)

        header_layout.addLayout(self.identity_layout, 2)
        header_layout.addLayout(actions_layout, 1)
        layout.addLayout(header_layout)

        # Tab widget for different sections
        self.tabs = QTabWidget()

        # Tab 1: Overview
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)

        # Company details
        info_form = QFormLayout()
        self.industry_label = QLabel("")
        info_form.addRow("Industry:", self.industry_label)

        self.website_label = QLabel("")
        info_form.addRow("Website:", self.website_label)

        self.size_label = QLabel("")
        info_form.addRow("Size:", self.size_label)

        overview_layout.addLayout(info_form)

        # Notes section
        overview_layout.addWidget(QLabel("Notes:"))
        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        overview_layout.addWidget(self.notes_display)

        # Tab 2: Relationships
        relationships_tab = QWidget()
        relationships_layout = QVBoxLayout(relationships_tab)

        relationships_layout.addWidget(QLabel("Company Relationships"))

        # Relationships table
        self.relationships_table = DataTable(0, ["Company", "Type", "Relationship", "Direction", "Actions"])
        self.relationships_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.relationships_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        relationships_layout.addWidget(self.relationships_table)

        # Collapsible visualization section
        self.visualization_container = QWidget()
        visualization_layout = QVBoxLayout(self.visualization_container)
        visualization_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with toggle button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        viz_label = QLabel("Relationship Visualization:")
        viz_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(viz_label)
        
        self.toggle_viz_button = QPushButton("Show")
        self.toggle_viz_button.setMaximumWidth(100)
        self.toggle_viz_button.clicked.connect(self.toggle_visualization)
        header_layout.addWidget(self.toggle_viz_button)
        
        visualization_layout.addLayout(header_layout)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        visualization_layout.addWidget(line)
        
        # Visualization content
        self.viz_content = QWidget()
        self.viz_content.setVisible(False)  # Initially hidden
        viz_content_layout = QVBoxLayout(self.viz_content)
        viz_content_layout.setContentsMargins(0, 10, 0, 0)
        
        # Create figure and canvas for the network graph
        self.figure = plt.figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)
        viz_content_layout.addWidget(self.canvas)
        
        visualization_layout.addWidget(self.viz_content)
        relationships_layout.addWidget(self.visualization_container)

        # Tab 3: Applications
        applications_tab = QWidget()
        applications_layout = QVBoxLayout(applications_tab)

        applications_layout.addWidget(QLabel("Job Applications with this Company"))

        # Applications table
        self.applications_table = DataTable(0, ["ID", "Job Title", "Position", "Status", "Applied Date"])
        self.applications_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.applications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.applications_table.doubleClicked.connect(self.on_application_double_clicked)
        applications_layout.addWidget(self.applications_table)

        # Add tabs to widget
        self.tabs.addTab(overview_tab, "Overview")
        self.tabs.addTab(relationships_tab, "Relationships")
        self.tabs.addTab(applications_tab, "Applications")

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_button)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def toggle_visualization(self):
        """Toggle the visibility of the visualization panel."""
        is_visible = self.viz_content.isVisible()
        self.viz_content.setVisible(not is_visible)
        
        # Update button text
        if is_visible:
            self.toggle_viz_button.setText("Show")
            # Restore original size
            self.resize(700, 500)
        else:
            self.toggle_viz_button.setText("Hide")
            # Expand dialog size when showing visualization
            self.resize(800, 700)
            
            # Make sure visualization is up to date
            if hasattr(self, 'last_relationships') and self.last_relationships:
                self._generate_network_visualization(self.last_relationships)

    def load_company_data(self) -> None:
        """Load all company data and populate the UI."""
        try:
            # Load company details
            service = CompanyService()
            self.company_data = service.get(self.company_id)

            if not self.company_data:
                if self.main_window:
                    self.main_window.show_status_message(f"Company {self.company_id} not found")
                return

            # Update header
            self.company_name.setText(self.company_data.get("name", "Unknown"))

            # Make sure company type is a string
            company_type = self.company_data.get("type", "")
            if company_type is None:
                company_type = "DIRECT_EMPLOYER"
            self.company_type.setText(f"Type: {company_type}")

            # Update overview fields - ensure we always use strings for display
            industry = self.company_data.get("industry", "")
            if industry is None or industry == "":
                industry = "Not specified"
            self.industry_label.setText(industry)

            website = self.company_data.get("website", "")
            if website is None or website == "":
                website = "No website provided"
            self.website_label.setText(website)

            size = self.company_data.get("size", "")
            if size is None or size == "":
                size = "Not specified"
            self.size_label.setText(size)

            # Update notes
            notes = self.company_data.get("notes", "")
            if notes is None or notes == "":
                notes = "No notes available."
            self.notes_display.setText(notes)

            # Load relationships
            self.load_relationships()

            # Load applications
            self.load_applications()

            if self.main_window:
                self.main_window.show_status_message(f"Viewing company: {self.company_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error loading company data: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading company data: {str(e)}")

    def load_relationships(self) -> None:
        """Load company relationships."""
        try:
            service = CompanyService()
            relationships = service.get_related_companies(self.company_id)
            self.last_relationships = relationships  # Store for visualization refresh

            self.relationships_table.setRowCount(0)

            if not relationships:
                self.relationships_table.insertRow(0)
                self.relationships_table.setItem(0, 0, QTableWidgetItem("No relationships found"))
                self.relationships_table.setItem(0, 1, QTableWidgetItem(""))
                self.relationships_table.setItem(0, 2, QTableWidgetItem(""))
                self.relationships_table.setItem(0, 3, QTableWidgetItem(""))
                self.relationships_table.setItem(0, 4, QTableWidgetItem(""))
                
                # Clear the visualization
                self.figure.clear()
                self.canvas.draw()
                return

            for i, rel in enumerate(relationships):
                self.relationships_table.insertRow(i)

                direction = "→" if rel["direction"] == "outgoing" else "←"

                self.relationships_table.setItem(i, 0, QTableWidgetItem(rel["company_name"]))
                self.relationships_table.setItem(i, 1, QTableWidgetItem(rel.get("company_type", "")))
                self.relationships_table.setItem(i, 2, QTableWidgetItem(rel["relationship_type"]))
                self.relationships_table.setItem(i, 3, QTableWidgetItem(direction))

                # Create action buttons cell
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                # Edit button
                edit_btn = QPushButton("Edit")
                edit_btn.setMaximumWidth(60)
                edit_btn.clicked.connect(lambda checked=False, row=i, rel_id=rel.get("relationship_id"): 
                                         self.on_edit_relationship(rel_id))
                actions_layout.addWidget(edit_btn)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setMaximumWidth(60)
                delete_btn.clicked.connect(lambda checked=False, row=i, rel_id=rel.get("relationship_id"): 
                                          self.on_delete_relationship(rel_id))
                actions_layout.addWidget(delete_btn)
                
                actions_layout.addStretch()
                actions_widget.setLayout(actions_layout)
                
                # Set the custom widget in the table cell
                self.relationships_table.setCellWidget(i, 4, actions_widget)
            
            # Generate network visualization if panel is visible
            if self.viz_content.isVisible():
                self._generate_network_visualization(relationships)

        except Exception as e:
            logger.error(f"Error loading relationships: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading relationships: {str(e)}")

    def _generate_network_visualization(self, relationships):
        """Generate a network graph visualization of company relationships."""
        try:
            # Clear previous figure
            self.figure.clear()
            
            # Create directed graph
            G = nx.DiGraph()
            
            # Add focal company node
            company_name = self.company_data.get("name", f"Company {self.company_id}")
            G.add_node(company_name)
            
            # Add edges for relationships
            edges = []
            edge_labels = {}
            
            for rel in relationships:
                other_company = rel["company_name"]
                rel_type = rel["relationship_type"]
                direction = rel["direction"]
                
                # Add the other company node
                G.add_node(other_company)
                
                # Add directed edge based on relationship direction
                if direction == "outgoing":
                    G.add_edge(company_name, other_company)
                    edge_labels[(company_name, other_company)] = rel_type
                else:
                    G.add_edge(other_company, company_name)
                    edge_labels[(other_company, company_name)] = rel_type
            
            # Create the plot
            ax = self.figure.add_subplot(111)
            
            # Generate positions for the nodes
            pos = nx.spring_layout(G)
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue', ax=ax)
            nx.draw_networkx_edges(G, pos, width=2, edge_color='gray', ax=ax, 
                                  arrowsize=20, connectionstyle='arc3,rad=0.1')
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)
            
            # Remove axis
            ax.axis('off')
            
            # Update the canvas
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error generating network visualization: {e}", exc_info=True)
            # Clear the figure in case of error
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Visualization error", ha='center', va='center')
            ax.axis('off')
            self.canvas.draw()

    def load_applications(self) -> None:
        """Load job applications for this company."""
        try:
            app_service = ApplicationService()
            applications = app_service.get_applications_by_company(self.company_id)

            self.applications_table.setRowCount(0)

            if not applications:
                self.applications_table.insertRow(0)
                self.applications_table.setItem(0, 0, QTableWidgetItem("No applications found"))
                self.applications_table.setItem(0, 1, QTableWidgetItem(""))
                self.applications_table.setItem(0, 2, QTableWidgetItem(""))
                self.applications_table.setItem(0, 3, QTableWidgetItem(""))
                self.applications_table.setItem(0, 4, QTableWidgetItem(""))
                return

            for i, app in enumerate(applications):
                self.applications_table.insertRow(i)

                self.applications_table.setItem(i, 0, QTableWidgetItem(str(app["id"])))
                self.applications_table.setItem(i, 1, QTableWidgetItem(app["job_title"]))
                self.applications_table.setItem(i, 2, QTableWidgetItem(app["position"]))
                self.applications_table.setItem(i, 3, QTableWidgetItem(app["status"]))

                # Format date
                date_str = app["applied_date"].split("T")[0]
                self.applications_table.setItem(i, 4, QTableWidgetItem(date_str))

        except Exception as e:
            logger.error(f"Error loading applications: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading applications: {str(e)}")

    @pyqtSlot()
    def on_edit_company(self) -> None:
        """Open dialog to edit the company."""
        from src.gui.dialogs.company_form import CompanyForm

        dialog = CompanyForm(self, self.company_id)
        if dialog.exec():
            self.load_company_data()

    @pyqtSlot()
    def on_add_relationship(self) -> None:
        """Open dialog to add a company relationship."""
        dialog = CompanyRelationshipForm(self, self.company_id)
        if dialog.exec():
            self.load_relationships()

    @pyqtSlot()
    def on_application_double_clicked(self, index) -> None:
        """Open application details when double clicked."""
        if self.applications_table.item(index.row(), 0).text() == "No applications found":
            return

        app_id = int(self.applications_table.item(index.row(), 0).text())
        dialog = ApplicationDetailDialog(self, app_id)
        dialog.exec()
        # Refresh applications in case there were changes
        self.load_applications()

    @pyqtSlot(int)
    def on_edit_relationship(self, relationship_id):
        """Open dialog to edit a company relationship."""
        dialog = CompanyRelationshipForm(self, self.company_id, relationship_id)
        if dialog.exec():
            self.load_relationships()

    @pyqtSlot(int)
    def on_delete_relationship(self, relationship_id):
        """Delete a company relationship."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, 
            'Delete Relationship',
            'Are you sure you want to delete this relationship?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = CompanyService()
                service.delete_relationship(relationship_id)

                self.main_window.show_status_message("Relationship deleted successfully")
                self.load_relationships()
            except Exception as e:
                logger.error(f"Error deleting relationship: {e}", exc_info=True)
                if self.main_window:
                    self.main_window.show_status_message(f"Error deleting relationship: {str(e)}")
