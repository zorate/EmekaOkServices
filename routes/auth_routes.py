# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from models.user_model import User
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("product.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Check if admin login
        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            user = User({
                "_id": "admin",  # static ID for admin
                "username": username,
                "role": "admin",
                "created_at": None
            })
            login_user(user, remember=True)
            flash("Welcome back, Admin!", "success")
            return redirect(url_for("admin.dashboard"))

        # Otherwise check DB for sales user
        user = User.authenticate(username, password)
        if user:
            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("product.dashboard"))

        flash("Invalid credentials", "error")

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
