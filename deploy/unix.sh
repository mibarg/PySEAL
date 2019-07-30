#!/usr/bin/env bash
export ROOT=${PWD}
# Build SEAL libraries
cd ${ROOT}/include/SEAL &&
tr -d "\r" <configure> configure-unix &&
chmod +x configure-unix &&
./configure-unix &&
make &&
mv ${ROOT}/include/bin/ ${ROOT}/include/SEAL/bin/
# Delete SEAL log if exists, to enable caching of SEAL binaries
rm -f ${ROOT}/include/SEAL/config.log &&
# Export SEAL include dir
echo "LD_LIBRARY_PATH ${ROOT}/include/SEAL/bin:${LD_LIBRARY_PATH}" &&
echo "SEAL ${ROOT}/include/SEAL"