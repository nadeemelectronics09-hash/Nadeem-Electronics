import os

from flask import Flask

from .extensions import csrf, db, login_manager
from .design import build_design_css, normalize_design_settings
from .models import AdminUser, Category, ShopSettings, WebsiteDesign
from .routes.admin import admin_bp
from .routes.public import public_bp
from .utils import whatsapp_product_url, whatsapp_url


def create_app():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(AdminUser, int(user_id))

    @app.context_processor
    def inject_globals():
        settings = ShopSettings.query.first()
        website_design = WebsiteDesign.query.first()
        design_settings = normalize_design_settings(
            website_design.settings if website_design else None
        )
        categories = (
            Category.query.filter_by(is_active=True)
            .order_by(Category.display_order.asc(), Category.name.asc())
            .all()
        )
        return {
            "site_settings": settings,
            "design_settings": design_settings,
            "design_css": build_design_css(design_settings),
            "nav_categories": categories,
            "whatsapp_contact_url": whatsapp_url(
                settings,
                "Assalam-o-Alaikum, I would like to ask about your electronics products.",
            ),
            "whatsapp_message_url": lambda message: whatsapp_url(settings, message),
            "whatsapp_product_url": lambda product: whatsapp_product_url(settings, product),
        }

    with app.app_context():
        db.create_all()

        if not AdminUser.query.first():
            default_user = AdminUser(username="admin")
            default_user.set_password("admin123")
            db.session.add(default_user)

        if not ShopSettings.query.first():
            db.session.add(
                ShopSettings(
                    shop_name="Nadeem Electronics",
                    address="Main Market, Lahore, Pakistan",
                    phone1="+92 300 1234567",
                    phone2="+92 321 7654321",
                    whatsapp="+92 300 1234567",
                    email="sales@electrocart.example",
                    opening_hours="Mon-Sat: 9:00 AM - 8:00 PM",
                    facebook="#",
                    instagram="#",
                    google_maps="#",
                    about_shop="Your trusted electronics showroom for quality products and flexible installment solutions.",
                    footer_text="© 2025 Nadeem Electronics. All rights reserved.",
                )
            )

        db.session.commit()

    return app
