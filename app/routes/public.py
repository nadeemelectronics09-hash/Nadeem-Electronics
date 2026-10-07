from decimal import InvalidOperation

from email_validator import EmailNotValidError, validate_email
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Category, InstallmentPlan, NewsletterSubscriber, Product, ShopSettings

public_bp = Blueprint("public", __name__)


@public_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # Older uploads were saved relative to the project root, including "uploads/".
    if filename.startswith("uploads/"):
        filename = filename[len("uploads/"):]
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@public_bp.route("/")
@public_bp.route("/dashboard")
def index():
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc(), Category.name.asc()).all()
    featured_products = Product.query.filter_by(is_active=True, featured=True).limit(6).all()
    latest_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    active_installment_count = (
        InstallmentPlan.query.join(Product)
        .filter(Product.is_active.is_(True), InstallmentPlan.is_active.is_(True))
        .count()
    )
    return render_template(
        "index.html",
        categories=categories,
        featured_products=featured_products,
        latest_products=latest_products,
        active_installment_count=active_installment_count,
    )


@public_bp.route("/products")
def products():
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "newest")
    category_filter = request.args.get("category", type=int)
    query = Product.query.filter_by(is_active=True)

    if category_filter:
        query = query.filter_by(category_id=category_filter)

    if request.args.get("search"):
        term = "%{}%".format(request.args.get("search"))
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.brand.ilike(term),
                Product.model.ilike(term),
                Product.product_code.ilike(term),
                Product.category.has(Category.name.ilike(term)),
            )
        )

    if sort == "price_low":
        query = query.order_by(Product.cash_price.asc().nullslast())
    elif sort == "price_high":
        query = query.order_by(Product.cash_price.desc().nullslast())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    return render_template("products.html", products_page=pagination, filters={"search": request.args.get("search"), "sort": sort, "category": category_filter})


@public_bp.route("/categories")
def categories():
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc(), Category.name.asc()).all()
    return render_template("categories.html", categories=categories)


@public_bp.route("/category/<int:category_id>")
def category_detail(category_id):
    category = Category.query.get_or_404(category_id)
    if not category.is_active:
        abort(404)

    products = Product.query.filter_by(category_id=category.id, is_active=True).order_by(Product.created_at.desc()).all()
    return render_template("category.html", category=category, products=products)


@public_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_active:
        abort(404)

    plans = sorted(
        (plan for plan in product.installment_plans if plan.is_active),
        key=lambda plan: plan.duration_months,
    )
    return render_template("product_detail.html", product=product, plans=plans)


@public_bp.route("/search")
def search():
    term = request.args.get("q", "", type=str).strip()
    if not term:
        return redirect(url_for("public.products"))

    products = (
        Product.query.filter_by(is_active=True)
        .filter(
            or_(
                Product.name.ilike(f"%{term}%"),
                Product.brand.ilike(f"%{term}%"),
                Product.model.ilike(f"%{term}%"),
                Product.product_code.ilike(f"%{term}%"),
                Product.category.has(Category.name.ilike(f"%{term}%")),
            )
        )
        .order_by(Product.created_at.desc())
        .all()
    )
    return render_template("search.html", products=products, search_term=term)


@public_bp.route("/installments")
def installments():
    plans = (
        InstallmentPlan.query.join(Product)
        .filter(Product.is_active.is_(True), InstallmentPlan.is_active.is_(True))
        .order_by(Product.name.asc(), InstallmentPlan.duration_months.asc())
        .all()
    )
    return render_template("installments.html", plans=plans)


