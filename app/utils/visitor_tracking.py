import os
import geoip2.database
from user_agents import parse
from flask import request
from app import db
from app.models import Visit

# Initialize the GeoIP reader
geoip_db_path = os.environ.get('GEOIP_DB_PATH', 'GeoLite2-City.mmdb')
try:
    geoip_reader = geoip2.database.Reader(geoip_db_path)
except FileNotFoundError:
    geoip_reader = None

def track_visit(short_url):
    """
    Track a visit to a short URL by collecting information from the request
    and storing it in the database.
    """
    # Extract IP address
    ip_address = request.remote_addr
    
    # Extract user agent information
    user_agent_string = request.user_agent.string
    user_agent = parse(user_agent_string)
    
    browser = user_agent.browser.family
    browser_version = user_agent.browser.version_string
    
    # Determine device type
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_tablet:
        device_type = 'tablet'
    else:
        device_type = 'desktop'
    
    # Get operating system
    operating_system = user_agent.os.family
    
    # Get location information from IP
    country_code = None
    country_name = None
    city = None
    
    if geoip_reader:
        try:
            geo_response = geoip_reader.city(ip_address)
            country_code = geo_response.country.iso_code
            country_name = geo_response.country.name
            city = geo_response.city.name
        except:
            # If IP lookup fails, just continue without location info
            pass
    
    # Get referrer if available
    referrer = request.referrer
    
    # Create and save visit record
    visit = Visit(
        short_url_id=short_url.id,
        ip_address=ip_address,
        user_agent=user_agent_string,
        browser=browser,
        browser_version=browser_version,
        device_type=device_type,
        operating_system=operating_system,
        country_code=country_code,
        country_name=country_name,
        city=city,
        referrer=referrer
    )
    
    db.session.add(visit)
    db.session.commit()
    
    return visit