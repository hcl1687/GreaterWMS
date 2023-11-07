# 20231027
## git clone
git clone path
```bash
/var/www/
```

## dev
```bash
apt update
apt install python3.8-venv
cd GreaterWMS
python3 -m venv env
source env/bin/activate`
```

## baseurl.txt
```bash
https://www.youdomain.com/api
```

## nginx.conf
```nginx
location / {
  #root   html;
  #index  testssl.html index.html index.htm;
  proxy_redirect off;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_pass http://127.0.0.1:8080/;
}

location /api/ {
  # First attempt to serve request as file, then
  # as directory, then fall back to displaying a 404.
  proxy_redirect off;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_pass http://localhost:8008/;
}

location /admin {
  # First attempt to serve request as file, then
  # as directory, then fall back to displaying a 404.
  proxy_redirect off;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_pass http://localhost:8008/admin;
}

location /static/ {
  alias /root/GreaterWMS/static_new/;
}

location /media/ {
  alias /root/GreaterWMS/media/;
}
```

## install djangorestframework-simplejwt
```bash
pip3 install --upgrade djangorestframework-simplejwt
```

## create admin
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

- Run Backend:
```shell
cd GreaterWMS
daphne -p 8008 greaterwms.asgi:application
or
daphne -b 0.0.0.0 -p 8008 greaterwms.asgi:application # lan
```

- Run Frontend:
```shell
cd templates
quasar d
```