# JobTrackr

**JobTrackr** is a modern, feature-rich job application tracking tool with a graphical user interface (GUI) built using PyQt6. It helps you organize, track, and analyze your job search process, including applications, companies, contacts, and interactions.

---

## Features

- **Track Job Applications:** Store details about each job application, including position, company, status, salary, notes, and more.
- **Company Management:** Manage companies, their details, and relationships between companies (e.g., parent, subsidiary, recruiter).
- **Contact Management:** Keep track of contacts, their roles, and their associations with companies and applications.
- **Interaction Logging:** Record interviews, calls, emails, and other interactions related to your job search.
- **Status History:** Automatically log changes to application status and maintain a full change history.
- **Dashboard:** Visual overview of your job search, including statistics and recent activity.
- **Search & Filtering:** Powerful search and filtering across applications, companies, and contacts.
- **Settings & Customization:** Configure database location, theme, and other preferences.
- **Data Persistence:** All data is stored locally using SQLite via SQLAlchemy ORM.
- **Cross-Platform:** Runs on Windows, macOS, and Linux.

---

## Installation

### Prerequisites

- **Python 3.13+** (see your Python version with `python --version`)
- [uv](https://github.com/astral-sh/uv)

### Install dependencies

```bash
uv sync
```


### Database Migration

On first run, JobTrackr will automatically create and migrate the database.

---

## Usage

### Run the Application

```bash
uv run python -m src.main
```

This will launch the JobTrackr GUI.

### Project Structure

- `src/` — Main application source code
  - `db/` — Database models and migration logic
  - `gui/` — PyQt6 GUI components, dialogs, and tabs
  - `services/` — Business logic and data access services
  - `utils/` — Utility functions (logging, decorators, etc.)
- `test/` — Automated tests (unit and end-to-end)
- `alembic/` — Database migration scripts

### Main Features in the UI

- **Dashboard:** Overview of your job search, stats, and recent applications.
- **Applications Tab:** Add, edit, and view job applications.
- **Companies Tab:** Manage companies and their relationships.
- **Contacts Tab:** Manage contacts and their associations.
- **Search:** Quickly find applications, companies, or contacts.
- **Settings:** Configure preferences and database location.

---

## Development

### Lint, Type Check, and Test

```bash
make lint      # Format and lint code
make mypy      # Type checking
make test      # Run tests with coverage
```

### Database Migrations

```bash
make migrate   # Apply migrations
make revision  # Create a new migration (will prompt for a message)
```

### Build Standalone Executable

```bash
make pyinstaller
```

---

## Configuration & Data

- **Settings:** Stored in `~/.jobtrackr/settings.json`
- **Database:** Default location is `~/jobtrackr_data/jobtrackr.db`
- **Logs:** Written to `~/.jobtrackr/logs/`

---

## Contributing

Contributions are welcome! Please open issues or pull requests on [GitHub](https://github.com/AN0DA/JobTrackr).

---

## License

This project is licensed under the MIT License.

---

## Author

Mikołaj Kaczmarek  
[12432719+AN0DA@users.noreply.github.com](mailto:12432719+AN0DA@users.noreply.github.com)

---

**JobTrackr** — Take control of your job search!
