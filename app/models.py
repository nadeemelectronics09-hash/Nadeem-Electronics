from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship("Product", backref="category", lazy=True, cascade="all, delete-orphan")


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    product_code = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    model = db.Column(db.String(150), nullable=False)
    short_description = db.Column(db.Text)
    full_description = db.Column(db.Text)
    mrp = db.Column(db.Numeric(10, 2))
    cash_price = db.Column(db.Numeric(10, 2))
    down_payment = db.Column(db.Numeric(10, 2))
    stock_status = db.Column(db.String(80), default="In Stock")
    featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship("ProductImage", backref="product", lazy=True, cascade="all, delete-orphan")
    specifications = db.relationship("ProductSpecification", backref="product", lazy=True, cascade="all, delete-orphan")
    installment_plans = db.relationship("InstallmentPlan", backref="product", lazy=True, cascade="all, delete-orphan")


class ProductImage(db.Model):
    __tablename__ = "product_image"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200))


class ProductSpecification(db.Model):
    __tablename__ = "product_specification"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.String(255), nullable=False)


class InstallmentPlan(db.Model):
    __tablename__ = "installment_plan"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    down_payment = db.Column(db.Numeric(10, 2))
    monthly_installment = db.Column(db.Numeric(10, 2))
    total_amount = db.Column(db.Numeric(10, 2))
    cash_price = db.Column(db.Numeric(10, 2))
    processing_fee = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ShopSettings(db.Model):
    __tablename__ = "shop_settings"

    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(200), nullable=False, default="ElectroCart")
    logo = db.Column(db.String(255))
    address = db.Column(db.String(300))
    phone1 = db.Column(db.String(50))
    phone2 = db.Column(db.String(50))
    whatsapp = db.Column(db.String(50))
    email = db.Column(db.String(150))
    opening_hours = db.Column(db.String(200))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    google_maps = db.Column(db.String(255))
    about_shop = db.Column(db.Text)
    footer_text = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
