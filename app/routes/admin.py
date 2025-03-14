from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import ShortURL, Visit
import validators

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
        
        # Validate target URL
        if not validators.url(target_url):
            flash('Invalid URL. Please enter a valid URL including http:// or https://', 'error')
            return redirect(url_for('admin.create_url'))
        
        # Create short URL
        short_url, error = ShortURL.create_with_unique_code(
            target_url=target_url,
            user_id=current_user.id,
            custom_code=custom_code
        )
        
        if error:
            flash(error, 'error')
            return redirect(url_for('admin.create_url'))
        
        flash(f'Short URL created successfully: {short_url.short_code}', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/create_url.html')

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
    
    return render_template('admin/user_analytics.html',
                           browser_stats=browser_stats,
                           device_stats=device_stats,
                           country_stats=country_stats,
                           top_urls=top_urls)