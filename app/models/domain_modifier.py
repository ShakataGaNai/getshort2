from datetime import datetime, UTC
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from app import db

class DomainModifier(db.Model):
    """Model for storing domain-specific URL modifiers (e.g., referral codes)"""
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False, index=True)
    include_subdomains = db.Column(db.Boolean, default=False)
    query_params = db.Column(db.Text, nullable=False)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<DomainModifier {self.domain}>'
    
    @staticmethod
    def apply_modifiers(url):
        """Apply all active domain modifiers to a URL if it matches the domain criteria"""
        if not url:
            return url
            
        # Parse the URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if not domain:
            return url  # No domain to match
        
        # Find matching domain modifiers
        # We need the current user, but we can't import it at the top level due to circular imports
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            modifiers = db.session.execute(
                db.select(DomainModifier).filter_by(active=True, user_id=current_user.id)
            ).scalars().all()
        else:
            # If there's no logged-in user (e.g., in public redirect), don't apply modifiers
            return url
            
        applicable_modifiers = []
        
        for modifier in modifiers:
            modifier_domain = modifier.domain.lower()
            
            # Check if domain matches
            if modifier.include_subdomains:
                # Check if domain is or is a subdomain of the modifier domain
                if domain == modifier_domain or domain.endswith('.' + modifier_domain):
                    applicable_modifiers.append(modifier)
            else:
                # Direct domain match only
                if domain == modifier_domain:
                    applicable_modifiers.append(modifier)
        
        if not applicable_modifiers:
            return url  # No modifiers to apply
            
        # Apply modifiers
        for modifier in applicable_modifiers:
            # Parse the existing query string
            query_dict = parse_qs(parsed_url.query)
            
            # Parse and add the modifier's query parameters
            import json
            new_params = json.loads(modifier.query_params)
            
            for key, value in new_params.items():
                query_dict[key] = [value]  # query_dict values are lists
            
            # Rebuild the query string
            new_query = urlencode(query_dict, doseq=True)
            
            # Update the parsed URL with the new query string
            parsed_url = parsed_url._replace(query=new_query)
        
        # Reconstruct the URL with the applied modifiers
        return urlunparse(parsed_url)