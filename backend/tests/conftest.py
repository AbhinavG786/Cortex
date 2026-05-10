import pytest
from app import create_app, db

@pytest.fixture
def app():
    """Creates a fresh instance of the app for testing."""
    app = create_app()
    
    # Override configuration for testing
    app.config.update({
        "TESTING": True,
        # Use an in-memory database for instant, isolated tests
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    # Create the test database tables
    with app.app_context():
        db.create_all()
        yield app
        # Drop everything after the test completes
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Provides a simulated web client to send HTTP requests to the app."""
    return app.test_client()