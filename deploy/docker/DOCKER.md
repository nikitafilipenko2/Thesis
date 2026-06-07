# Docker deployment

## Stack

- `web` — Django + Gunicorn
- `db` — PostgreSQL
- `nginx` — reverse proxy for static, media and HTTP traffic

## Prepare env

Copy the template and replace values:

```bash
cp deploy/docker/.env.docker.example .env
```

Required fields:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `POSTGRES_PASSWORD`

If you have a domain, set:

```env
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
```

## Start

```bash
docker compose up --build -d
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
docker compose up --build -d
```

## Run tests in container

```bash
docker compose exec web python manage.py test api
```

## Create superuser

```bash
docker compose exec web python manage.py createsuperuser
```

## Production note

For HTTPS on Ubuntu VPS:

- keep this stack
- put a real domain into `.env`
- either terminate TLS in a host Nginx or add Certbot in front of this compose stack
