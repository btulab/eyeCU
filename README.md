# eyeCU - The Red Buffalo Network
eyeCU is a project aiming to monitor the "health" of the University of Colorado, Boulder campus through a network of IoT devices.


Docker Setup
==
We're using a docker image with uWSGI and NGinx for Flask apps. For more info see:


https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/

To get up and running:

Change host ip and passwd to their appropriate values
```
$ echo "[database]
host = 172.17.0.2
user = root
passwd = mypass
db = eyedb

[motd]
message = "Hello World!"

" > client/db.cfg
```

Auto Installation:
```
$ ./deploy.sh --complete
```

Manually:
MySQL/MariaDB Container
```
$ docker pull mariadb:latest
$ docker run -d --name=eyecu-mariadb --env="MYSQL_ROOT_PASSWORD=mypass" mariadb
$ mysql -uroot -pmypass -h 172.17.0.2 < mariadb/eyeCUdata.sql
```

Nginx Container
```
$ sudo docker build -t eyecu-nginx:latest .
$ sudo docker run -d -p 80:5000 --link eyecu-mariadb:mariadb --name=eyecu-client eyecu-nginx
```

Create a user account
```
$ cd client
$ python auth.py username password
```
