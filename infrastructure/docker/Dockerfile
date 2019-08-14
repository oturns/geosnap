FROM jupyter/scipy-notebook:307ad2bb5fce

LABEL maintainer="Serge Rey <sjsrey@gmail.com>"

RUN conda config --add channels conda-forge --force
RUN conda config --set channel_priority strict
RUN conda config --set safety_checks disabled
RUN conda install scipy>=1.3.0
RUN conda install geopandas
RUN conda install mapclassify
RUN conda install giddy
RUN conda install scikit-learn
RUN conda install cenpy
RUN conda install spenc
RUN pip install quilt3
RUN pip install https://github.com/pysal/region/archive/master.zip
RUN pip install https://github.com/pysal/tobler/archive/master.zip
RUN conda install pytest
RUN conda install nose nose-progressive coverage coveralls pytest-cov pytest-mpl
RUN pip install dash dash-bootstrap-components
RUN pip install -U statsmodels==0.10.0rc2 --pre
COPY develop.sh /home/jovyan/develop.sh
