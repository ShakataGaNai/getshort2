from flask import Blueprint, render_template, redirect, abort
from app.models import ShortURL
from app.utils.visitor_tracking import track_visit

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main landing page explaining the service"""
    return render_template('index.html')

@main_bp.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect a user to the target URL based on the short code"""
    short_url = ShortURL.query.filter_by(short_code=short_code).first_or_404()
    
    # Track this visit
    track_visit(short_url)
    
    # Redirect to the target URL
    return redirect(short_url.target_url)