# REG.RU Ubuntu VPS Checklist

## 1. Что заказать

- Услуга: `VPS/VDS на Linux`
- ОС: `Ubuntu 24.04 LTS`
- Минимально разумный тариф для этого проекта: `4 vCPU / 4 GB RAM / 80 GB SSD`
- Более надежный вариант под защиту диплома: `4 vCPU / 8 GB RAM`

## 2. Что выбрать при заказе

- IPv4: включить
- IPv6: можно включить, но не обязательно
- Панель управления: не нужна
- Автобэкапы: желательно включить, если бюджет позволяет
- Дополнительные сервисы: не обязательны

## 3. Что сделать сразу после покупки

- Открыть карточку услуги в личном кабинете REG.RU
- Скопировать:
  - внешний IP сервера
  - логин пользователя
  - пароль или SSH-ключ
- Проверить, что сервер имеет статус `активен`

## 4. Подключение к серверу

Windows PowerShell:

```powershell
ssh root@<server-ip>
```

Если используется обычный пользователь:

```powershell
ssh <username>@<server-ip>
```

## 5. Первичная настройка Ubuntu

```bash
apt update && apt upgrade -y
timedatectl set-timezone Europe/Moscow
adduser deploy
usermod -aG sudo deploy
```

Если хочешь работать не под `root`, дальше заходи под `deploy`.

## 6. Настройка SSH

На локальной машине:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

На сервере:

```bash
mkdir -p /home/deploy/.ssh
nano /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

После этого можно запретить вход по паролю:

```bash
nano /etc/ssh/sshd_config
```

Проверь или выставь:

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Применить:

```bash
systemctl restart ssh
```

## 7. Открытие нужных портов

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
ufw status
```

## 8. Привязка домена

В REG.RU у домена:

- открыть управление DNS-зоной;
- создать `A` запись:
  - `@` -> `<server-ip>`
- создать `A` запись:
  - `www` -> `<server-ip>`

Подождать применения DNS.

Проверка:

```powershell
nslookup example.com
nslookup www.example.com
```

## 9. Заливка проекта на сервер

На сервере:

```bash
mkdir -p /var/www
chown -R deploy:deploy /var/www
cd /var/www
git clone <your-repository-url> thesis
cd thesis
```

## 10. Production env

Скопировать шаблон:

```bash
cp deploy/ubuntu/.env.production.example backend/.env
nano backend/.env
```

Что заменить:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `POSTGRES_PASSWORD`

## 11. Поднять PostgreSQL, Nginx и Gunicorn

Дальше идти по инструкции:

- `deploy/ubuntu/DEPLOY.md`

Или выполнить:

```bash
bash deploy/ubuntu/deploy.sh
```

Перед запуском `deploy.sh` проверь:

- проект уже лежит в `/var/www/thesis`
- `backend/.env` заполнен
- в `deploy/ubuntu/nginx-thesis.conf` указан твой домен

## 12. Настройка Nginx под твой домен

Открыть:

```bash
nano /var/www/thesis/deploy/ubuntu/nginx-thesis.conf
```

Заменить:

```text
server_name example.com www.example.com;
```

На:

```text
server_name your-domain.ru www.your-domain.ru;
```

## 13. Выпуск SSL

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.ru -d www.your-domain.ru
```

## 14. Финальная проверка

```bash
systemctl status gunicorn-thesis
systemctl status nginx
nginx -t
journalctl -u gunicorn-thesis -n 100 --no-pager
```

Проверить в браузере:

- `http://your-domain.ru`
- `https://your-domain.ru`

## 15. Что проверить перед защитой

- сайт открывается по HTTPS
- регистрация и логин работают
- суммаризация текста работает
- загрузка `.txt/.pdf/.docx` работает
- история запросов сохраняется
- статические файлы и стили отдаются без ошибок
- `python manage.py test api` проходит на сервере
