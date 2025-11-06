# Instructions

Install
- [Docker Engine](https://docs.docker.com/engine/install/)
- Golang (`sudo apt install -y golang-go`)

Run the webapp
```shell
cd webapp
sudo docker build . -t aitm_demo:latest
sudo docker run -p 80:8000 aitm_demo:latest
```

Build Evilginx
```shell
cd evilginx2
make
```
The Evilginx binary will be written to `./evilginx2/build/evilginx`

