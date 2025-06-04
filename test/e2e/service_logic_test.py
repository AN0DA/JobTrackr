import pytest
from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService
from src.services.contact_service import ContactService
from src.services.interaction_service import InteractionService
from datetime import datetime
from src.db.database import get_session

def test_application_crud():
    service = ApplicationService()
    # Create
    data = {
        "job_title": "Dev",
        "position": "Engineer",
        "status": "APPLIED",
        "applied_date": datetime.now().isoformat(),
        "company_id": None,
    }
    app = service.create(data)
    assert app["job_title"] == "Dev"
    # Read
    got = service.get(app["id"])
    assert got["job_title"] == "Dev"
    # Update
    updated = service.update(app["id"], {"job_title": "Dev2"})
    assert updated["job_title"] == "Dev2"
    # Delete
    assert service.delete(app["id"])
    assert service.get(app["id"]) is None

def test_company_crud():
    service = CompanyService()
    # Create
    company = service.create({"name": "Acme"})
    assert company["name"] == "Acme"
    # Read
    got = service.get(company["id"])
    assert got["name"] == "Acme"
    # Update
    updated = service.update(company["id"], {"name": "Acme2"})
    assert updated["name"] == "Acme2"
    # Delete
    assert service.delete(company["id"])
    assert service.get(company["id"]) is None

def test_contact_crud():
    service = ContactService()
    # Create
    contact = service.create({"name": "Alice"})
    assert contact["name"] == "Alice"
    # Read
    got = service.get(contact["id"])
    assert got["name"] == "Alice"
    # Update
    updated = service.update(contact["id"], {"name": "Bob"})
    assert updated["name"] == "Bob"
    # Delete
    assert service.delete(contact["id"])
    assert service.get(contact["id"]) is None

def test_interaction_crud():
    # Need a contact and application first
    app_service = ApplicationService()
    contact_service = ContactService()
    app = app_service.create({
        "job_title": "Dev",
        "position": "Engineer",
        "status": "APPLIED",
        "applied_date": datetime.now().isoformat(),
        "company_id": None,
    })
    contact = contact_service.create({"name": "Alice"})
    service = InteractionService()
    data = {
        "contact_id": contact["id"],
        "application_id": app["id"],
        "interaction_type": "EMAIL",
        "date": datetime.now().isoformat(),
        "subject": "Intro",
        "notes": "Test note",
    }
    interaction = service.create(data)
    assert interaction["interaction_type"] == "EMAIL"
    # Read
    got = service.get(interaction["id"])
    assert got["subject"] == "Intro"
    # Update
    updated = service.update(interaction["id"], {"subject": "Followup"})
    assert updated["subject"] == "Followup"
    # Delete
    assert service.delete(interaction["id"])
    assert service.get(interaction["id"]) is None

def test_company_search_and_edge_cases():
    service = CompanyService()
    # Create companies
    service.create({"name": "Acme"})
    service.create({"name": "Beta"})
    # Get all and filter by name
    all_companies = service.get_all()
    acme = [c for c in all_companies if c["name"] == "Acme"]
    assert acme
    # Update non-existent
    with pytest.raises(ValueError):
        service.update(9999, {"name": "Ghost"})
    # Delete non-existent
    assert service.delete(9999) is False

def test_contact_search_and_edge_cases():
    service = ContactService()
    service.create({"name": "Alice"})
    service.create({"name": "Bob"})
    # Search by name (positional argument)
    results = service.search_contacts("Alice")
    assert any("Alice" in c["name"] for c in results)
    # Get all
    all_contacts = service.get_all()
    assert len(all_contacts) >= 2
    # Update non-existent
    with pytest.raises(ValueError):
        service.update(9999, {"name": "Ghost"})
    # Delete non-existent
    assert service.delete(9999) is False

def test_application_status_counts_and_recent():
    from src.db.database import get_session
    service = ApplicationService()
    service.create({
        "job_title": "Job1",
        "position": "P1",
        "status": "APPLIED",
        "applied_date": datetime.now().isoformat(),
        "company_id": None,
    })
    service.create({
        "job_title": "Job2",
        "position": "P2",
        "status": "INTERVIEW",
        "applied_date": datetime.now().isoformat(),
        "company_id": None,
    })
    session = get_session()
    try:
        # Status counts
        counts = service.get_status_counts(session)
        assert any(c["status"] == "APPLIED" for c in counts)
        # Recent applications
        recent = service.get_recent_applications(session)
        assert len(recent) >= 2
        # Dashboard stats
        stats = service.get_dashboard_stats(session)
        assert "applications_by_status" in stats and "recent_applications" in stats
    finally:
        session.close()

def test_db_operation_decorator_handles_exceptions():
    from src.utils.decorators import db_operation
    class DummyService:
        @db_operation
        def fail(self, session=None):
            raise ValueError("fail!")
    service = DummyService()
    with pytest.raises(ValueError):
        service.fail() 