#!/bin/bash

# Colors
RED='\033[0;31m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;93m'
NC='\033[0m' # No Color

image_name="eyecu-nginx"
workdir="/data/eyeCU"
cd $workdir
force=$1

git_update() {
  echo -e "${GREEN}$(date)"
  echo -e "${CYAN}Checking for updates..${NC}"
  git remote update
  status=$(git status -uno | grep up-to-date)

  if [[ -n "${status// }" && "$force" != "-f" ]]
  then
    touch /tmp/noupdate
    echo "Branch is up to date."
    echo "Use -f flag to force new image creation and container deployment."
    exit
  fi
}

cleanup_test() {
  echo -e "${YELLOW}Removing test container...${NC}"
  docker stop eyecu-TEST
  docker rm eyecu-TEST
}

launch_test_image() {
  echo -e "${YELLOW}Building test image...${NC}"
  docker build -t $image_name:$1 .

  echo -e "${YELLOW}Running test container and executing test...${NC}"
  docker run -d -p 5000:5000 --link eyecu-mariadb:mariadb --name=eyecu-TEST $image_name:$1
  echo -e "${CYAN}Patiently waiting...${NC}"
  sleep 3

  # Run our tests
  GET_REQUEST=$(curl --silent -I -X GET localhost:5000 | head -n 1 | cut -d$' ' -f2)
  if [ "$GET_REQUEST" != "200" ] 
  then
    echo -e "${RED}UPDATE FAILED${NC}"
    echo -e "${RED}ERROR HANDLING GET REQUEST${NC}"
    cleanup_test
    echo -e "${YELLOW}Finished cleanup.${NC}"
    exit
  fi
  echo -e "${GREEN}Tests completed."
}

launch_production_image() {
  echo -e "${YELLOW}Removing current production container...${NC}"
  docker stop eyecu-client
  docker rm eyecu-client

  echo -e "${GREEN}Starting up new container...${NC}"
  docker run -d -p 80:5000 --link eyecu-mariadb:mariadb --name=eyecu-client $image_name:$1
  touch /tmp/update
}

git_update
git pull origin master
version_tag=$(git log -1 --pretty=%h)
launch_test_image $version_tag
cleanup_test
launch_production_image $version_tag
echo -e "${GREEN}Deployment script finished.${NC}"
