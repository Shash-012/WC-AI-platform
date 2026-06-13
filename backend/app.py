from flask import Flask

app = Flask(__name__)

from modules.scout.routes import scout_bp
app.register_blueprint(scout_bp, url_prefix="/scout")

if __name__ == "__main__":
    app.run(debug=True)