from app import create_app
from datetime import datetime, UTC

app = create_app()

# Add current date to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now(UTC)}

if __name__ == '__main__':
    # Flask 3.x compatibility: debug is now part of the config rather than a run parameter
    app.config['DEBUG'] = True
    app.run(host='0.0.0.0', port=5001)