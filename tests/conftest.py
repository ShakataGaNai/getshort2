import os
import pytest
import tempfile
import uuid
import datetime
from app import create_app, db
from app.models import User, ShortURL

# Create different data for each test to avoid conflicts
@pytest.fixture(scope="function")
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app for testing with in-memory SQLite
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain',
    })
    
    # Add current year to templates for base.html
    @test_app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}

    # Create the database but don't load test data yet
    with test_app.app_context():
        db.create_all()
    
    # Return the app for testing
    yield test_app
    
    # Clean up after the test
    with test_app.app_context():
        db.session.remove()
        db.drop_all()
    
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

@pytest.fixture
def test_user(app):
    """Create a test user for tests."""
    with app.app_context():
        # Use unique values to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            github_id=int(unique_id, 16) % 100000  # Convert part of UUID to int
        )
        db.session.add(user)
        db.session.commit()
        
        # Get the ID before the session closes
        user_id = user.id
        
        # Return fresh user object from the database using Session.get (avoiding Query.get deprecation)
        return db.session.get(User, user_id)

@pytest.fixture
def test_url(app, test_user):
    """Create a test short URL for tests."""
    with app.app_context():
        # Use unique short code
        unique_id = str(uuid.uuid4())[:6]
        url = ShortURL(
            short_code=f'test_{unique_id}',
            target_url='https://example.com',
            user_id=test_user.id
        )
        db.session.add(url)
        db.session.commit()
        
        # Get the ID before the session closes
        url_id = url.id
        
        # Return fresh URL object from the database using Session.get (avoiding Query.get deprecation)
        return db.session.get(ShortURL, url_id)