FROM postgres:16-alpine

ENV POSTGRES_DB="bdjuno"
ENV POSTGRES_PASSWORD="root"

#RUN apk add git &&\
    #cd /tmp &&\
    #git clone 'https://github.com/forbole/bdjuno.git' &&\
    #cp /tmp/bdjuno/database/schema/* /docker-entrypoint-initdb.d/ &&\
    #rm -rf /tmp/bdjuno

COPY bdjuno/database/schema /docker-entrypoint-initdb.d
