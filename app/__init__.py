"""Flask application factory"""
from flask import Flask, render_template
from flask_cors import CORS
from app.config import Config
from app.logging_config import setup_logging
from app.routes import api
from app.metrics import metrics_endpoint

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    app.config.from_object(Config)

    setup_logging()
    CORS(app)

    app.register_blueprint(api)
    app.add_url_rule('/metrics', 'metrics', metrics_endpoint)

    @app.route('/')
    def index():
        """Serve frontend interface"""
        return render_template('index.html')

    return app
