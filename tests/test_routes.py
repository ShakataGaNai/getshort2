import json
from flask import url_for

def test_index_route(client):
    """Test the main index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'GetShort URL Shortener' in response.data

def test_redirect_route(client, app):
    """Test the URL redirection functionality."""
    with app.test_request_context():
        # Test with a valid short code
        response = client.get('/test123')
        assert response.status_code == 302
        assert response.location == 'https://example.com'
        
        # Test with an invalid short code
        response = client.get('/nonexistent')
        assert response.status_code == 404

def test_api_urls_route_unauthenticated(client, app):
    """Test the API URLs route without authentication."""
    with app.test_request_context():
        response = client.get(url_for('api.get_urls'))
        # Should redirect to login page since we're not authenticated
        assert response.status_code == 302

def test_api_create_url_route_unauthenticated(client, app):
    """Test the API create URL route without authentication."""
    with app.test_request_context():
        response = client.post(
            url_for('api.create_url'),
            data=json.dumps({'target_url': 'https://test.com'}),
            content_type='application/json'
        )
        # Should redirect to login page since we're not authenticated
        assert response.status_code == 302