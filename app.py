import os

from flask import Flask, redirect, render_template, url_for

from config import Config
from extensions import db, login_manager
from models import User


def create_app(config_class=Config):
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path=f"{config_class.URL_PREFIX}/static",
    )
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER_VIDEOS"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_POSTERS"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from blueprints.auth import bp as auth_bp
    from blueprints.main import bp as main_bp
    from blueprints.admin import bp as admin_bp

    app.register_blueprint(main_bp, url_prefix=config_class.URL_PREFIX)
    app.register_blueprint(auth_bp, url_prefix=config_class.URL_PREFIX)
    app.register_blueprint(admin_bp, url_prefix=f"{config_class.URL_PREFIX}/admin")

    @app.route("/")
    def root_redirect():
        return redirect(url_for("main.library"))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="Brak dostępu do tej strony."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Nie znaleziono strony."), 404

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=app.config["DEBUG"])
