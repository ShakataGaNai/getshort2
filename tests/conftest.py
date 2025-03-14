import os
import pytest
import tempfile
from app import create_app, db
from app.models import User, ShortURL

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app for testing
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain',
    })

    # Create the database and load test data
    with app.app_context():
        db.create_all()
        _create_test_data()
    
    # Return the app for testing
    yield app
    
    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

def _create_test_data():
    """Create some test data for the tests."""
    # Create test user
    test_user = User(
        username='testuser',
        email='test@example.com',
        github_id=12345
    )
    db.session.add(test_user)
    db.session.commit()
    
    # Create test short URL
    test_url = ShortURL(
        short_code='test123',
        target_url='https://example.com',
        user_id=test_user.id
    )
    db.session.add(test_url)
    db.session.commit()