# Veggimart

Online vegetable store built with Django and **MySQL/MariaDB** (no SQLite).

## Setup

1. Create the database (MySQL or MariaDB):

   ```sql
   CREATE DATABASE veggimart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'veggimart'@'localhost' IDENTIFIED BY 'choose-a-password';
   GRANT ALL PRIVILEGES ON veggimart.* TO 'veggimart'@'localhost';
   ```

2. Install and configure:

   ```bash
   python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   export DB_PASSWORD='choose-a-password'               # Windows: set DB_PASSWORD=...
   # optional: DB_NAME, DB_USER, DB_HOST, DB_PORT, DJANGO_SECRET_KEY, DJANGO_DEBUG
   ```

3. Create tables, sample data, admin user, run:

   ```bash
   python manage.py migrate
   python manage.py seed_veggies
   python manage.py createsuperuser
   python manage.py runserver
   ```

Open http://127.0.0.1:8000 (store) and http://127.0.0.1:8000/admin (manage products and orders).

## Features
Categories, search, sort/organic filter, pagination, product pages, session cart (stock-capped),
checkout (guest or logged in, atomic stock deduction), order history, signup/login, Django admin.
