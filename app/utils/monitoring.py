import time
# from healthcheck import HealthCheck  # Commenting out due to compatibility issues
from prometheus_flask_exporter import PrometheusMetrics, Counter, Histogram
from flask import Blueprint, current_app, jsonify, g, request
from sqlalchemy import text

# Create monitoring blueprints
health_bp = Blueprint('health', __name__, url_prefix='/health')
metrics_bp = Blueprint('metrics', __name__)

# Initialize Prometheus metrics
metrics = PrometheusMetrics.for_app_factory()

# Custom metrics
redirect_counter = Counter(
    'getshort_redirect_total', 
    'Number of URL redirects', 
    ['status', 'short_code']
)

url_operation_counter = Counter(
    'getshort_url_operations_total',
    'Number of URL operations',
    ['operation', 'status']
)

request_latency = Histogram(
    'getshort_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

# Define latency monitoring for requests
@metrics_bp.before_request
def before_request():
    g.start_time = time.time()

@metrics_bp.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        request_duration = time.time() - g.start_time
        endpoint = request.endpoint or 'unknown'
        request_latency.labels(endpoint=endpoint).observe(request_duration)
    return response

def init_health_check(app, db):
    """Initialize the health check endpoints"""
    # Register the health check endpoint
    @health_bp.route('/')
    def health_check():
        try:
            # Execute a simple database query
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            db_status = True
        except Exception as e:
            db_status = False
            db_error = str(e)
        
        health_status = {
            "status": "healthy" if db_status else "unhealthy",
            "checks": {
                "database": {
                    "status": "ok" if db_status else "error",
                    "message": "Database connection OK" if db_status else db_error
                },
                "app": {
                    "status": "ok",
                    "message": "Application is running"
                }
            }
        }
        
        status_code = 200 if db_status else 500
        return jsonify(health_status), status_code

    # Register the readiness endpoint
    @health_bp.route('/ready')
    def readiness():
        try:
            # Check if the database is accessible
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return jsonify({"status": "ready"}), 200
        except Exception as e:
            return jsonify({"status": "not ready", "reason": str(e)}), 503

    # Register the liveness endpoint
    @health_bp.route('/live')
    def liveness():
        return jsonify({"status": "alive"})

    # Register the blueprint with the app
    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)

    # Initialize the metrics with the app
    metrics.init_app(app)

    return app