# models/sale_model.py
from datetime import datetime
from bson import ObjectId
from utils.db import get_db

db = get_db()

class Sale:
    """
    Sale model for recording and analyzing product sales.
    Each sale is linked to a product and includes quantity, amount, and timestamp.
    """

    @staticmethod
    def log_sale(product_id, quantity, unit_price=None):
        """
        Logs a sale and returns the inserted sale document.
        If unit_price is not provided, it uses the product's current price.
        """
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise ValueError("Product not found")

        qty = int(quantity)
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        price = float(unit_price) if unit_price is not None else float(product.get("unit_price", 0.0))
        if price <= 0:
            raise ValueError("Unit price must be positive")

        amount = qty * price
        sale = {
            "product_id": ObjectId(product_id),
            "product_name": product.get("name", "Unknown"),
            "quantity": qty,
            "unit_price": price,
            "amount": amount,
            "date": datetime.utcnow()
        }

        db.sales.insert_one(sale)

        # Update product totals and stock
        db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {
                    "total_quantity_sold": qty,
                    "total_amount_sold": amount,
                    "stock_quantity": -qty
                },
                "$push": {"sales": {"quantity": qty, "amount": amount, "date": sale["date"]}}
            }
        )

        return sale

    @staticmethod
    def get_totals_by_product(product_id):
        """
        Returns total quantity and revenue for a given product.
        """
        pipeline = [
            {"$match": {"product_id": ObjectId(product_id)}},
            {"$group": {
                "_id": "$product_id",
                "total_quantity": {"$sum": "$quantity"},
                "total_amount": {"$sum": "$amount"}
            }}
        ]
        result = list(db.sales.aggregate(pipeline))
        if result:
            return result[0]["total_quantity"], result[0]["total_amount"]
        return 0, 0

    @staticmethod
    def get_recent_sales(limit=20):
        """
        Returns the most recent sales across all products.
        """
        return list(db.sales.find({}).sort("date", -1).limit(limit))

    @staticmethod
    def get_sales_by_day(days=7):
        """
        Returns total sales per day for the last `days` days.
        Useful for trend charts.
        """
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {"date": {"$gte": start_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$date"},
                    "month": {"$month": "$date"},
                    "day": {"$dayOfMonth": "$date"}
                },
                "total_amount": {"$sum": "$amount"},
                "total_quantity": {"$sum": "$quantity"}
            }},
            {"$sort": {"_id": 1}}
        ]
        return list(db.sales.aggregate(pipeline))

    @staticmethod
    def delete_sale(sale_id):
        """
        Deletes a sale by ID and optionally adjusts product totals.
        """
        sale = db.sales.find_one({"_id": ObjectId(sale_id)})
        if not sale:
            return False

        db.sales.delete_one({"_id": ObjectId(sale_id)})

        # Optional: reverse product totals
        db.products.update_one(
            {"_id": sale["product_id"]},
            {
                "$inc": {
                    "total_quantity_sold": -sale["quantity"],
                    "total_amount_sold": -sale["amount"],
                    "stock_quantity": sale["quantity"]
                }
            }
        )
        return True
