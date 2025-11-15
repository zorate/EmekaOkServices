# models.py
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.id = username  # for Flask-Login

class Product:
    def __init__(self, name, cost_price, sell_price, stock):
        self.name = name
        self.cost_price = cost_price
        self.sell_price = sell_price
        self.stock = stock
        self.created_at = datetime.utcnow()

class Sale:
    def __init__(self, product_id, quantity, amount):
        self.product_id = product_id
        self.quantity = quantity
        self.amount = amount
        self.date = datetime.utcnow()
