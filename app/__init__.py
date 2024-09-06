from flask import Flask, send_from_directory
from .extensions import mongo
from .webhook import routes

def create_app():
    app = Flask(__name__)

    app.config["MONGO_URI"] = "mongodb://localhost:27017/webhook_data"
    mongo.init_app(app)

    # Register blueprints
    app.register_blueprint(routes.webhook)

    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')

    return app
