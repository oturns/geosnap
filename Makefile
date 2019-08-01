
container:
	docker build -t geosnap ./infrastructure/docker/

# run a shell for our env
cli:
	docker run -it -p 8888:8888 -v ${PWD}:/home/jovyan/host geosnap /bin/bash

dstop:
	docker stop $(docker ps -aq)
