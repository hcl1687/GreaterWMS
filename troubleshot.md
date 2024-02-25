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
gradle v4.10.3

### install
```bash
cd app
nvm use v14.21.3
npm install -g cordova
npm install
```

### .bashrc
append env variables to .bashrc
```bash
export PATH=$PATH:/opt/gradle/gradle-4.10.3/bin
export ANDROID_HOME="$HOME/Android/Sdk"
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
export PATH=$PATH:$ANDROID_SDK_ROOT/tools; PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools
```
source .bashrc in the current shell

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
* if app can not connect to the pc successfully, remove platform andorid and re-add it.

### build
```bash
cd app
quasar build -m cordova -T android

# should download bundletool, if it's in ~/Downloads folder:
cd ~/Downloads
java -jar bundletool-all-1.15.6.jar build-apks --bundle=/home/hcl/github.com/hcl1687/GreaterWMS/app/dist/cordova/android/bundle/release/app-release.aab --output=GreaterWMS.apks --mode=universal
mv GreaterWMS.apks GreaterWMS.zip
unzip -d ./tmp GreaterWMS.zip
```



# 20240223
## dev on ubuntu22.04
### install pyenv and pyenv-virtualenv
https://www.hupeiwei.com/post/%E4%BD%BF%E7%94%A8pyenv%E8%BF%9B%E8%A1%8Cpython%E7%89%88%E6%9C%AC%E4%B8%8E%E8%99%9A%E6%8B%9F%E7%8E%AF%E5%A2%83%E7%9A%84%E7%AE%A1%E7%90%86/

### use pyenv
```bash
pyenv install 3.8.10
cd ~/github.com/hcl1687/GreaterWMS
pyenv local 3.8.10
pyenv virtualenv 3.8.10 wms_3810
pyenv activate wms_3810

# install dependency
pip install -U 'Twisted[tls,http2]'
pip install -r requirements.txt
pip install daphne

# create db
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### use nvm
https://tecadmin.net/how-to-install-nvm-on-ubuntu-22-04/
```bash
nvm install v14.21.3
cd ~/github.com/hcl1687/GreaterWMS/templates

# install dependency
nvm use v14.21.3
npm install -g @quasar/cli --force
npm install
```

### install redis
https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-22-04


### run
* run backend

  ```bash
  # win10 
  set GREATERWMS_ENV=dev
  # linux
  export GREATERWMS_ENV=dev
  # lan
  daphne -b 0.0.0.0 -p 8008 greaterwms.asgi:application
  ```

* run celery worker

  celery do not support win10. Should use docker under win10.
  ```bash
  # linux
  export GREATERWMS_ENV=dev
  celery -A greaterwms.celery worker -l info
  ```

* run celery beat (optional)
  
  celery do not support win10. Should use docker under win10.
  ```bash
  # linux
  export GREATERWMS_ENV=dev
  celery -A greaterwms.celery beat -l info
  ```

* run flower (optional)
  
  celery do not support win10. Should use docker under win10.
  ```bash
  # linux
  export GREATERWMS_ENV=dev
  # visit http://localhost:5555
  celery -A greaterwms.celery flower -l info
  ```

* run frontend
  
  ```bash
  cd ~/github.com/hcl1687/GreaterWMS/templates
  nvm use v14.21.3
  npm run start
  ```