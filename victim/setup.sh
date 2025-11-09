#!/bin/bash

echo "Victim setup."

echo "Enter the subdomain you will use for the bank app (optional): "
read subdomain

echo "Enter the root domain you will use for the banking app: "
read domain

if ! command -v docker &> /dev/null
then
  if ! command -v curl &> /dev/null
  then
    echo "Installing curl."
    sudo apt install -y curl &> /dev/null
  fi

  echo "Installing Docker."
  curl https://get.docker.com | sh
else
  echo "Docker installed already."
fi

cd bank
sed -i "s/demo/${subdomain}/g" Caddyfile
sed -i "s/hnolan.com/${domain}/g" Caddyfile
sed -i "s/hnolan.com/${domain}/" main.py

sudo docker compose up -d &> /dev/null

echo "Setup complete; bank app has been launched."
