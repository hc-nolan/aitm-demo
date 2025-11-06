#!/bin/bash
sudo apt install -y golang-go
git submodule update --init
cd evilginx2
make
echo "Evilginx binary compiled"
cd ../

echo "---------------------------------------------------"
echo "Please enter the web server domain name, without subdomain, e.g."
echo "login.microsoft.com -> microsoft.com: "
read web_domain
echo "Enter the web server subdomain (optional): "
read web_subdomain
echo "Enter the phishing domain name: "
read phish_domain

sed -i "s/hnolan.com/${web_domain}/g" demo.yaml
sed -i "s/demo/${web_subdomain}/g" demo.yaml
sudo bash -c "echo "127.0.0.1 ${phish_domain}" >> /etc/hosts"

sudo ./evilginx2/build/evilginx -p ./ -developer

