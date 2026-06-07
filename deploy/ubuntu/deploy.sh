#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=/var/www/thesis
BACKEND_ROOT=$PROJECT_ROOT/backend
VENV_ROOT=$PROJECT_ROOT/.venv

sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib

sudo mkdir -p "$PROJECT_ROOT"
sudo chown -R "$USER":"$USER" "$PROJECT_ROOT"

python3 -m venv "$VENV_ROOT"
source "$VENV_ROOT/bin/activate"

pip install --upgrade pip
pip install -r "$BACKEND_ROOT/requirements.txt"

cd "$BACKEND_ROOT"
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test api

sudo cp "$PROJECT_ROOT/deploy/ubuntu/gunicorn.service" /etc/systemd/system/gunicorn-thesis.service
sudo cp "$PROJECT_ROOT/deploy/ubuntu/nginx-thesis.conf" /etc/nginx/sites-available/thesis
sudo ln -sf /etc/nginx/sites-available/thesis /etc/nginx/sites-enabled/thesis
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable gunicorn-thesis
sudo systemctl restart gunicorn-thesis
sudo nginx -t
sudo systemctl restart nginx
