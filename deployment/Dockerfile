#
# Container to build Linux SEAL libraries, python wrapper, and examples
#
FROM ubuntu:18.04

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
COPY /include /SEAL
WORKDIR /SEAL/SEAL/
RUN chmod +x configure
RUN sed -i -e 's/\r$//' configure
RUN ./configure
RUN make
ENV LD_LIBRARY_PATH /SEAL/bin:$LD_LIBRARY_PATH
ENV SEAL /SEAL/

# Delete SEAL log if exists, to enable caching of SEAL binaries
RUN rm -f /SEAL/config.log;

# Install dependencies
WORKDIR /
COPY /requirements.txt /sealed/requirements.txt
WORKDIR /sealed
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN pip3 install -r requirements.txt

# Install PySeal
WORKDIR /
COPY /sealed /sealed/sealed
COPY /tests /sealed/tests
COPY /setup.py /sealed/setup.py
WORKDIR /sealed
RUN python3 setup.py build_ext -i
ENV PYTHONPATH $PYTHONPATH:/sealed:$SEAL/bin

# Return to root directory
WORKDIR /

# Clean-up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
