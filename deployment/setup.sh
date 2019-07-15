#!/usr/bin/env bash
# Variables
export ROOT=${PWD}
# Prerequisites
sudo apt-get -qqy update
sudo apt-get install -qqy \
	g++ make sudo libdpkg-perl --no-install-recommends
# Build SEAL libraries
cd ${ROOT}/dependencies/SEAL
chmod +x configure
sed -i -e 's/\r$//' configure
./configure
make
export LD_LIBRARY_PATH=${ROOT}/dependencies/SEAL/bin:${LD_LIBRARY_PATH}
export SEAL=${ROOT}/dependencies/SEAL
# Install PyBind11
cd ${ROOT}
git clone https://github.com/pybind/pybind11.git
cd ${ROOT}/pybind11
git checkout a303c6fc479662fd53eaa8990dbc65b7de9b7deb
export PYBIND11=${ROOT}/pybind11
# Install PySeal
cd ${ROOT}
pip install --upgrade pip
pip install -r requirements.txt
python setup.py build_ext -i
export PYTHONPATH=${PYTHONPATH}:${ROOT}:${SEAL}/bin
# Clean-up
apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*