# routes/sale_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models.product_model import Product
from models.sale_model import Sale
from bson import ObjectId
from utils.db import get_db
from datetime import datetime



sale_bp = Blueprint("sale", __name__, url_prefix="/sales")

db = get_db()

@sale_bp.route("/log/<id>", methods=["GET", "POST"])
@login_required
def log_sale(id):
    product = db.products.find_one({"_id": ObjectId(id)})
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.dashboard"))

    # Compute total quantity and total amount sold so far
    sales = list(db.sales.find({"product_id": ObjectId(id)}))
    total_quantity_sold = sum(s["quantity"] for s in sales)
    total_amount_sold = sum(s["amount"] for s in sales)

    if request.method == "POST":
        quantity = int(request.form.get("quantity", 0))
        amount = float(request.form.get("amount", 0))

        if quantity <= 0 or amount <= 0:
            flash("Invalid sale data.", "error")
            return redirect(request.url)

        # Audit log: include user info
        sale_record = {
            "product_id": ObjectId(id),
            "product_name": product.get("name", "Unknown"),
            "quantity": quantity,
            "amount": amount,
            "unit_price": amount / quantity,
            "user_id": current_user.id,
            "username": current_user.username,
            "date": datetime.utcnow()
        }

        db.sales.insert_one(sale_record)

        # Update product totals
        db.products.update_one(
            {"_id": ObjectId(id)},
            {
                "$inc": {
                    "total_quantity_sold": quantity,
                    "total_amount_sold": amount,
                    "stock_quantity": -quantity
                },
                "$push": {"sales": {
                    "quantity": quantity,
                    "amount": amount,
                    "date": sale_record["date"]
                }}
            }
        )

        flash(f"Sale logged for {product['name']}", "success")
        return redirect(url_for("product.dashboard"))

    return render_template(
        "log_sale.html",
        product=product,
        total_quantity_sold=total_quantity_sold,
        total_amount_sold=total_amount_sold
    )

@sale_bp.route("/recent-sales")
@login_required
def recent_sales():
    sales = list(db.sales.find().sort("date", -1).limit(100))  # or filter by user
    return render_template("admin/recent_sales.html", sales=sales)


@sale_bp.route("/quick-sale", methods=["GET", "POST"])
@login_required
def quick_sale():
    # Only show active batches
    products = list(db.products.find({"status": "active"}).sort("created_at", -1))

    if request.method == "POST":
        product_id = request.form.get("product_id")
        quantity = int(request.form.get("quantity", 0))
        amount = float(request.form.get("amount", 0))

        if not product_id or quantity <= 0 or amount <= 0:
            flash("Please enter valid quantity and amount.", "error")
            return redirect(url_for("sale.quick_sale"))

        # Save sale
        sale = {
            "product_id": product_id,
            "product_name": db.products.find_one({"_id": product_id})["name"],
            "quantity": quantity,
            "amount": amount,
            "user_id": current_user.id,
            "username": current_user.username,
            "date": datetime.utcnow()
        }
        db.sales.insert_one(sale)

        # Update product totals
        db.products.update_one(
            {"_id": product_id},
            {
                "$inc": {
                    "total_quantity_sold": quantity,
                    "total_amount_sold": amount
                }
            }
        )

        flash("Sale logged successfully!", "success")
        return redirect(url_for("product.dashboard"))

    return render_template("admin/quick_sale.html", products=products)
