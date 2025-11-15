# routes/admin_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from utils.db import get_db
from bson import ObjectId
from datetime import datetime
import io, csv

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
db = get_db()

def admin_only():
    if current_user.role != "admin":
        return "Access denied", 403

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if admin_only(): return admin_only()

    products = list(db.products.find({}))
    total_revenue = sum(p.get("total_amount_sold", 0) for p in products)
    total_cost = sum(p.get("batch_cost", 0) for p in products)
    total_profit = total_revenue - total_cost
    total_quantity = sum(p.get("total_quantity_sold", 0) for p in products)
    user_count = db.users.count_documents({"role": {"$ne": "admin"}})

    return render_template("admin/dashboard.html",
                           total_revenue=total_revenue,
                           total_profit=total_profit,
                           total_quantity=total_quantity,
                           user_count=user_count)

@admin_bp.route("/manage-users", methods=["GET", "POST"])
@login_required
def manage_users():
    if admin_only(): return admin_only()

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        from models.user_model import User
        try:
            User.register(username, password, role="sales")
            flash(f"User '{username}' added successfully!", "success")
        except ValueError:
            flash("Username already exists.", "error")
        return redirect(url_for("admin.manage_users"))

    users = list(db.users.find({"role": {"$ne": "admin"}}))
    return render_template("admin/manage_users.html", users=users)

@admin_bp.route("/delete-user/<id>")
@login_required
def delete_user(id):
    if admin_only(): return admin_only()
    db.users.delete_one({"_id": ObjectId(id)})
    flash("User deleted.", "info")
    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/export")
@login_required
def export():
    if admin_only(): return admin_only()

    products = list(db.products.find({}))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Batch", "Qty Sold", "Revenue", "Cost", "Profit"])
    for p in products:
        profit = p.get("total_amount_sold", 0) - p.get("batch_cost", 0)
        writer.writerow([
            p.get("name", ""),
            p.get("total_quantity_sold", 0),
            p.get("total_amount_sold", 0),
            p.get("batch_cost", 0),
            profit
        ])
    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="business_report.csv")

@admin_bp.route("/audit")
@login_required
def audit_log():
    if current_user.role != "admin":
        return "Access denied", 403

    sales = list(db.sales.find({}).sort("date", -1).limit(50))
    return render_template("audit_log.html", sales=sales)


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if admin_only(): return admin_only()

    if request.method == "POST":
        shop_name = request.form.get("shop_name")
        contact = request.form.get("contact")
        db.settings.update_one({}, {"$set": {
            "shop_name": shop_name,
            "contact": contact
        }}, upsert=True)
        flash("Settings updated.", "success")
        return redirect(url_for("admin.settings"))

    settings = db.settings.find_one({}) or {}
    return render_template("settings.html", settings=settings)
