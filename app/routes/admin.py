from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.design import (
    DEFAULT_DESIGN_SETTINGS,
    FONT_FAMILIES,
    normalize_design_settings,
    parse_design_form,
)
from app.extensions import db
from app.models import (
    AdminUser,
    Category,
    InstallmentPlan,
    Product,
    ProductImage,
    ProductSpecification,
    ShopSettings,
    WebsiteDesign,
)
from app.utils import allowed_image, save_uploaded_file

admin_bp = Blueprint("admin", __name__)


def product_query():
    return Product.query.order_by(Product.created_at.desc())


def category_query():
    return Category.query.order_by(Category.display_order.asc(), Category.name.asc())


def product_code_exists(product_code, exclude_product_id=None):
    query = Product.query.filter(Product.product_code.ilike(product_code))
    if exclude_product_id is not None:
        query = query.filter(Product.id != exclude_product_id)
    return query.first() is not None


def category_name_exists(name, exclude_category_id=None):
    query = Category.query.filter(Category.name.ilike(name))
    if exclude_category_id is not None:
        query = query.filter(Category.id != exclude_category_id)
    return query.first() is not None


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    categories = Category.query.count()
    featured_products = Product.query.filter_by(featured=True).count()
    plans = InstallmentPlan.query.count()
    stock_summary = {
        "in_stock": Product.query.filter_by(stock_status="In Stock").count(),
        "low_stock": Product.query.filter(Product.stock_status.ilike("%Low%")) .count(),
        "out_of_stock": Product.query.filter(Product.stock_status.ilike("%Out%")) .count(),
    }

    recent_products = product_query().limit(6).all()
    recent_categories = category_query().limit(6).all()
    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        active_products=active_products,
        categories=categories,
        featured_products=featured_products,
        plans=plans,
        stock_summary=stock_summary,
        recent_products=recent_products,
        recent_categories=recent_categories,
    )


