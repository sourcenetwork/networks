#!/usr/bin/env sh
set -e

sleep 5

if [ !  -e /etc/bdjuno/INITIALIZED ]; then
    bdjuno parse genesis-file --home /etc/bdjuno --genesis-file-path /etc/bdjuno/genesis.json
    touch /etc/bdjuno/INITIALIZED
fi


bdjuno $@
