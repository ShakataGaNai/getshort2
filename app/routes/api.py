from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import ShortURL, Visit
import validators

api_bp = Blueprint('api', __name__)

@api_bp.route('/urls', methods=['GET'])
@login_required
def get_urls():
    """API endpoint to get all URLs for the current user"""
    urls = ShortURL.query.filter_by(user_id=current_user.id).order_by(ShortURL.created_at.desc()).all()
    
    result = []
    for url in urls:
        visit_count = Visit.query.filter_by(short_url_id=url.id).count()
        result.append({
            'id': url.id,
            'short_code': url.short_code,
            'target_url': url.target_url,
            'created_at': url.created_at.isoformat(),
            'visit_count': visit_count,
            'short_url': url_for('main.redirect_to_url', short_code=url.short_code, _external=True)
        })
    
    return jsonify(urls=result)

@api_bp.route('/urls', methods=['POST'])
@login_required
def create_url():
    """API endpoint to create a new shortened URL"""
    data = request.json
    
    if not data or 'target_url' not in data:
        return jsonify(error='Missing target_url parameter'), 400
    
    target_url = data.get('target_url')
    custom_code = data.get('custom_code')
    
    # Validate target URL
    if not validators.url(target_url):
        return jsonify(error='Invalid URL. Please enter a valid URL including http:// or https://'), 400
    
    # Create short URL
    short_url, error = ShortURL.create_with_unique_code(
        target_url=target_url,
        user_id=current_user.id,
        custom_code=custom_code
    )
    
    if error:
        return jsonify(error=error), 400
    
    return jsonify({
        'id': short_url.id,
        'short_code': short_url.short_code,
        'target_url': short_url.target_url,
        'created_at': short_url.created_at.isoformat(),
        'short_url': url_for('main.redirect_to_url', short_code=short_url.short_code, _external=True)
    }), 201

@api_bp.route('/urls/<int:url_id>', methods=['DELETE'])
@login_required
def delete_url(url_id):
    """API endpoint to delete a shortened URL"""
    short_url = ShortURL.query.get_or_404(url_id)
    
    # Make sure the URL belongs to the current user
    if short_url.user_id != current_user.id:
        return jsonify(error='You do not have permission to delete this URL'), 403
    
    db.session.delete(short_url)
    db.session.commit()
    
    return jsonify(message='URL deleted successfully'), 200

@api_bp.route('/urls/<int:url_id>/analytics', methods=['GET'])
@login_required
def url_analytics(url_id):
    """API endpoint to get analytics for a specific URL"""
    short_url = ShortURL.query.get_or_404(url_id)
    
    # Make sure the URL belongs to the current user
    if short_url.user_id != current_user.id:
        return jsonify(error='You do not have permission to view analytics for this URL'), 403
    
    # Get visit count
    visit_count = Visit.query.filter_by(short_url_id=url_id).count()
    
    # Get visit statistics
    browser_stats = db.session.query(
        Visit.browser, func.count(Visit.id).label('count')
    ).filter_by(short_url_id=url_id).group_by(Visit.browser).all()
    
    device_stats = db.session.query(
        Visit.device_type, func.count(Visit.id).label('count')
    ).filter_by(short_url_id=url_id).group_by(Visit.device_type).all()
    
    country_stats = db.session.query(
        Visit.country_name, func.count(Visit.id).label('count')
    ).filter_by(short_url_id=url_id).group_by(Visit.country_name).all()
    
    return jsonify({
        'url_id': url_id,
        'short_code': short_url.short_code,
        'target_url': short_url.target_url,
        'total_visits': visit_count,
        'browser_stats': [{'browser': b, 'count': c} for b, c in browser_stats],
        'device_stats': [{'device': d, 'count': c} for d, c in device_stats],
        'country_stats': [{'country': c, 'count': count} for c, count in country_stats if c]
    })