@admin_bp.route("/products")
@login_required
def products():
    items = product_query().all()
    return render_template("admin/products.html", products=items)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        product_code = request.form.get("product_code", "").strip()
        if not product_code:
            flash("Product code is required.", "danger")
            return redirect(url_for("admin.add_product"))
        if product_code_exists(product_code):
            flash("Product code already exists.", "danger")
            return redirect(url_for("admin.add_product"))

        product = Product(
            category_id=request.form.get("category_id", type=int),
            product_code=product_code,
            name=request.form.get("name", "").strip(),
            brand=request.form.get("brand", "").strip(),
            model=request.form.get("model", "").strip(),
            short_description=request.form.get("short_description", "").strip(),
            full_description=request.form.get("full_description", "").strip(),
            mrp=request.form.get("mrp", type=float),
            cash_price=request.form.get("cash_price", type=float),
            down_payment=request.form.get("down_payment", type=float),
            stock_status=request.form.get("stock_status", "In Stock").strip() or "In Stock",
            featured=bool(request.form.get("featured")),
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(product)
        db.session.flush()

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            path = save_uploaded_file(image_file, "products")
            if path:
                product.image = path

        for file in request.files.getlist("gallery_images"):
            if file and file.filename:
                path = save_uploaded_file(file, "products")
                if path:
                    db.session.add(ProductImage(product_id=product.id, image_path=path))

        specs_text = request.form.get("specifications", "")
        for line in specs_text.splitlines():
            if not line.strip():
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                db.session.add(ProductSpecification(product_id=product.id, name=key.strip(), value=value.strip()))

        db.session.commit()
        flash("Product added successfully.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", product=None, categories=category_query().all())


@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.category_id = request.form.get("category_id", type=int)
        product.product_code = request.form.get("product_code", "").strip()
        if not product.product_code:
            flash("Product code is required.", "danger")
            return redirect(url_for("admin.edit_product", product_id=product.id))
        if product_code_exists(product.product_code, exclude_product_id=product.id):
            flash("Product code already exists.", "danger")
            return redirect(url_for("admin.edit_product", product_id=product.id))
        product.name = request.form.get("name", "").strip()
        product.brand = request.form.get("brand", "").strip()
        product.model = request.form.get("model", "").strip()
        product.short_description = request.form.get("short_description", "").strip()
        product.full_description = request.form.get("full_description", "").strip()
        product.mrp = request.form.get("mrp", type=float)
        product.cash_price = request.form.get("cash_price", type=float)
        product.down_payment = request.form.get("down_payment", type=float)
        product.stock_status = request.form.get("stock_status", "In Stock").strip() or "In Stock"
        product.featured = bool(request.form.get("featured"))
        product.is_active = bool(request.form.get("is_active"))
        product.updated_at = datetime.utcnow()

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            path = save_uploaded_file(image_file, "products")
            if path:
                product.image = path

        gallery_files = request.files.getlist("gallery_images")
        for file in gallery_files:
            if file and file.filename:
                path = save_uploaded_file(file, "products")
                if path:
                    db.session.add(ProductImage(product_id=product.id, image_path=path))

        existing_specs = ProductSpecification.query.filter_by(product_id=product.id).all()
        for item in existing_specs:
            db.session.delete(item)

        specs_text = request.form.get("specifications", "")
        for line in specs_text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                db.session.add(ProductSpecification(product_id=product.id, name=key.strip(), value=value.strip()))

        db.session.commit()
        flash("Product updated successfully.", "success")
        return redirect(url_for("admin.products"))

    specs = [f"{spec.name}: {spec.value}" for spec in product.specifications]
    return render_template("admin/product_form.html", product=product, categories=category_query().all(), specifications="\n".join(specs))


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/categories")
@login_required
def categories():
    items = category_query().all()
    return render_template("admin/categories.html", categories=items)


@admin_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
def add_category():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("admin.add_category"))
        if category_name_exists(name):
            flash("Category name already exists.", "danger")
            return redirect(url_for("admin.add_category"))

        category = Category(
            name=name,
            description=request.form.get("description", "").strip(),
            display_order=request.form.get("display_order", type=int) or 0,
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(category)
        db.session.flush()

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            path = save_uploaded_file(image_file, "categories")
            if path:
                category.image = path

        db.session.commit()
        flash("Category added successfully.", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/category_form.html", category=None)


@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == "POST":
        category.name = request.form.get("name", "").strip()
        if not category.name:
            flash("Category name is required.", "danger")
            return redirect(url_for("admin.edit_category", category_id=category.id))
        if category_name_exists(category.name, exclude_category_id=category.id):
            flash("Category name already exists.", "danger")
            return redirect(url_for("admin.edit_category", category_id=category.id))
        category.description = request.form.get("description", "").strip()
        category.display_order = request.form.get("display_order", type=int) or 0
        category.is_active = bool(request.form.get("is_active"))

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            path = save_uploaded_file(image_file, "categories")
            if path:
                category.image = path

        db.session.commit()
        flash("Category updated successfully.", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/category_form.html", category=category)


@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted successfully.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/installments")
@login_required
def installments():
    plans = InstallmentPlan.query.order_by(InstallmentPlan.duration_months.asc()).all()
    return render_template("admin/installments.html", plans=plans)


@admin_bp.route("/installments/add", methods=["GET", "POST"])
@login_required
def add_installment():
    if request.method == "POST":
        plan = InstallmentPlan(
            product_id=request.form.get("product_id", type=int),
            duration_months=request.form.get("duration_months", type=int),
            down_payment=request.form.get("down_payment", type=float),
            monthly_installment=request.form.get("monthly_installment", type=float),
            total_amount=request.form.get("total_amount", type=float),
            cash_price=request.form.get("cash_price", type=float),
            processing_fee=request.form.get("processing_fee", type=float),
            notes=request.form.get("notes", "").strip(),
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(plan)
        db.session.commit()
        flash("Installment plan added successfully.", "success")
        return redirect(url_for("admin.installments"))

    return render_template("admin/installment_form.html", plan=None, products=Product.query.filter_by(is_active=True).all())


@admin_bp.route("/installments/edit/<int:plan_id>", methods=["GET", "POST"])
@login_required
def edit_installment(plan_id):
    plan = InstallmentPlan.query.get_or_404(plan_id)

    if request.method == "POST":
        plan.product_id = request.form.get("product_id", type=int)
        plan.duration_months = request.form.get("duration_months", type=int)
        plan.down_payment = request.form.get("down_payment", type=float)
        plan.monthly_installment = request.form.get("monthly_installment", type=float)
        plan.total_amount = request.form.get("total_amount", type=float)
        plan.cash_price = request.form.get("cash_price", type=float)
        plan.processing_fee = request.form.get("processing_fee", type=float)
        plan.notes = request.form.get("notes", "").strip()
        plan.is_active = bool(request.form.get("is_active"))
        db.session.commit()
        flash("Installment plan updated successfully.", "success")
        return redirect(url_for("admin.installments"))

    return render_template("admin/installment_form.html", plan=plan, products=Product.query.filter_by(is_active=True).all())


@admin_bp.route("/installments/delete/<int:plan_id>", methods=["POST"])
@login_required
def delete_installment(plan_id):
    plan = InstallmentPlan.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    flash("Installment plan deleted successfully.", "success")
    return redirect(url_for("admin.installments"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings = ShopSettings.query.first() or ShopSettings()

    if request.method == "POST":
        settings.shop_name = request.form.get("shop_name", "ElectroCart").strip() or "ElectroCart"
        settings.address = request.form.get("address", "").strip()
        settings.phone1 = request.form.get("phone1", "").strip()
        settings.phone2 = request.form.get("phone2", "").strip()
        settings.whatsapp = request.form.get("whatsapp", "").strip()
        settings.email = request.form.get("email", "").strip()
        settings.opening_hours = request.form.get("opening_hours", "").strip()
        settings.facebook = request.form.get("facebook", "").strip()
        settings.instagram = request.form.get("instagram", "").strip()
        settings.google_maps = request.form.get("google_maps", "").strip()
        settings.about_shop = request.form.get("about_shop", "").strip()
        settings.footer_text = request.form.get("footer_text", "").strip()

        logo = request.files.get("logo")
        if logo and logo.filename:
            path = save_uploaded_file(logo, "logo")
            if path:
                settings.logo = path

        if not settings.id:
            db.session.add(settings)

        db.session.commit()
        flash("Shop settings updated successfully.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", settings=settings)


@admin_bp.route("/design", methods=["GET", "POST"])
@login_required
def design():
    website_design = WebsiteDesign.query.first()
    settings = normalize_design_settings(
        website_design.settings if website_design else DEFAULT_DESIGN_SETTINGS
    )

    if request.method == "POST":
        if request.form.get("action") == "reset":
            settings = normalize_design_settings(DEFAULT_DESIGN_SETTINGS)
            if website_design is None:
                website_design = WebsiteDesign()
                db.session.add(website_design)
            website_design.settings = settings
            db.session.commit()
            flash("Website design restored to its default settings.", "success")
            return redirect(url_for("admin.design"))

        values, errors = parse_design_form(request.form, settings)
        hero_image = request.files.get("hero_image")
        if hero_image and hero_image.filename and not allowed_image(hero_image.filename):
            errors.append("Hero image must be a JPG, JPEG, PNG, or WEBP image.")

        if errors:
            for error in errors:
                flash(error, "danger")
            settings.update(values)
            return render_template(
                "admin/design.html",
                design=settings,
                font_families=FONT_FAMILIES,
            )

        if hero_image and hero_image.filename:
            image_path = save_uploaded_file(hero_image, "design")
            if not image_path:
                flash("The hero image could not be saved. Please try another image.", "danger")
                settings.update(values)
                return render_template(
                    "admin/design.html",
                    design=settings,
                    font_families=FONT_FAMILIES,
                )
            values["hero_image"] = image_path

        if website_design is None:
            website_design = WebsiteDesign()
            db.session.add(website_design)
        website_design.settings = values
        db.session.commit()
        flash("Website design updated successfully.", "success")
        return redirect(url_for("admin.design"))

    return render_template(
        "admin/design.html",
        design=settings,
        font_families=FONT_FAMILIES,
    )
