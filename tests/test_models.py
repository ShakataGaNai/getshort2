from app.models import User, ShortURL, Visit, generate_short_code

def test_generate_short_code():
    """Test that generate_short_code returns a string of the expected length."""
    code = generate_short_code()
    assert isinstance(code, str)
    assert len(code) == 6
    
    # Test with custom length
    code = generate_short_code(length=10)
    assert len(code) == 10

def test_user_model(app):
    """Test basic User model functionality."""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.github_id == 12345
        
        # Test relationship to short URLs
        assert len(user.short_urls) > 0
        assert user.short_urls[0].short_code == 'test123'

def test_short_url_model(app):
    """Test basic ShortURL model functionality."""
    with app.app_context():
        url = ShortURL.query.filter_by(short_code='test123').first()
        assert url is not None
        assert url.target_url == 'https://example.com'
        
        # Test relationship to user
        assert url.creator is not None
        assert url.creator.username == 'testuser'

def test_create_with_unique_code(app):
    """Test the create_with_unique_code method."""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        
        # Test with custom code that doesn't exist
        url, error = ShortURL.create_with_unique_code(
            target_url='https://test.com',
            user_id=user.id,
            custom_code='custom1'
        )
        assert error is None
        assert url is not None
        assert url.short_code == 'custom1'
        
        # Test with custom code that already exists
        url, error = ShortURL.create_with_unique_code(
            target_url='https://test2.com',
            user_id=user.id,
            custom_code='test123'  # This already exists from test data
        )
        assert error is not None
        assert url is None
        
        # Test with generated code
        url, error = ShortURL.create_with_unique_code(
            target_url='https://test3.com',
            user_id=user.id
        )
        assert error is None
        assert url is not None
        assert len(url.short_code) == 6