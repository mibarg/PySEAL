FROM ubuntu:18.04

# Install binary dependencies
RUN apt-get -qqy update && apt-get install -qqy \
	python3 \
	python3-dev \
	python3-pip \
	g++ \
	make \
	sudo libdpkg-perl \
	--no-install-recommends

# Enable docker cached requirements in case build fails
COPY /requirements.txt /sealed/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -U setuptools
RUN pip3 install -r /sealed/requirements.txt

# Copy source
COPY / /sealed
WORKDIR /sealed

# Deploy
RUN pip3 install . --install-option="--build-seal"