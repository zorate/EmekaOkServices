# routes/analytics_routes.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.db import get_db
from bson import ObjectId
from datetime import datetime, timedelta

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")
db = get_db()

@analytics_bp.route("/")
@login_required
def analytics():
    if current_user.role != "admin":
        return "Access denied", 403

    products = list(db.products.find({}))
    total_revenue = sum(p.get("total_amount_sold", 0) for p in products)
    total_cost = sum(p.get("batch_cost", 0) for p in products)
    total_profit = total_revenue - total_cost

    # 7-day trend
    start_date = datetime.utcnow() - timedelta(days=7)
    pipeline = [
        {"$match": {"date": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dayOfWeek": "$date"},
            "total": {"$sum": "$amount"}
        }},
        {"$sort": {"_id": 1}}
    ]
    trend = list(db.sales.aggregate(pipeline))

    return render_template("analytics.html",
                           products=products,
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           total_profit=total_profit,
                           trend=trend)
