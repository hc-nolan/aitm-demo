#!/bin/bash

BASE=$(pwd)

cd webapp
echo "Building webapp"
sudo docker build . -t aitm_demo:latest > /dev/null
sudo docker run -d -p 80:8000 --name=aitm_demo aitm_demo:latest > /dev/null
echo "Webapp running on port 80."

cd $BASE

cd evilginx2
make
echo "Evilginx binary compiled to {$BASE}/evilginx2/build/"
