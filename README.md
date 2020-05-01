<< Looking for contributors to help with SEAL v3 migration >>

# Intro

[![Build Status](https://travis-ci.com/mibarg/sealed.svg?token=YtpyWjLrpzZ5G11Nfbjk&branch=master)](https://travis-ci.com/mibarg/sealed)

`sealed` builds on top of [PySEAL](https://github.com/Lab41/PySEAL) to provide a Python-native homomorphic 
encryption library based on Microsoft SEAL v2.3.
By Python-native, we mean that it enables using homomorphic operations on CipherText using 
familiar Python syntax such as `+`, `*` and `**`.

Here is a short example:

```python
from sealed import CipherScheme

cs = CipherScheme()
pk, sk, ek, _ = cs.generate_keys()

secret_1 = 1.0
secret_2 = 2.0

# you can encrypt int, float or numpy arrays
cipher_1 = cs.encrypt(pk, secret_1)
cipher_2 = cs.encrypt(pk, secret_2)

# homomorphic operations with Python-native syntax
cipher_res = 4.4 * cipher_1 + cipher_2 ** 3

res = cipher_res.decrypt(sk)
print("Dec[4.4 * Enc[%s] + Enc[%s] ** 3] = %s" % (secret_1, secret_2, res))
# >> Dec[4.4 * Enc[1.0] + Enc[2.0] ** 3] = 12.4
```

The code is heavily documented, and tries to be intuitive based on Python operator's expected behavior.
For usage samples, see tests dir.

# Install

`sealed` is available for Python version >= 3.5.

## Easiest options

`sealed` support automatic build of dependencies for Linux through a pip command, or through Docker via Dockerfile.

On Linux:

```bash
git clone https://github.com/mibarg/sealed
cd sealed
pip3 install . --install-option="--build-seal"
```

Docker:

```bash
git clone https://github.com/mibarg/sealed
cd sealed
docker build -t sealed-container-name -f deploy/Dockerfile .
```

## Other platforms

`sealed` is built on top of Microsoft SEAL v2.3. Therefore, you need to install in order for `sealed` to function.
Microsoft SEAL v2.3 sources are available in the [include](/include) dir.

To install `sealed` on other platforms, follow the following steps:
- Build Microsoft SEAL v2.3 (requires CMake (>= 3.10), GNU G++ (>= 6.0) or Clang++ (>= 5.0) and Xcode toolchain (>= 9.3) in macOS)
- Point environment variable _SEAL_ to the newly built library root
- Install `sealed` using `pip3 install sealed`

# Acknowledgments
`sealed` was inspired by and uses large parts of the CPP wrapper for SEAL developed by [PySEAL](https://github.com/Lab41/PySEAL).
