#!/bin/bash

# Colors
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

workdir="/data/eyeCU"

cd $workdir
echo -e "${CYAN}Checking for updates..${NC}"
git remote update
status=$(git status -uno | grep up-to-date)

if [[ -n "${status// }" && $1 != "-f" ]]
then
	touch /tmp/noupdate
	echo "Branch is up to date."
	echo "Use -f flag to force new image creation and container deployment."
	exit
fi

echo -e "${RED}Building Docker image...${NC}"
git pull origin master
docker build -t eyecu-nginx:latest .

echo -e "${RED}Removing current container...${NC}"
docker stop eyecu-client
docker rm eyecu-client

echo -e "${RED}Starting up new container...${NC}"
docker run -d -p 80:5000 --link eyecu-mariadb:mariadb --name=eyecu-client eyecu-nginx
touch /tmp/update
