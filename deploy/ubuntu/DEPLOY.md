# Deployment on Ubuntu

## Recommended stack

- Ubuntu 24.04 LTS
- Nginx
- Gunicorn
- systemd
- PostgreSQL
- Python virtual environment

## Project layout on server

```text
/var/www/thesis/
├── backend/
├── deploy/
└── .venv/
```

## Minimal server preparation

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib
```

## Clone project

```bash
sudo mkdir -p /var/www
sudo chown -R $USER:$USER /var/www
cd /var/www
git clone <your-repository-url> thesis
cd thesis
```

## Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

## Environment file

Create `backend/.env`:

```env
DJANGO_SECRET_KEY=replace-with-strong-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,<server-ip>
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DJANGO_SECURE_SSL_REDIRECT=True
ENABLE_DJANGO_EXTENSIONS=False
POSTGRES_ENABLED=True
POSTGRES_DB=thesis
POSTGRES_USER=thesis
POSTGRES_PASSWORD=replace-with-strong-password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

## PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE thesis;
CREATE USER thesis WITH PASSWORD 'replace-with-strong-password';
ALTER ROLE thesis SET client_encoding TO 'utf8';
ALTER ROLE thesis SET default_transaction_isolation TO 'read committed';
ALTER ROLE thesis SET timezone TO 'Europe/Moscow';
GRANT ALL PRIVILEGES ON DATABASE thesis TO thesis;
\q
```

## Django commands

```bash
cd /var/www/thesis/backend
source /var/www/thesis/.venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test api
```

## Gunicorn

1. Copy `deploy/ubuntu/gunicorn.service` to `/etc/systemd/system/gunicorn-thesis.service`
2. Adjust paths if needed
3. Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-thesis
sudo systemctl start gunicorn-thesis
sudo systemctl status gunicorn-thesis
```

## Nginx

1. Copy `deploy/ubuntu/nginx-thesis.conf` to `/etc/nginx/sites-available/thesis`
2. Replace `example.com` with your domain
3. Enable config:

```bash
sudo ln -sf /etc/nginx/sites-available/thesis /etc/nginx/sites-enabled/thesis
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
```

## Update procedure

```bash
cd /var/www/thesis
git pull
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test api
sudo systemctl restart gunicorn-thesis
sudo systemctl reload nginx
```

## Useful checks

```bash
sudo journalctl -u gunicorn-thesis -n 100 --no-pager
sudo nginx -t
curl -I http://127.0.0.1
```
