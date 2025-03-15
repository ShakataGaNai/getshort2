from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import ShortURL, Visit, DomainModifier
import validators
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard showing user's shortened URLs"""
    # Get user's short URLs
    short_urls = ShortURL.query.filter_by(user_id=current_user.id).order_by(ShortURL.created_at.desc()).all()
    
    # For each URL, count the number of visits
    urls_with_stats = []
    for url in short_urls:
        visit_count = Visit.query.filter_by(short_url_id=url.id).count()
        urls_with_stats.append({
            'url': url,
            'visit_count': visit_count
        })
    
    return render_template('admin/dashboard.html', urls=urls_with_stats)

@admin_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_url():
    """Create a new shortened URL"""
    if request.method == 'POST':
        target_url = request.form.get('target_url')
        custom_code = request.form.get('custom_code') or None
        apply_modifiers = request.form.get('apply_modifiers', 'on') == 'on'
        
        # Validate target URL
        if not validators.url(target_url):
            flash('Invalid URL. Please enter a valid URL including http:// or https://', 'error')
            return redirect(url_for('admin.create_url'))
        
        # Create short URL
        short_url, error = ShortURL.create_with_unique_code(
            target_url=target_url,
            user_id=current_user.id,
            custom_code=custom_code,
            apply_modifiers=apply_modifiers
        )
        
        if error:
            flash(error, 'error')
            return redirect(url_for('admin.create_url'))
        
        flash(f'Short URL created successfully: {short_url.short_code}', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/create_url.html')

@admin_bp.route('/edit/<int:url_id>', methods=['GET', 'POST'])
@login_required
def edit_url(url_id):
    """Edit a shortened URL"""
    short_url = ShortURL.query.get_or_404(url_id)
    
    # Make sure the URL belongs to the current user
    if short_url.user_id != current_user.id:
        flash('You do not have permission to edit this URL', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        target_url = request.form.get('target_url')
        apply_modifiers = request.form.get('apply_modifiers', 'off') == 'on'
        
        # Validate target URL
        if not validators.url(target_url):
            flash('Invalid URL. Please enter a valid URL including http:// or https://', 'error')
            return redirect(url_for('admin.edit_url', url_id=url_id))
        
        short_url.target_url = target_url
        short_url.apply_modifiers = apply_modifiers
        db.session.commit()
        
        flash('URL updated successfully', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/edit_url.html', url=short_url)

@admin_bp.route('/delete/<int:url_id>', methods=['POST'])
@login_required
def delete_url(url_id):
    """Delete a shortened URL"""
    short_url = ShortURL.query.get_or_404(url_id)
    
    # Make sure the URL belongs to the current user
    if short_url.user_id != current_user.id:
        flash('You do not have permission to delete this URL', 'error')
        return redirect(url_for('admin.dashboard'))
    
    db.session.delete(short_url)
    db.session.commit()
    
    flash('URL deleted successfully', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/analytics/<int:url_id>')
@login_required
def url_analytics(url_id):
    """View analytics for a specific URL"""
    short_url = ShortURL.query.get_or_404(url_id)
    
    # Make sure the URL belongs to the current user
    if short_url.user_id != current_user.id:
        flash('You do not have permission to view analytics for this URL', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Get all visits for this URL
    visits = Visit.query.filter_by(short_url_id=url_id).order_by(Visit.timestamp.desc()).all()
    
    # Get visit statistics
    browser_stats = db.session.query(
        Visit.browser, func.count(Visit.id)
    ).filter_by(short_url_id=url_id).group_by(Visit.browser).all()
    
    device_stats = db.session.query(
        Visit.device_type, func.count(Visit.id)
    ).filter_by(short_url_id=url_id).group_by(Visit.device_type).all()
    
    country_stats = db.session.query(
        Visit.country_name, func.count(Visit.id)
    ).filter_by(short_url_id=url_id).group_by(Visit.country_name).all()
    
    return render_template('admin/url_analytics.html', 
                           url=short_url, 
                           visits=visits,
                           browser_stats=browser_stats,
                           device_stats=device_stats,
                           country_stats=country_stats)

@admin_bp.route('/analytics')
@login_required
def user_analytics():
    """View analytics for all user's URLs"""
    # Get all user's URLs
    short_urls = ShortURL.query.filter_by(user_id=current_user.id).all()
    url_ids = [url.id for url in short_urls]
    
    if not url_ids:
        flash('You don\'t have any URLs yet', 'info')
        return redirect(url_for('admin.dashboard'))
    
    # Get aggregated stats for all user's URLs
    browser_stats = db.session.query(
        Visit.browser, func.count(Visit.id)
    ).filter(Visit.short_url_id.in_(url_ids)).group_by(Visit.browser).all()
    
    device_stats = db.session.query(
        Visit.device_type, func.count(Visit.id)
    ).filter(Visit.short_url_id.in_(url_ids)).group_by(Visit.device_type).all()
    
    country_stats = db.session.query(
        Visit.country_name, func.count(Visit.id)
    ).filter(Visit.short_url_id.in_(url_ids)).group_by(Visit.country_name).all()
    
    # Get top 10 most visited URLs
    top_urls = db.session.query(
        ShortURL, func.count(Visit.id).label('visit_count')
    ).join(Visit).filter(ShortURL.id.in_(url_ids)).group_by(ShortURL.id).order_by(
        func.count(Visit.id).desc()
    ).limit(10).all()
    
    # Process the top_urls to include rank without using enumerate in template
    processed_top_urls = []
    for i, (url, visit_count) in enumerate(top_urls):
        processed_top_urls.append({
            'rank': i + 1,
            'url': url,
            'visit_count': visit_count
        })
    
    return render_template('admin/user_analytics.html',
                           browser_stats=browser_stats,
                           device_stats=device_stats,
                           country_stats=country_stats,
                           top_urls=processed_top_urls)

# Domain Modifiers Management
@admin_bp.route('/domain-modifiers')
@login_required
def domain_modifiers():
    """View all domain modifiers"""
    modifiers = DomainModifier.query.filter_by(user_id=current_user.id).order_by(DomainModifier.created_at.desc()).all()
    
    # Prepare the modifiers by parsing the JSON query_params
    parsed_modifiers = []
    for modifier in modifiers:
        mod_dict = modifier.__dict__.copy()
        try:
            mod_dict['parsed_query_params'] = json.loads(modifier.query_params)
        except (json.JSONDecodeError, TypeError):
            mod_dict['parsed_query_params'] = {}
        parsed_modifiers.append(mod_dict)
    
    return render_template('admin/domain_modifiers.html', modifiers=parsed_modifiers)

@admin_bp.route('/domain-modifiers/create', methods=['GET', 'POST'])
@login_required
def create_domain_modifier():
    """Create a new domain modifier"""
    if request.method == 'POST':
        domain = request.form.get('domain', '').lower()
        include_subdomains = request.form.get('include_subdomains', 'off') == 'on'
        
        # Get all query parameters
        query_params = {}
        param_keys = request.form.getlist('param_key[]')
        param_values = request.form.getlist('param_value[]')
        
        # Print debug info
        print(f"Form data: {request.form}")
        print(f"Param keys: {param_keys}")
        print(f"Param values: {param_values}")
        
        for i in range(len(param_keys)):
            if i < len(param_values) and param_keys[i].strip():
                query_params[param_keys[i].strip()] = param_values[i].strip()
        
        # Validate domain
        if not domain or '.' not in domain:
            flash('Invalid domain name', 'error')
            return redirect(url_for('admin.create_domain_modifier'))
        
        # Validate query params
        if not query_params:
            flash('You must specify at least one query parameter', 'error')
            return redirect(url_for('admin.create_domain_modifier'))
        
        # Create new domain modifier
        modifier = DomainModifier(
            domain=domain,
            include_subdomains=include_subdomains,
            query_params=json.dumps(query_params),
            user_id=current_user.id,
            active=True
        )
        
        db.session.add(modifier)
        db.session.commit()
        
        flash('Domain modifier created successfully', 'success')
        return redirect(url_for('admin.domain_modifiers'))
    
    return render_template('admin/create_domain_modifier.html')

@admin_bp.route('/domain-modifiers/edit/<int:modifier_id>', methods=['GET', 'POST'])
@login_required
def edit_domain_modifier(modifier_id):
    """Edit a domain modifier"""
    modifier = DomainModifier.query.get_or_404(modifier_id)
    
    # Make sure the modifier belongs to the current user
    if modifier.user_id != current_user.id:
        flash('You do not have permission to edit this domain modifier', 'error')
        return redirect(url_for('admin.domain_modifiers'))
    
    if request.method == 'POST':
        domain = request.form.get('domain', '').lower()
        include_subdomains = request.form.get('include_subdomains', 'off') == 'on'
        active = request.form.get('active', 'off') == 'on'
        
        # Get all query parameters
        query_params = {}
        param_keys = request.form.getlist('param_key[]')
        param_values = request.form.getlist('param_value[]')
        
        for i in range(len(param_keys)):
            if i < len(param_values) and param_keys[i].strip():
                query_params[param_keys[i].strip()] = param_values[i].strip()
        
        # Validate domain
        if not domain or '.' not in domain:
            flash('Invalid domain name', 'error')
            return redirect(url_for('admin.edit_domain_modifier', modifier_id=modifier_id))
        
        # Validate query params
        if not query_params:
            flash('You must specify at least one query parameter', 'error')
            return redirect(url_for('admin.edit_domain_modifier', modifier_id=modifier_id))
        
        # Update domain modifier
        modifier.domain = domain
        modifier.include_subdomains = include_subdomains
        modifier.query_params = json.dumps(query_params)
        modifier.active = active
        
        db.session.commit()
        
        flash('Domain modifier updated successfully', 'success')
        return redirect(url_for('admin.domain_modifiers'))
    
    # Parse query parameters for template
    query_params = json.loads(modifier.query_params)
    
    return render_template('admin/edit_domain_modifier.html', 
                          modifier=modifier, 
                          query_params=query_params)

@admin_bp.route('/domain-modifiers/delete/<int:modifier_id>', methods=['POST'])
@login_required
def delete_domain_modifier(modifier_id):
    """Delete a domain modifier"""
    modifier = DomainModifier.query.get_or_404(modifier_id)
    
    # Make sure the modifier belongs to the current user
    if modifier.user_id != current_user.id:
        flash('You do not have permission to delete this domain modifier', 'error')
        return redirect(url_for('admin.domain_modifiers'))
    
    db.session.delete(modifier)
    db.session.commit()
    
    flash('Domain modifier deleted successfully', 'success')
    return redirect(url_for('admin.domain_modifiers'))

@admin_bp.route('/domain-modifiers/test', methods=['GET', 'POST'])
@login_required
def test_domain_modifier():
    """Test a domain modifier without creating it"""
    if request.method == 'POST':
        url = request.form.get('url')
        
        # Get all query parameters
        query_params = {}
        param_keys = request.form.getlist('param_key[]')
        param_values = request.form.getlist('param_value[]')
        
        for i in range(len(param_keys)):
            if i < len(param_values) and param_keys[i].strip():
                query_params[param_keys[i].strip()] = param_values[i].strip()
        
        # Validate URL
        if not validators.url(url):
            flash('Invalid URL. Please enter a valid URL including http:// or https://', 'error')
            return redirect(url_for('admin.test_domain_modifier'))
        
        # Simulate domain modifier
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed_url = urlparse(url)
        query_dict = parse_qs(parsed_url.query)
        
        for key, value in query_params.items():
            query_dict[key] = [value]
        
        new_query = urlencode(query_dict, doseq=True)
        parsed_url = parsed_url._replace(query=new_query)
        
        modified_url = urlunparse(parsed_url)
        
        return render_template('admin/test_domain_modifier.html', 
                              original_url=url, 
                              modified_url=modified_url,
                              query_params=query_params)
    
    return render_template('admin/test_domain_modifier.html')