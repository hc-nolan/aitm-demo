#!/bin/bash

curl https://get.docker.com | sh

cd webapp
sudo docker compose up -d
