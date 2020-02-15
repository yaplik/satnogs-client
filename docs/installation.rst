Installation
============

.. note::

   These installation steps are intended to be used for contributing
   to the satnogs-client codebase. If you are interested in setting up satnogs-client
   for your ground station check the `wiki <https://wiki.satnogs.org/Main_Page>`_.

Requirements: You will need python, python-virtualenvwrapper, pip and git

#. **Install the dependencies**

   SatNOGS client depends on `libhamlib2` Python bindings.
   In Debian, these bindings are provided by installing `python3-libhamlib2` package.

#. **Build the environment**

   Clone source code from the `repository <https://gitlab.com/librespacefoundation/satnogs/satnogs-client>`_::

     $ git clone https://gitlab.com/librespacefoundation/satnogs/satnogs-client.git

   Set up the virtual environment. On first run you should create it and link it to your project path.::

     $ cd satnogs-client
     $ mkvirtualenv --system-site-packages satnogs-client -a .

   Activate your python virtual environment::

     $ workon satnogs-client

   Install local development requirements::

     $ pip install -e .

#. **Run the client**

   Create an ``.env`` file on the project root and configure the client environment variables.

   Run ``satnogs-client``::

     $ satnogs-client
