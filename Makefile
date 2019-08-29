# Linux specific Docker file for geosnap

container:
	docker build -t geosnap ./infrastructure/docker/

# run a shell for our env
cli:
	docker run -it -p 8888:8888 -v ${PWD}:/home/jovyan geosnap /bin/bash

# run a shell with two mount points
cli2:
	docker run -it -p 8888:8888 -v ${PWD}:/home/jovyan/geosnap -v ${HOME}/.local:/home/jovyan/.local geosnap /bin/bash


# run a shell with two mount points and an environment variable for our tests
cli2e:
	docker run -it -p 8888:8888 -e "DLPATH=/home/jovyan/.local/share/geosnap/data" -v ${PWD}:/home/jovyan -v ${HOME}/.local:/home/jovyan/.local geosnap /bin/bash


cli2s:
	docker run -it -p 8888:8888 -e "DLPATH=/home/jovyan/.local/share/geosnap/data" -v ${PWD}:/home/jovyan -v ${HOME}/.local:/home/jovyan/.local geosnap sh -c "/home/jovyan/develop.sh && /bin/bash"

cli2tg:
	docker run -it -p 8888:8888 -e "DLPATH=/home/jovyan/.local/share/geosnap/data" -v ${PWD}:/home/jovyan -v $(subst geosnap,tobler, ${PWD}):/home/jovyan/tobler -v ${HOME}/.local:/home/jovyan/.local geosnap sh -c "/home/jovyan/develop.sh && /bin/bash"


test:
	echo ${PWD}
	echo $(subst HI, hi, HI There)
	echo $(subst geosnap,tobler, ${PWD})
	TOBLER := $(subst geosnap,tobler, ${PWD})
	echo ${TOBLER}
