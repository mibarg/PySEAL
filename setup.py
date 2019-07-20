import os
from os.path import join
import sys
from distutils.core import setup, Extension


# Locate SEAL
if os.path.exists("/usr/local/lib/libseal.a") and os.path.exists("/usr/local/include/seal/"):
    SEAL_INCLUDE = "/usr/local/include/"
    SEAL_BIN = "/usr/local/lib/libseal.a"
else:
    if "SEAL" not in os.environ:
        raise ImportError("Couldn't find SEAL in /usr/local/ or environment variables. "
                          "Please install Microsoft SEAL (https://github.com/microsoft/SEAL) "
                          "and point environment variable SEAL to its root.")
    SEAL_INCLUDE = join(os.environ["SEAL"], 'SEAL')
    SEAL_BIN = join(os.environ["SEAL"], 'bin/libseal.a')


def get_includes():

    includes = []

    import pybind11
    includes.append(pybind11.get_include(True))
    includes.append(pybind11.get_include(False))

    includes.append(join(sys.prefix, "include/site/python%d.%d" % sys.version_info[:2]))

    includes.append(SEAL_INCLUDE)

    return includes


ext_modules = [
    Extension(
        '_primitives',
        ['sealed/cpp/wrapper.cpp'],
        include_dirs=get_includes(),
        language='c++',
        extra_compile_args=['-std=c++11'],
        extra_objects=[SEAL_BIN],
    ),
]

setup(
    name='sealed',
    version='0.0.1',
    author='Mibarg, Todd Stavish, Shashwat Kishore',
    author_email='mibarg@users.noreply.github.com',
    description='Python-native homomorphic encryption based on SEAL',
    ext_modules=ext_modules,
    package_dir={'': 'sealed'},
)
