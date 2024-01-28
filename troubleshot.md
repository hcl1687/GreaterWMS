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

## deploy
```bash
docker-compose up -d
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

## Run Backend:
```bash
cd GreaterWMS
# win10: set GREATERWMS_ENV=dev
export GREATERWMS_ENV=dev
daphne -p 8008 greaterwms.asgi:application
or
daphne -b 0.0.0.0 -p 8008 greaterwms.asgi:application # lan
```

## Run Frontend:
```bash
cd templates
npm run start
```

## uninstall docker-compose
```bash
cd GreaterWMS
docker-compose stop
docker-compose rm
docker rmi backend-image-id
docker rmi frondend-image-id
```

## post install
```bash
cd /usr/local/lib/python3.8/site-packages/asgihandler
vim handler.py
# replace url with 'your ip/'
```

## test ozon
```bash
curl -o /dev/null -s -w "@curl-format.txt" --header "Content-Type: application/json" --header "Client-Id: your-id" --header "Api-Key: your-key" --request POST --data '{"filter":{"cutoff_from":"2023-11-01T14:15:22Z","cutoff_to":"2023-11-11T14:15:22Z"},"limit":1,"offset":0}' https://api-seller.ozon.ru/v3/posting/fbs/unfulfilled/list
```

## pip install
```bash
pip install package && pip freeze > requirements.txt
```

## celery
celery do not support win10. Should use docker under win10.

# 20240128
## config flower account
create a .env file before deploy

```
FLOWER_ADMIN=xxx
FLOWER_PASSWORD=xxxxx
```


