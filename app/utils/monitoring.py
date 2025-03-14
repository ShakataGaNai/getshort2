import time
from healthcheck import HealthCheck
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
    health = HealthCheck()

    # Add check for database connection
    def db_check():
        try:
            # Execute a simple query
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return True, "Database connection OK"
        except Exception as e:
            return False, str(e)

    # Add check for app status
    def app_status():
        return True, "Application is running"

    # Add the checks to the health check instance
    health.add_check(db_check)
    health.add_check(app_status)

    # Register the health check endpoint
    @health_bp.route('/')
    def health_check():
        return health.run()

    # Register the readiness endpoint
    @health_bp.route('/ready')
    def readiness():
        # Add additional checks for readiness if needed
        checks = health.run()
        if checks[0] != 200:
            return jsonify({"status": "not ready"}), 503
        return jsonify({"status": "ready"})

    # Register the liveness endpoint
    @health_bp.route('/live')
    def liveness():
        return jsonify({"status": "alive"})

    # Register the blueprint with the app
    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)

    # Initialize the metrics with the app
    metrics.init_app(app)

    return health