# Electronics Product Catalog & Installment Management App

A professional electronics showroom web application built with Flask, SQLite, SQLAlchemy, Bootstrap 5, and Jinja2.

## Features

- Public showroom landing page
- Product browsing by category
- Search, filtering, pagination, sorting
- Product detail pages with specifications and installment plans
- Product-specific WhatsApp inquiry links throughout the catalog
- Installment plan management
- Secure admin dashboard with login
- Shop settings management
- Product and category upload support
- Responsive design for desktop and mobile devices
- Basic SEO support and error pages

## Setup

1. Install Python 3.10+
2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the environment:

   - Windows PowerShell:

     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

   - Command Prompt:

     ```cmd
     venv\Scripts\activate.bat
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Set a persistent secret key before deployment. Generate one with:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Set the generated value in the `SECRET_KEY` environment variable. For HTTPS deployments, set `SESSION_COOKIE_SECURE=true`. Without `SECRET_KEY`, the app generates a temporary random key at startup, so browser sessions will expire when the process restarts.

6. Initialize the database:

   ```bash
   python -c "from app import create_app; create_app()"
   ```

7. Run the app:

   ```bash
   python app.py
   ```

8. Open the app at:

   ```text
   http://127.0.0.1:5000/
   ```

## Default Admin

The application creates a default admin account automatically on first startup.

- Username: `admin`
- Password: `admin123`

Change this immediately after login in production.

## Admin Pages

- `/admin/login`
- `/admin`
- `/admin/products`
- `/admin/categories`
- `/admin/installments`
- `/admin/settings`
- `/admin/design` — global storefront theme, hero content/image, and homepage section visibility/order
- `/admin/newsletter` — review and remove email update subscribers

## Notes

- All catalog data is stored in the database.
- Products, categories, plans, and shop information can be managed from the admin panel.
- No real storefront pricing is hard-coded into the application.
- This is a WhatsApp inquiry catalog, not an online ordering or payment system. Each product's WhatsApp button opens a prefilled message to the shop, which confirms availability, delivery, and pricing directly with the customer.
- Product ratings, customer reviews, and color variants are not shown because the current product schema does not store those values.

## Frontend architecture

Public pages extend `templates/base.html`. Shared public layout is kept in
`templates/components/`:

- `navbar.html`, `footer.html`, and `flash_messages.html` control the shared
  navigation, footer/mobile navigation, and flash alerts.
- `hero.html`, `search_bar.html`, and `category_card.html` are included by the
  pages that use those elements.
- `templates/_product_card.html` is the shared product card used by product
  listings.
- Admin pages continue to extend `templates/admin/layout.html`; the shared
  flash-message component is used there too.

Global design tokens live in `static/css/variables.css`, which is loaded before
the existing stylesheets by both public and admin layouts. Change
`--design-primary`, `--design-background`, `--design-font-family`,
`--design-button-radius`, `--design-card-radius`, and
`--design-spacing-section` there to update the corresponding shared styles
while keeping the current CSS cascade. The dark admin theme has separate
`--design-showroom-*` tokens.

To update a shared navigation/footer/hero/search/category-card layout, edit its
component once. To update product-card markup, edit
`templates/_product_card.html`. Existing Flask routes, page templates, and
admin forms continue to provide their own content and behavior.

The shared footer uses the shop profile's configured logo, description, hours,
phone numbers, email, address, map, and social links. Phone/email/map/social
actions are only rendered as working links when the corresponding setting is
available; WhatsApp opens the existing configured shop contact. Footer
navigation points to the existing storefront routes.

The Website Design page saves its settings separately in the `website_design`
database table. On startup, SQLAlchemy's `create_all()` creates that new table
when it is missing; it does not replace existing catalog tables or records.
The controls cover global storefront colors, built-in font choices, button and
card corner radius, section spacing, hero heading/subtitle/button/image, and
visibility/order of the homepage search, hero, categories, featured products,
new arrivals, installment promotion, and newsletter areas. Uploaded hero
artwork is stored under the existing uploads directory. Resetting design
settings does not delete catalog content.

The homepage also includes an installment-plan promotion and email updates
signup. Newsletter addresses are validated, stored separately in the
`newsletter_subscriber` table after signup, and manageable by an authenticated
admin at `/admin/newsletter`. This stores the opt-in list; it does not send
email automatically and requires an email delivery service for campaigns.

## Local UI verification

Run the existing Flask application locally with `python app.py`, then check the
homepage, products, categories, category details, search, shop, product
details, contact, installments, and admin pages in a browser. Existing database
records and admin credentials are required to exercise the corresponding
content and authenticated workflows.
