#!/usr/bin/env sh

set -e

if [ $# -ne 2 ]; then
    echo "Usage: node-state-fetcher archiver-server-url moniker"
    exit 1
fi

cd ~
curl -L $1/$2.tar.gz > $2.tar.gz

tar -xvf $2.tar.gz

sourcehubd keys import validator key

rm key
rm $2.tar.gz
