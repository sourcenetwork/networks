FROM golang:1.21-alpine AS builder

COPY ./bdjuno /tmp/bdjuno
COPY ./cosmos-sdk /tmp/cosmos-sdk
COPY ./juno /tmp/juno

RUN apk add --no-cache make git &&\
    cd /tmp/bdjuno &&\
    go mod download &&\
    make build &&\
    apk del git make &&\
    rm -rf /tmp/cosmos-sdk /tmp/juno

FROM alpine:latest

COPY --from=builder /tmp/bdjuno/build/bdjuno /usr/local/bin/bdjuno

RUN adduser bdjuno -S

VOLUME  /etc/bdjuno

COPY --chown=bdjuno:root bdjuno-config.yaml /etc/bdjuno/config.yaml
COPY --chown=bdjuno:root genesis.json /etc/bdjuno/genesis.json
COPY bdjuno-entrypoint.sh /usr/local/bin/

USER bdjuno

# Prometheus sink port
EXPOSE 8000 

# Hasura actions port
EXPOSE 3000 

ENTRYPOINT ["bdjuno-entrypoint.sh"]
CMD ["start", "--home /etc/bdjuno"]
