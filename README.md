[![Build Status](https://travis-ci.com/mibarg/sealed.svg?token=YtpyWjLrpzZ5G11Nfbjk&branch=master)](https://travis-ci.com/mibarg/sealed)

Short example:

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

# 4.4 * 1.0 + 2.0 ** 3 == 12.4
res = cipher_res.decrypt(sk)
print("Dec[4.4 * Enc[%s] + Enc[%s] ** 3] = %s" % (secret_1, secret_2, res))
# >> Dec[4.4 * Enc[1.0] + Enc[2.0] ** 3] = 12.4
```