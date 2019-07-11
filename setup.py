import os
from os.path import join, dirname, basename
import sys
from distutils.core import setup, Extension
from distutils import sysconfig

# Locate SEAL
if os.path.exists("/usr/local/lib/libseal.a") and os.path.exists("/usr/local/include/seal/"):
    SEAL_ROOT = None
else:
    if "SEAL" not in os.environ:
        raise ImportError("Couldn't find SEAL in /usr/local/ or environment variables. "
                          "Please install Microsoft SEAL (https://github.com/microsoft/SEAL) "
                          "and point environment variable SEAL to its root.")
    SEAL_ROOT = os.environ["SEAL"]

# Locate pybind11
if "PYBIND11" not in os.environ:
    raise ImportError("Couldn't find pybind11 in environment variables. "
                      "Please install pybind11 (https://github.com/pybind/pybind11) "
                      "and point environment variable PYBIND11 to its root.")
PYBIND11_ROOT = os.environ["PYBIND11"]

# Remove strict-prototypes compiler flag
cfg_vars = sysconfig.get_config_vars()
for key, value in cfg_vars.items():
    if type(value) == str:
        cfg_vars[key] = value.replace('-Wstrict-prototypes', '')

PY_INCLUDE = join(sys.prefix, "include/site/python%d.%d" % sys.version_info[:2])

ext_modules = [
    Extension(
        '_primitives',
        ['seal/wrapper.cpp'],
        include_dirs=['/usr/include/python3', PY_INCLUDE, os.path.join(PYBIND11_ROOT, 'include')] +
                     [join(SEAL_ROOT, 'SEAL') if SEAL_ROOT else ''],
        language='c++',
        extra_compile_args=['-std=c++11'],
        extra_objects=[join(SEAL_ROOT, 'bin/libseal.a') if SEAL_ROOT else ''],
    ),
]

setup(
    name='seal',
    version='2.3',
    author='Todd Stavish, Shashwat Kishore',
    author_email='toddstavish@gmail.com',
    description='Python wrapper for SEAL',
    ext_modules=ext_modules,
    package_dir={'': 'seal'},
)
