from os import environ, getcwd
from os.path import join

import platform
import traceback

from subprocess import Popen, PIPE, STDOUT

from distutils import sysconfig
from distutils.core import setup, Extension
from distutils.command.install import install
from distutils.command.build_ext import build_ext


def parse_requirements(file_name: str):
    """
    Parse pip requirements.txt file
    """
    with open(file_name, "r") as fp:
        reqs = []
        for line in fp:
            req = line.split('#')[0].strip()
            if len(req) > 0:
                reqs.append(req)

        return reqs


class InstallCommand(install):
    """
    Add a build-seal flag that builds Microsoft SEAL v2.3 from project include/ dir.
    """

    # single-version-externally-managed is manually added to fix a pip bug
    user_options = install.user_options + \
                   [("build-seal", None, None), ("single-version-externally-managed", None, None), ]

    # noinspection PyAttributeOutsideInit
    def initialize_options(self):
        install.initialize_options(self)
        self.build_seal = None
        self.single_version_externally_managed = True

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):

        if self.build_seal:
            print("Building Microsoft SEAL v2.3...")
            self.do_build_seal()

        if "SEAL" not in environ:
            raise ImportError(
                "Please install Microsoft SEAL v2.3 and point environment variable SEAL to its root.\n"
                "To build SEAL automatically use: pip install sealed --install-option=\"--build-seal\".")
        else:
            print("Found SEAL environment variable pointing to: %s.\n"
                  "Expecting to find 'bin' dir with 'libseal.a' and "
                  "'seal' dir with library headers." % environ["SEAL"])

        install.run(self)

    @staticmethod
    def do_build_seal():
        plat = platform.system()

        if plat in ("Linux", ):

            try:

                proc = Popen("./deploy/unix.sh", cwd=getcwd(), env=environ, stdout=PIPE, stderr=STDOUT)

                last_lines = []
                for bytes_line in proc.stdout:
                    line = bytes_line.decode("utf8").strip('\n')

                    print(line)
                    last_lines = last_lines[-1:] + [line, ]

                ld_library_path = last_lines[0].split(' ')
                seal = last_lines[1].split(' ')

                assert ld_library_path[0] == "LD_LIBRARY_PATH"
                environ["LD_LIBRARY_PATH"] = join(getcwd(), ld_library_path[1])

                assert seal[0] == "SEAL"
                environ["SEAL"] = join(getcwd(), seal[1])

            except (IndexError, UnicodeEncodeError):
                traceback.print_exc()

                if plat == "Linux":
                    deps = "sudo apt-get -qqy update && " \
                           "sudo apt-get install -qqy g++ make sudo libdpkg-perl --no-install-recommends"
                else:
                    deps = None
                deps_msg = "Make sure you have installed the required dependencies. " \
                           "Try the following command: %s.\n" % deps if deps else ""

                raise ImportError(
                    "Automatic build of Microsoft SEAL v2.3 failed.\n%s"
                    "Please install Microsoft SEAL v2.3 and point environment variable SEAL to its root." % deps_msg)

        else:
            raise ImportError(
                "Automatic build of Microsoft SEAL v2.3 is not supported for %s.\n"
                "Please install Microsoft SEAL v2.3 and point environment variable SEAL to its root." % plat)


class DelayEvaluation:
    """
    Delayed evaluation of include directories, to after they were installed by pip
    """

    def eval(self):
        return []


class GetIncludes(DelayEvaluation):

    def eval(self):

        includes = []

        # PyBind11
        import pybind11
        includes.append(pybind11.get_include(True))
        includes.append(pybind11.get_include(False))

        # Python include dir
        from sysconfig import get_paths
        includes.append(get_paths().get("include"))

        # Microsoft SEAL v2.3
        includes.append(environ["SEAL"])

        return includes


class GetObjects(DelayEvaluation):
    def eval(self):
        return [join(environ["SEAL"], "bin/libseal.a")]


class BuildExtCommand(build_ext):
    """
    - Remove strict-prototypes compiler flag
    - Add support for delayed evaluation of include directories, to after they were installed by pip
    """

    def _build_extensions_serial(self):
        """
        Add support for delayed evaluation of include directories, to after they were installed by pip
        """

        for ext in self.extensions:
            with self._filter_build_errors(ext):
                if isinstance(ext.include_dirs, DelayEvaluation):
                    ext.include_dirs = ext.include_dirs.eval()
                if isinstance(ext.extra_objects, DelayEvaluation):
                    ext.extra_objects = ext.extra_objects.eval()
                self.build_extension(ext)

    def build_extension(self, ext):
        """
        Remove strict-prototypes compiler flag
        """

        sysconfig.customize_compiler(self.compiler)
        try:
            self.compiler.compiler_so.remove("-Wstrict-prototypes")
        except (AttributeError, ValueError):
            pass
        build_ext.build_extension(self, ext)


ext_modules = [
    Extension(
        "_seal_primitives",
        ["sealed/cpp/wrapper.cpp"],
        include_dirs=GetIncludes(),
        language="c++",
        extra_compile_args=["-std=c++11"],
        extra_objects=GetObjects(),
    ),
]

setup(
    cmdclass={"build_ext": BuildExtCommand, "install": InstallCommand},
    name="sealed",
    version="0.0.1",
    url="https://github.com/mibarg/sealed",
    author="mibarg",
    author_email="mibarg@users.noreply.github.com",
    description="Python-native homomorphic encryption based on SEAL v2.3",
    install_requires=parse_requirements("requirements.txt"),
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    ext_modules=ext_modules,
    package_dir={"": "sealed"},
)
