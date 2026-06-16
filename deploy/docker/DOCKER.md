# Docker deployment

## Stack

- `web` - Django + Gunicorn
- `db` - PostgreSQL
- `nginx` - reverse proxy for static, media and HTTP traffic

## Files

- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/entrypoint.sh`
- `.env.example`
- `deploy/docker/nginx/default.conf`

## First start

Copy the root env template:

```bash
cp .env.example .env
```

Fill at least:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

If you want models to be downloaded before the web container starts, set:

```env
PRELOAD_MODEL_LIST=cointegrated/rut5-base-absum
```

You can list multiple models separated by commas, but this will require much more disk space.

Then start:

```bash
docker compose up -d --build
```

## Stop

```bash
docker compose down
```

## Logs

```bash
docker compose logs -f
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f db
```

## Rebuild after changes

```bash
docker compose up -d --build
```

## Management commands

Create superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Open Django shell:

```bash
docker compose exec web python manage.py shell
```

## Server preparation on Ubuntu VPS

Install Docker:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git
sudo usermod -aG docker $USER
```

Reconnect to the server after adding your user to the `docker` group.

## Deploy on VPS

```bash
cd /var/www
git clone https://github.com/nikitafilipenko2/Thesis.git thesis
cd thesis
cp .env.example .env
nano .env
docker compose up -d --build
```

## Domain and HTTPS

Right now the stack is ready for HTTP on port `80`.

When you buy a domain:

- point the `A` record to the VPS IP
- update `.env`:
  - `DJANGO_ALLOWED_HOSTS`
  - `DJANGO_CSRF_TRUSTED_ORIGINS`
- then either:
  - terminate TLS in host Nginx with Certbot
  - or put another reverse proxy in front of Docker

## Notes

- PostgreSQL data is stored in Docker volume `postgres_data`
- Hugging Face cache is stored in Docker volume `model_cache`
- static files are stored in `static_volume`
- uploaded files are stored in `media_volume`
- migrations and `collectstatic` run automatically on container start
- `model-init` downloads NLTK resources and selected Hugging Face models before `web` starts
