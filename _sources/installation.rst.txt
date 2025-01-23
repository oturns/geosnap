.. Installation

Installation
===============

``geosnap`` supports python >`3.8`_. Please make sure that you are
operating in a python 3 environment.

Installing a released version
------------------------------
``geosnap`` is available on both conda and pip, and can be installed with either

.. code-block:: bash

    conda install -c conda-forge geosnap

or

.. code-block:: bash

    pip install geosnap

Installing development version
------------------------------
The recommended method for installing geosnap is with `anaconda`_. To get started with the development version, clone this repository or download it manually then `cd` into the directory and run the following commands::

$ conda env create -f environment.yml
$ source activate geosnap 
$ pip install -e . 

You can  also `fork`_ the `oturns/geosnap`_ repo and create a local clone of
your fork. By making changes
to your local clone and submitting a pull request to `oturns/geosnap`_, you can
contribute to the geosnap development.

.. _3.5: https://docs.python.org/3.5/
.. _3.6: https://docs.python.org/3.6/
.. _oturns/geosnap: https://github.com/oturns/geosnap
.. _fork: https://help.github.com/articles/fork-a-repo/
.. _anaconda: https://www.anaconda.com/download/ 
