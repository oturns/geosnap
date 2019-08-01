FROM jupyter/scipy-notebook:307ad2bb5fce

LABEL maintainer="Serge Rey <sjsrey@gmail.com>"

RUN conda config --add channels conda-forge --force
RUN conda config --set channel_priority strict
RUN conda config --set safety_checks disabled
RUN conda install geopandas
RUN conda install mapclassify
RUN conda install giddy

