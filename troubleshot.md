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

  # allow yourIp;
  # deny all;

  proxy_redirect off;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_pass http://localhost:8008/admin;

  error_page 403 = @goaway;
}

location /flower/ {
  # First attempt to serve request as file, then
  # as directory, then fall back to displaying a 404.

  # allow yourIp;
  # deny all;

  proxy_redirect off;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_pass http://localhost:5555;

  error_page 403 = @goaway;
}

location /static/ {
  alias /root/GreaterWMS/static_new/;
}

location /media/ {
  alias /root/GreaterWMS/media/;
}

location @goaway {
  return 404;
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
# win10 
set GREATERWMS_ENV=dev
# linux
export GREATERWMS_ENV=dev
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

# 20240129
order-init task period: 1min, expired time: 45s
order-update task period: 10min, expired time: 480s

# 20240219
## Android dev
https://www.56yhz.com/md/android_environment/zh-CN
### requirement
node v14
jdk1.8
android studio
gradle

### install
```bash
cd app
nvm use v14.21.3
npm install -g cordova
yarn install
```

### verify
```bash
cd app/src-cordova
cordova requirements
```

### debug
* modify server in app/src/store/settings/state.js
* Use your mobile phone or PDA to connect to your computer via USB.
* run

    ``` bash
    cd app
    quasar d -m cordova -T android
    ```
    It will auto install apk to the connected phone.

* go to settings/server page, set openid and baseurl.

