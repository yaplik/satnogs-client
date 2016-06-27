FROM debian:testing

# Add code to image
RUN mkdir /code
COPY . /code
WORKDIR /code

# Install apt dependencies
RUN apt-get clean && apt-get update && \
    apt-get install git python python-dev python-pip \
    libhamlib-utils libusb-1.0-0-dev \
    gnuradio fftw-dev gr-osmosdr -y

# Install satnogs-client
RUN pip install --upgrade setuptools
RUN python setup.py build && python setup.py install
