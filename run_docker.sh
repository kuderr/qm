docker stop qm
docker rm qm
docker build -t qm .
docker run -d \
 -it \
 --restart on-failure \
 --name qm \
 --net=host \
 -v $HOME/creds:/qm/creds \
 qm
