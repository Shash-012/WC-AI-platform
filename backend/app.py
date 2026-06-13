from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour", "20 per minute"],
    storage_uri="memory://"
)

from modules.scout.routes import scout_bp
app.register_blueprint(scout_bp, url_prefix="/scout")

if __name__ == "__main__":
    app.run(debug=True)