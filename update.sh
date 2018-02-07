#!/bin/bash

workdir="/data/eyeCU"

cd $workdir
echo "Checking for updates..."
status=$(git status -uno | grep up-to-date)

if [[ -n "${status// }" && $1 != "-f" ]]
then
	touch /tmp/noupdate
	echo "Branch is up to date."
	echo "Use -f flag to force new image creation and container deployment."
	exit
fi

echo "Building Docker image..."
git pull origin master
docker build -t eyecu-nginx:latest .

echo "Removing current container..."
docker stop eyecu-client
docker rm eyecu-client

echo "Starting up new container..."
docker run -d -p 80:5000 --link eyecu-mariadb:mariadb --name=eyecu-client eyecu-nginx
touch /tmp/update
