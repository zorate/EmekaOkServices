# routes/product_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.product_model import Product
from models.sale_model import Sale
from utils.db import get_db
from bson import ObjectId
from datetime import datetime

product_bp = Blueprint("product", __name__, url_prefix="/products")
db = get_db()

@product_bp.route("/dashboard")
@login_required
def dashboard():
    # Fetch all products
    products_cursor = db.products.find().sort("created_at", -1)
    products = []

    for p in products_cursor:
        # Aggregate sales for this batch
        sales = list(db.sales.find({"product_id": ObjectId(p["_id"])}))
        total_amount_sold = sum(s["amount"] for s in sales)
        total_quantity_sold = sum(s["quantity"] for s in sales)

        batch_cost = p.get("batch_cost", p.get("cost_price", 0))

        products.append({
            "_id": p["_id"],
            "name": p["name"],
            "status": p.get("status", "active"),
            "cost_price": p.get("cost_price", 0),
            "sell_price": p.get("unit_price", 0),
            "quantity": p.get("stock_quantity", 0),
            "batch_cost": batch_cost,
            "total_amount_sold": total_amount_sold,
            "total_quantity_sold": total_quantity_sold,
            "created_at": p.get("created_at")
        })

    # Count active batches
    active_count = sum(1 for p in products if p["status"] == "active")

    # Get today's sales for current user
    today = datetime.utcnow().date()
    user_sales_today = list(db.sales.find({
        "user_id": current_user.id,
        "date": {
            "$gte": datetime(today.year, today.month, today.day),
            "$lt": datetime(today.year, today.month, today.day, 23, 59, 59)
        }
    }))
    my_sales_today = sum(s["amount"] for s in user_sales_today)
    my_items_sold = sum(s["quantity"] for s in user_sales_today)

    # Recent sales by current user
    recent_sales = list(db.sales.find({"user_id": current_user.id}).sort("date", -1).limit(5))

    return render_template("dashboard.html",
                           products=products,
                           active_count=active_count,
                           my_sales_today=my_sales_today,
                           my_items_sold=my_items_sold,
                           recent_sales=recent_sales)

@product_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name").strip()
        batch_cost = float(request.form.get("batch_cost", 0))
        stock_quantity = int(request.form.get("stock_quantity", 0))
        unit_price = float(request.form.get("unit_price", 0))

        if Product.get_active_count() >= 15:
            flash("You can only have 15 active products at once.", "error")
            return redirect(url_for("product.dashboard"))

        Product.create(name, batch_cost, stock_quantity, unit_price)
        flash(f"Product '{name}' added successfully!", "success")
        return redirect(url_for("product.dashboard"))

    return render_template("add_product.html")

@product_bp.route("/finish/<id>")
@login_required
def mark_finished(id):
    if current_user.role != "admin":
        flash("Access denied: only admin can finish batches.", "error")
        return redirect(url_for("product.dashboard"))

    Product.mark_finished(id)
    flash("Product marked as finished.", "info")
    return redirect(url_for("product.dashboard"))
