# Movies Store

Django movie catalog with search, accounts, reviews/reporting, a session cart,
and order history. Checkout records an order; it does not charge a payment
method or deliver movie files.

## Local setup

Use Python 3.12 or later:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Add movies and poster images through `/admin/`. A fresh checkout starts with an
empty catalog. Local databases, uploaded media, secrets and caches are not source
code and must not be committed. Existing local database files are preserved.

For persistent local login sessions, set `DJANGO_SECRET_KEY` in your environment.
Without it, development uses a fresh random key at each process start.

## Checks

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

GitHub Actions runs these on pushes and pull requests. Tests use an isolated test
database and cover accounts, permissions, review validation, cart validation,
checkout rollback, order privacy and historical prices.

## PythonAnywhere deployment

GitHub updates do not automatically update PythonAnywhere. Back up the hosted
SQLite database and media before deploying. In the hosted checkout, pull `main`,
activate the site's virtualenv, install requirements, migrate, and collect static
files. This update stops tracking `db.sqlite3`, so the first pull can remove the
hosted file from the working tree. Back it up outside the checkout first and
restore it immediately after pulling, before running migrations. Pause writes to
the app during this backup/deploy so no orders or reviews are lost:

```sh
# Run from the hosted checkout with the web app paused for maintenance.
# Choose a new backup filename; do not overwrite an existing backup.
cp -p db.sqlite3 ../moviesstore-pre-audit.sqlite3
git pull --ff-only origin main
cp -p ../moviesstore-pre-audit.sqlite3 db.sqlite3
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Configure these environment variables before the WSGI application loads Django
(for example in the PythonAnywhere WSGI configuration):

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY`: a new, long random secret generated privately on the server
- `DJANGO_ALLOWED_HOSTS=lynjung0804.pythonanywhere.com`

The previous source-controlled secret must be replaced; it remains exposed in
Git history. Rotation signs out existing sessions. Never commit the new secret.
Production refuses to start without a secret when debug is disabled. Production
enables secure session/CSRF cookies, HTTPS redirects and one hour of HSTS.
Ensure the hosting proxy reports HTTPS correctly before enabling these settings.

Configure PythonAnywhere static mappings:

- `/static/` → the checkout's `staticfiles/` directory
- `/media/` → the existing persistent `media/` directory

Run `python manage.py check --deploy --fail-level ERROR` with the production
environment, then reload the web app in PythonAnywhere. The optional HSTS
subdomain/preload checks (W005/W021) remain warnings by design; the site does
not enroll its domain or subdomains in browser preload lists. Check login, a movie
poster, cart checkout and order history after reload. Preserve the hosted database
and uploads; do not replace them with a development database.
