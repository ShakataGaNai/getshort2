from app import db
from app.models import User, ShortURL, Visit, generate_short_code

def test_generate_short_code():
    """Test that generate_short_code returns a string of the expected length."""
    code = generate_short_code()
    assert isinstance(code, str)
    assert len(code) == 6
    
    # Test with custom length
    code = generate_short_code(length=10)
    assert len(code) == 10

def test_user_model(app, test_user, test_url):
    """Test basic User model functionality."""
    with app.app_context():
        # Retrieve the user from the database using Session.get (avoiding Query.get deprecation)
        user = db.session.get(User, test_user.id)
        assert user is not None
        assert user.username == test_user.username
        assert user.email == test_user.email
        assert user.github_id == test_user.github_id
        
        # Test relationship to short URLs
        assert len(user.short_urls) > 0
        assert user.short_urls[0].short_code == test_url.short_code

def test_short_url_model(app, test_url):
    """Test basic ShortURL model functionality."""
    with app.app_context():
        url = db.session.get(ShortURL, test_url.id)
        assert url is not None
        assert url.target_url == 'https://example.com'
        
        # Test relationship to user
        assert url.creator is not None
        assert url.creator.id == test_url.user_id

def test_create_with_unique_code(app, test_user, test_url):
    """Test the create_with_unique_code method."""
    with app.app_context():
        # Test with custom code that doesn't exist
        url, error = ShortURL.create_with_unique_code(
            target_url='https://test.com',
            user_id=test_user.id,
            custom_code='custom1'
        )
        assert error is None
        assert url is not None
        assert url.short_code == 'custom1'
        
        # Test with custom code that already exists
        existing_code = test_url.short_code
        url, error = ShortURL.create_with_unique_code(
            target_url='https://test2.com',
            user_id=test_user.id,
            custom_code=existing_code  # This already exists
        )
        assert error is not None
        assert url is None
        
        # Test with generated code
        url, error = ShortURL.create_with_unique_code(
            target_url='https://test3.com',
            user_id=test_user.id
        )
        assert error is None
        assert url is not None
        assert len(url.short_code) == 6