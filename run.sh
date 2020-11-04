docker stop queue_manager
docker rm queue_manager
docker build -t queue_manager .
docker run -d \
 -it \
 --restart on-failure \
 --name queue_manager \
 --net=host \
 --env-file .env \
 -v $HOME/creds:/queue_manager/creds \
 queue_manager
