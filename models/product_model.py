# models/product_model.py
from datetime import datetime
from bson import ObjectId
from utils.db import get_db

db = get_db()

class Product:
    """
    Product model with sales-friendly helpers:
    - Create products with stock and price
    - Record sales (updates totals and stock)
    - Restock and reprice
    - Calculate profit
    """

    @staticmethod
    def create(name, batch_cost, stock_quantity=0, unit_price=0.0, status="active"):
        doc = {
            "name": name.strip(),
            "batch_cost": float(batch_cost),
            "stock_quantity": int(stock_quantity),
            "unit_price": float(unit_price),
            "status": status,
            "created_at": datetime.utcnow(),
            "total_quantity_sold": 0,
            "total_amount_sold": 0.0,
            "sales": []  # [{quantity, amount, date}]
        }
        result = db.products.insert_one(doc)
        return result.inserted_id

    @staticmethod
    def get_all():
        return list(db.products.find({}).sort("created_at", -1))

    @staticmethod
    def get_active():
        return list(db.products.find({"status": "active"}).sort("created_at", -1))

    @staticmethod
    def get_active_count():
        return db.products.count_documents({"status": "active"})

    @staticmethod
    def get_by_id(product_id):
        return db.products.find_one({"_id": ObjectId(product_id)})

    @staticmethod
    def mark_finished(product_id):
        return db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"status": "finished"}}
        )

    @staticmethod
    def delete(product_id):
        return db.products.delete_one({"_id": ObjectId(product_id)})

    @staticmethod
    def set_price(product_id, unit_price):
        return db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"unit_price": float(unit_price)}}
        )

    @staticmethod
    def restock(product_id, quantity):
        return db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"stock_quantity": int(quantity)}}
        )

    @staticmethod
    def record_sale(product_id, quantity, unit_price=None):
        """
        Records a sale:
        - Uses current unit_price unless overridden
        - Decreases stock
        - Increments totals
        - Appends to sales history
        """
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise ValueError("Product not found")

        qty = int(quantity)
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        # Use provided price or stored unit price
        price = float(unit_price) if unit_price is not None else float(product.get("unit_price", 0.0))
        if price <= 0:
            raise ValueError("Unit price must be positive")

        current_stock = int(product.get("stock_quantity", 0))
        if current_stock < qty:
            raise ValueError("Insufficient stock")

        amount = qty * price
        sale = {"quantity": qty, "amount": amount, "date": datetime.utcnow()}

        return db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {
                    "stock_quantity": -qty,
                    "total_quantity_sold": qty,
                    "total_amount_sold": amount
                },
                "$push": {"sales": sale}
            }
        )

    @staticmethod
    def update(product_id, **fields):
        """
        Update allowed fields safely.
        Allowed keys: name, batch_cost, status, unit_price, stock_quantity
        """
        allowed = {"name", "batch_cost", "status", "unit_price", "stock_quantity"}
        payload = {}
        for k, v in fields.items():
            if k in allowed:
                if k in {"batch_cost", "unit_price"}:
                    payload[k] = float(v)
                elif k in {"stock_quantity"}:
                    payload[k] = int(v)
                elif k == "name":
                    payload[k] = str(v).strip()
                else:
                    payload[k] = v
        if not payload:
            return None
        return db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": payload}
        )

    @staticmethod
    def compute_profit(product_id):
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return 0.0
        return float(product.get("total_amount_sold", 0.0)) - float(product.get("batch_cost", 0.0))

    @staticmethod
    def search_by_name(query, limit=20):
        """
        Case-insensitive partial match search by product name.
        """
        return list(
            db.products.find({"name": {"$regex": query, "$options": "i"}})
                       .sort("created_at", -1)
                       .limit(int(limit))
        )
