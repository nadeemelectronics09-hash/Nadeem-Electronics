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

## Notes

- All catalog data is stored in the database.
- Products, categories, plans, and shop information can be managed from the admin panel.
- No real storefront pricing is hard-coded into the application.
- This is a WhatsApp inquiry catalog, not an online ordering or payment system. Each product's WhatsApp button opens a prefilled message to the shop, which confirms availability, delivery, and pricing directly with the customer.
- Product ratings, customer reviews, and color variants are not shown because the current product schema does not store those values.
