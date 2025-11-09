#!/bin/bash

echo "Attacker setup."

echo "Enter the subdomain you will use for the bank app (optional): "
read subdomain

echo "Enter the root domain you will use for the banking app: "
read domain

echo "Enter the root domain you will use for the phishing URL: "
read domain_phish

echo "Cloning submodules."
cd ../
git submodule update --init > /dev/null

if ! command -v go &> /dev/null; then
  echo "Installing Go."
  sudo apt install -y golang-go &> /dev/null
fi

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

cd attacker/evilginx2
make
cd ../
mv evilginx2/build/evilginx .

sed -i "s/demo/$(subdomain)/g" demo.yaml
sed -i "s/hnolan.com/$(domain)/g" demo.yaml

etchost="127.0.0.1 ${subdomain}.${domain_phish}"
sudo bash -c "echo '$etchost' >> /etc/hosts"
sudo bash -c "echo '127.0.0.1 web.mail'>> /etc/hosts"

cd mail
sudo docker compose up -d &> /dev/null
echo "Mail app launched at http://web.mail:8080."