@public_bp.route("/newsletter/subscribe", methods=["POST"])
def newsletter_subscribe():
    email = request.form.get("email", "").strip()
    if request.form.get("website", "").strip():
        return redirect(url_for("public.index", _anchor="newsletter"))

    try:
        normalized_email = validate_email(email, check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        flash("Enter a valid email address to subscribe.", "danger")
        return redirect(url_for("public.index", _anchor="newsletter"))

    if NewsletterSubscriber.query.filter_by(email=normalized_email).first():
        flash("This email is already subscribed to store updates.", "info")
        return redirect(url_for("public.index", _anchor="newsletter"))

    db.session.add(NewsletterSubscriber(email=normalized_email))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if NewsletterSubscriber.query.filter_by(email=normalized_email).first() is None:
            raise
        flash("This email is already subscribed to store updates.", "info")
    else:
        flash("You are subscribed to Nadeem Electronics store updates.", "success")
    return redirect(url_for("public.index", _anchor="newsletter"))


@public_bp.route("/shop")
def shop():
    settings = ShopSettings.query.first()
    page = request.args.get("page", 1, type=int)
    search_term = request.args.get("search", "", type=str).strip()
    category_id = request.args.get("category", type=int)
    brand = request.args.get("brand", "", type=str).strip()
    sort = request.args.get("sort", "newest", type=str)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    availability = request.args.get("availability", "", type=str)
    query = Product.query.filter_by(is_active=True)

    if search_term:
        term = f"%{search_term}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.brand.ilike(term),
                Product.model.ilike(term),
                Product.product_code.ilike(term),
                Product.category.has(Category.name.ilike(term)),
            )
        )
    if category_id:
        query = query.filter_by(category_id=category_id)
    if brand:
        query = query.filter(Product.brand == brand)
    if min_price is not None and min_price >= 0:
        query = query.filter(Product.cash_price >= min_price)
    if max_price is not None and max_price >= 0:
        query = query.filter(Product.cash_price <= max_price)
    if availability == "available":
        query = query.filter(~Product.stock_status.ilike("%out%"))
    elif availability == "unavailable":
        query = query.filter(Product.stock_status.ilike("%out%"))
    if request.args.get("discount") == "1":
        query = query.filter(
            Product.mrp.isnot(None),
            Product.cash_price.isnot(None),
            Product.mrp > Product.cash_price,
        )

    if sort == "price_low":
        query = query.order_by(Product.cash_price.asc().nullslast())
    elif sort == "price_high":
        query = query.order_by(Product.cash_price.desc().nullslast())
    elif sort == "name":
        query = query.order_by(Product.name.asc(), Product.id.asc())
    elif sort == "featured":
        query = query.order_by(Product.featured.desc(), Product.created_at.desc())
    else:
        sort = "newest"
        query = query.order_by(Product.created_at.desc())

    products_page = query.paginate(page=page, per_page=12, error_out=False)
    brands = [
        value[0]
        for value in db.session.query(Product.brand)
        .filter(Product.is_active.is_(True), Product.brand.isnot(None), Product.brand != "")
        .distinct()
        .order_by(Product.brand.asc())
        .all()
    ]
    category_counts = dict(
        db.session.query(Category.id, func.count(Product.id))
        .join(Product, Product.category_id == Category.id)
        .filter(Category.is_active.is_(True), Product.is_active.is_(True))
        .group_by(Category.id)
        .all()
    )
    price_bounds = (
        db.session.query(func.min(Product.cash_price), func.max(Product.cash_price))
        .filter(Product.is_active.is_(True), Product.cash_price.isnot(None))
        .one()
    )
    catalog_total = Product.query.filter_by(is_active=True).count()
    price_minimum = float(price_bounds[0]) if price_bounds[0] is not None else 0
    price_maximum = float(price_bounds[1]) if price_bounds[1] is not None else 0
    return render_template(
        "shop.html",
        settings=settings,
        products_page=products_page,
        brands=brands,
        catalog_total=catalog_total,
        category_counts=category_counts,
        price_minimum=price_minimum,
        price_maximum=price_maximum,
        filters={
            "search": search_term,
            "category": category_id,
            "brand": brand,
            "sort": sort,
            "min_price": min_price,
            "max_price": max_price,
            "availability": availability,
            "discount": request.args.get("discount") == "1",
        },
    )


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    settings = ShopSettings.query.first()
    if request.method == "POST":
        flash("Your inquiry has been recorded. Our team will reach out shortly.", "success")
        return redirect(url_for("public.contact"))
    return render_template("contact.html", settings=settings)


@public_bp.route("/403")
def forbidden():
    abort(403)


@public_bp.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@public_bp.errorhandler(403)
def forbidden_page(error):
    return render_template("403.html"), 403


@public_bp.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500
