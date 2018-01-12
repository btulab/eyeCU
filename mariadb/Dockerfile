FROM mysql:latest

ENV MYSQL_DATABASE=eyecu \
    MYSQL_ROOT_PASSWORD=permutations

ADD eyeCU_schema.sql /docker-entrypoint-initdb.d

EXPOSE 3306
