# Introduction

[Video demo](https://youtu.be/n__1rk8I7ZM)

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
sudo apt update && sudo apt install git
git clone https://github.com/hc-nolan/aitm-demo
cd aitm-demo/victim
./setup.sh
```

## Attacker VM

- Make sure you can access the web application. Create a user account and setup MFA.
- Ensure git is installed: `sudo apt install -y git`
- Run the following commands:

```shell
git clone https://github.com/hc-nolan/aitm-demo
cd aitm-demo/attacker
./setup.sh
```

# Playing the victim

On the attacker VM, open the webmail UI: `http://web.mail:8080`. Click the link in the phishing email and log in as if you were the victim. Notice how there appears to be nothing unusual about the sign-in - it is identical to as if you were signing in directly to the application in a legitimate way.

# Using the captured information

Back in the Evilginx process, run:

```shell
: sessions
```

Note the number of the session and then rerun 'sessions' with the number after. Copy the output of the 'cookies' section. In a web browser, download the [Cookie Editor](https://cookie-editor.com/) extension, press the import button, and paste the output from Evilginx. You will now be authenticated to the web application with the user's stolen session token.

