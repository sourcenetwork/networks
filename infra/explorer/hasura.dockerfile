FROM docker.io/hasura/graphql-engine:v2.37.0-ce.cli-migrations-v3.ubuntu

#RUN apt-get update &&\
    #apt-get install git --yes &&\
    #cd /tmp &&\
    #git clone 'https://github.com/forbole/bdjuno.git' &&\
    #mkdir -p /hasura-metadata &&\
    #cp -r /tmp/bdjuno/hasura/metadata/* /hasura-metadata/ &&\
    #apt-get purge git --yes &&\
    #rm -rf /var/lib/apt/lists/* &&\
    #apt-get clean --yes &&\
    #rm -rf /tmp/bdjuno

COPY bdjuno/hasura/metadata /hasura-metadata

COPY hasura-entrypoint.sh /usr/local/bin

ENTRYPOINT ["hasura-entrypoint.sh"]
CMD ["graphql-engine", "serve"]
