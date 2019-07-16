#
# Container to build Linux SEAL libraries, python wrapper, and examples
#
FROM ubuntu:18.04
MAINTAINER Todd Stavish <toddstavish@gmail.com>

# Install binary dependencies
RUN apt-get -qqy update && apt-get install -qqy \
	g++ \
	git \
	make \
	python3 \
	python3-dev \
	python3-pip \
	sudo \
        libdpkg-perl \
	--no-install-recommends

# Build SEAL libraries
RUN mkdir -p SEAL/
COPY /include /SEAL/
WORKDIR /SEAL/SEAL/
RUN chmod +x configure
RUN sed -i -e 's/\r$//' configure
RUN ./configure
RUN make
ENV LD_LIBRARY_PATH SEAL/bin:$LD_LIBRARY_PATH
ENV SEAL /SEAL

# Delete SEAL log if exists, to enable caching of SEAL binaries
RUN rm -f /SEAL/SEAL/config.log;

# Install PyBind11
WORKDIR /SEAL/
RUN git clone https://github.com/pybind/pybind11.git
WORKDIR /SEAL/pybind11
RUN git checkout a303c6fc479662fd53eaa8990dbc65b7de9b7deb
ENV PYBIND11 /SEAL/pybind11

# Install dependencies
COPY /requirements.txt /SEAL/PySeal/requirements.txt
WORKDIR /SEAL/PySeal
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN pip3 install -r requirements.txt

# Install PySeal
COPY /sealed /SEAL/PySeal/sealed
COPY /tests /SEAL/PySeal/tests
COPY /setup.py /SEAL/PySeal/setup.py
WORKDIR /SEAL/PySeal
RUN python3 setup.py build_ext -i
ENV PYTHONPATH $PYTHONPATH:/SEAL/PySeal:$SEAL/bin

# Return to SEAL root directory
WORKDIR /SEAL

# Clean-up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
