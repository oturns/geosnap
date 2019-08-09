# Linux specific Docker file for geosnap
container:
	docker build -t geosnap ./infrastructure/docker/

# run a shell for our env
cli:
	docker run -it -p 8888:8888 -v ${PWD}:/home/jovyan geosnap /bin/bash

# run a shell with two mount points
cli2:
	docker run -it -p 8888:8888 -v ${PWD}:/home/jovyan/geosnap -v /home/serge/.local:/home/jovyan/.local geosnap /bin/bash


# run a shell with two mount points and an environment variable for our tests
cli2e:
	docker run -it -p 8888:8888 -e "DLPATH=/home/jovyan/.local/share/geosnap/data" -v ${PWD}:/home/jovyan/geosnap -v /home/serge/.local:/home/jovyan/.local geosnap /bin/bash
