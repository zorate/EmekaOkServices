# app.py
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from models.user_model import User
import os

# Blueprints
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.sale_routes import sale_bp
from routes.analytics_routes import analytics_bp
from routes.admin_routes import admin_bp  # NEW

app = Flask(__name__)
app.config.from_object(Config)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return User({
            "_id": "admin",
            "username": os.getenv("ADMIN_USERNAME"),
            "role": "admin",
            "created_at": None
        })
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        return None
    return User.get_by_id(obj_id)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(product_bp)
app.register_blueprint(sale_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(admin_bp)  # NEW

@app.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("product.dashboard"))
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
