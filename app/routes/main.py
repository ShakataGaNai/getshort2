from flask import Blueprint, render_template, redirect, abort, current_app
from app import db
from app.models import ShortURL
from app.utils.visitor_tracking import track_visit
from app.utils.monitoring import redirect_counter

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main landing page explaining the service"""
    return render_template('index.html')

@main_bp.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect a user to the target URL based on the short code"""
    short_url = db.session.execute(
        db.select(ShortURL).filter_by(short_code=short_code)
    ).scalar_one_or_none()
    
    if not short_url:
        # Log unsuccessful redirect attempt
        redirect_counter.labels(status='not_found', short_code=short_code).inc()
        return abort(404)
    
    try:
        # Track this visit
        track_visit(short_url)
        
        # Get the target URL with modifiers applied if needed
        target_url = short_url.get_redirect_url()
        
        # Log successful redirect
        redirect_counter.labels(status='success', short_code=short_code).inc()
        
        # Redirect to the target URL
        return redirect(target_url)
    except Exception as e:
        current_app.logger.error(f"Error redirecting {short_code}: {str(e)}")
        redirect_counter.labels(status='error', short_code=short_code).inc()
        return abort(500)