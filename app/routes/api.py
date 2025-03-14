from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import ShortURL, Visit, DomainModifier
import validators
import json
from app.utils.monitoring import url_operation_counter

api_bp = Blueprint('api', __name__)

@api_bp.route('/urls', methods=['GET'])
@login_required
def get_urls():
    """API endpoint to get all URLs for the current user"""
    try:
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
                'apply_modifiers': url.apply_modifiers,
                'short_url': url_for('main.redirect_to_url', short_code=url.short_code, _external=True)
            })
        
        url_operation_counter.labels(operation='list', status='success').inc()
        return jsonify(urls=result)
    except Exception as e:
        url_operation_counter.labels(operation='list', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/urls', methods=['POST'])
@login_required
def create_url():
    """API endpoint to create a new shortened URL"""
    data = request.json
    
    if not data or 'target_url' not in data:
        url_operation_counter.labels(operation='create', status='bad_request').inc()
        return jsonify(error='Missing target_url parameter'), 400
    
    target_url = data.get('target_url')
    custom_code = data.get('custom_code')
    apply_modifiers = data.get('apply_modifiers', True)
    
    # Validate target URL
    if not validators.url(target_url):
        url_operation_counter.labels(operation='create', status='validation_error').inc()
        return jsonify(error='Invalid URL. Please enter a valid URL including http:// or https://'), 400
    
    # Create short URL
    try:
        short_url, error = ShortURL.create_with_unique_code(
            target_url=target_url,
            user_id=current_user.id,
            custom_code=custom_code,
            apply_modifiers=apply_modifiers
        )
        
        if error:
            url_operation_counter.labels(operation='create', status='error').inc()
            return jsonify(error=error), 400
        
        url_operation_counter.labels(operation='create', status='success').inc()
        return jsonify({
            'id': short_url.id,
            'short_code': short_url.short_code,
            'target_url': short_url.target_url,
            'created_at': short_url.created_at.isoformat(),
            'apply_modifiers': short_url.apply_modifiers,
            'short_url': url_for('main.redirect_to_url', short_code=short_url.short_code, _external=True)
        }), 201
    except Exception as e:
        url_operation_counter.labels(operation='create', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/urls/<int:url_id>', methods=['PATCH'])
@login_required
def update_url(url_id):
    """API endpoint to update a shortened URL"""
    try:
        short_url = ShortURL.query.get_or_404(url_id)
        
        # Make sure the URL belongs to the current user
        if short_url.user_id != current_user.id:
            url_operation_counter.labels(operation='update', status='unauthorized').inc()
            return jsonify(error='You do not have permission to update this URL'), 403
        
        data = request.json
        if 'apply_modifiers' in data:
            short_url.apply_modifiers = bool(data['apply_modifiers'])
        
        db.session.commit()
        
        url_operation_counter.labels(operation='update', status='success').inc()
        return jsonify({
            'id': short_url.id,
            'short_code': short_url.short_code,
            'target_url': short_url.target_url,
            'created_at': short_url.created_at.isoformat(),
            'apply_modifiers': short_url.apply_modifiers,
            'short_url': url_for('main.redirect_to_url', short_code=short_url.short_code, _external=True)
        })
    except Exception as e:
        url_operation_counter.labels(operation='update', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/urls/<int:url_id>', methods=['DELETE'])
@login_required
def delete_url(url_id):
    """API endpoint to delete a shortened URL"""
    try:
        short_url = ShortURL.query.get_or_404(url_id)
        
        # Make sure the URL belongs to the current user
        if short_url.user_id != current_user.id:
            url_operation_counter.labels(operation='delete', status='unauthorized').inc()
            return jsonify(error='You do not have permission to delete this URL'), 403
        
        db.session.delete(short_url)
        db.session.commit()
        
        url_operation_counter.labels(operation='delete', status='success').inc()
        return jsonify(message='URL deleted successfully'), 200
    except Exception as e:
        url_operation_counter.labels(operation='delete', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/urls/<int:url_id>/analytics', methods=['GET'])
@login_required
def url_analytics(url_id):
    """API endpoint to get analytics for a specific URL"""
    try:
        short_url = ShortURL.query.get_or_404(url_id)
        
        # Make sure the URL belongs to the current user
        if short_url.user_id != current_user.id:
            url_operation_counter.labels(operation='analytics', status='unauthorized').inc()
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
        
        url_operation_counter.labels(operation='analytics', status='success').inc()
        return jsonify({
            'url_id': url_id,
            'short_code': short_url.short_code,
            'target_url': short_url.target_url,
            'apply_modifiers': short_url.apply_modifiers,
            'total_visits': visit_count,
            'browser_stats': [{'browser': b, 'count': c} for b, c in browser_stats],
            'device_stats': [{'device': d, 'count': c} for d, c in device_stats],
            'country_stats': [{'country': c, 'count': count} for c, count in country_stats if c]
        })
    except Exception as e:
        url_operation_counter.labels(operation='analytics', status='error').inc()
        return jsonify(error=str(e)), 500

# Domain Modifier API Endpoints
@api_bp.route('/domain-modifiers', methods=['GET'])
@login_required
def get_domain_modifiers():
    """API endpoint to get all domain modifiers for the current user"""
    try:
        modifiers = DomainModifier.query.filter_by(user_id=current_user.id).order_by(DomainModifier.created_at.desc()).all()
        
        result = []
        for modifier in modifiers:
            result.append({
                'id': modifier.id,
                'domain': modifier.domain,
                'include_subdomains': modifier.include_subdomains,
                'query_params': json.loads(modifier.query_params),
                'created_at': modifier.created_at.isoformat(),
                'updated_at': modifier.updated_at.isoformat(),
                'active': modifier.active
            })
        
        url_operation_counter.labels(operation='list_modifiers', status='success').inc()
        return jsonify(modifiers=result)
    except Exception as e:
        url_operation_counter.labels(operation='list_modifiers', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/domain-modifiers', methods=['POST'])
@login_required
def create_domain_modifier():
    """API endpoint to create a new domain modifier"""
    data = request.json
    
    required_fields = ['domain', 'query_params']
    for field in required_fields:
        if field not in data:
            url_operation_counter.labels(operation='create_modifier', status='bad_request').inc()
            return jsonify(error=f'Missing required field: {field}'), 400
    
    domain = data.get('domain').lower()
    include_subdomains = data.get('include_subdomains', False)
    query_params = data.get('query_params', {})
    
    if not isinstance(query_params, dict):
        url_operation_counter.labels(operation='create_modifier', status='validation_error').inc()
        return jsonify(error='query_params must be an object with key-value pairs'), 400
    
    # Basic domain validation
    if not domain or '.' not in domain:
        url_operation_counter.labels(operation='create_modifier', status='validation_error').inc()
        return jsonify(error='Invalid domain name'), 400
    
    try:
        # Create new domain modifier
        modifier = DomainModifier(
            domain=domain,
            include_subdomains=include_subdomains,
            query_params=json.dumps(query_params),
            user_id=current_user.id,
            active=data.get('active', True)
        )
        
        db.session.add(modifier)
        db.session.commit()
        
        url_operation_counter.labels(operation='create_modifier', status='success').inc()
        return jsonify({
            'id': modifier.id,
            'domain': modifier.domain,
            'include_subdomains': modifier.include_subdomains,
            'query_params': json.loads(modifier.query_params),
            'created_at': modifier.created_at.isoformat(),
            'updated_at': modifier.updated_at.isoformat(),
            'active': modifier.active
        }), 201
    except Exception as e:
        url_operation_counter.labels(operation='create_modifier', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/domain-modifiers/<int:modifier_id>', methods=['PATCH'])
@login_required
def update_domain_modifier(modifier_id):
    """API endpoint to update a domain modifier"""
    try:
        modifier = DomainModifier.query.get_or_404(modifier_id)
        
        # Make sure the modifier belongs to the current user
        if modifier.user_id != current_user.id:
            url_operation_counter.labels(operation='update_modifier', status='unauthorized').inc()
            return jsonify(error='You do not have permission to update this domain modifier'), 403
        
        data = request.json
        
        if 'domain' in data:
            domain = data['domain'].lower()
            if not domain or '.' not in domain:
                url_operation_counter.labels(operation='update_modifier', status='validation_error').inc()
                return jsonify(error='Invalid domain name'), 400
            modifier.domain = domain
            
        if 'include_subdomains' in data:
            modifier.include_subdomains = bool(data['include_subdomains'])
            
        if 'query_params' in data:
            query_params = data['query_params']
            if not isinstance(query_params, dict):
                url_operation_counter.labels(operation='update_modifier', status='validation_error').inc()
                return jsonify(error='query_params must be an object with key-value pairs'), 400
            modifier.query_params = json.dumps(query_params)
            
        if 'active' in data:
            modifier.active = bool(data['active'])
        
        db.session.commit()
        
        url_operation_counter.labels(operation='update_modifier', status='success').inc()
        return jsonify({
            'id': modifier.id,
            'domain': modifier.domain,
            'include_subdomains': modifier.include_subdomains,
            'query_params': json.loads(modifier.query_params),
            'created_at': modifier.created_at.isoformat(),
            'updated_at': modifier.updated_at.isoformat(),
            'active': modifier.active
        })
    except Exception as e:
        url_operation_counter.labels(operation='update_modifier', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/domain-modifiers/<int:modifier_id>', methods=['DELETE'])
@login_required
def delete_domain_modifier(modifier_id):
    """API endpoint to delete a domain modifier"""
    try:
        modifier = DomainModifier.query.get_or_404(modifier_id)
        
        # Make sure the modifier belongs to the current user
        if modifier.user_id != current_user.id:
            url_operation_counter.labels(operation='delete_modifier', status='unauthorized').inc()
            return jsonify(error='You do not have permission to delete this domain modifier'), 403
        
        db.session.delete(modifier)
        db.session.commit()
        
        url_operation_counter.labels(operation='delete_modifier', status='success').inc()
        return jsonify(message='Domain modifier deleted successfully'), 200
    except Exception as e:
        url_operation_counter.labels(operation='delete_modifier', status='error').inc()
        return jsonify(error=str(e)), 500

@api_bp.route('/domain-modifiers/test', methods=['POST'])
@login_required
def test_domain_modifier():
    """API endpoint to test a domain modifier without creating it"""
    data = request.json
    
    if not data or 'url' not in data or 'query_params' not in data:
        return jsonify(error='Missing required fields: url and query_params'), 400
    
    url = data.get('url')
    query_params = data.get('query_params', {})
    
    # Validate URL
    if not validators.url(url):
        return jsonify(error='Invalid URL. Please enter a valid URL including http:// or https://'), 400
    
    # Simulate domain modifier
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    parsed_url = urlparse(url)
    query_dict = parse_qs(parsed_url.query)
    
    for key, value in query_params.items():
        query_dict[key] = [value]
    
    new_query = urlencode(query_dict, doseq=True)
    parsed_url = parsed_url._replace(query=new_query)
    
    modified_url = urlunparse(parsed_url)
    
    return jsonify({
        'original_url': url,
        'modified_url': modified_url,
        'query_params_added': query_params
    })