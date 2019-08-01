FROM jupyter/scipy-notebook:307ad2bb5fce

LABEL maintainer="Serge Rey <sjsrey@gmail.com>"

RUN conda config --add channels conda-forge --force
RUN conda config --set channel_priority strict
RUN conda config --set safety_checks disabled
RUN conda install geopandas
RUN conda install mapclassify
RUN conda install giddy
RUN conda install scikit-learn
RUN conda install hdbscan
RUN conda install cenpy
RUN pip install quilt3
RUN pip install spenc
RUN pip install https://github.com/pysal/region/archive/master.zip

