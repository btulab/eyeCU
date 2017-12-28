# eyeCU - The Red Buffalo Network
eyeCU is a project aiming to monitor the "health" of the University of Colorado, Boulder campus through a network of IoT devices.


Docker Setup
=====
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
" > client/db.cfg
```

MySQL Container
```
$ sudo docker run -d --name=eyecu-mysql --env="MYSQL_ROOT_PASSWORD=mypass" mysql
$ mysql -uroot -pmypass -h 172.17.0.2 < info/eyeCUdata.sql
```

Nginx Container
```
$ sudo docker build -t eyecu-nginx:latest .
$ sudo docker run -d -p 80:5000 --link eyecu-mysql --name=eyecu-nginx eyecu-nginx
```

Create a user account
```
$ python client/auth.py username password
```
