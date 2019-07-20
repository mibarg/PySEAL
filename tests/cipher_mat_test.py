import pytest
import numpy as np

from sealed.models import CipherScheme


@pytest.mark.parametrize("mat_element", (0, 1, 3))
def test_add_enc_dec(mat_element,
                     poly_mod=4096, coeff_mod=0, plain_mod=40961, security=128):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    plain = mat_element * np.ones((2, 2048), int)
    expected = np.add(plain, plain)

    cipher_1 = cs.encrypt(pk, plain)
    cipher_2 = cipher_1 + cipher_1

    decrypted = cipher_2.decrypt(sk)

    assert np.linalg.norm(np.subtract(expected, decrypted), ord=1) <= 0.5 * poly_mod


@pytest.mark.parametrize("mat_element", (1, 3))
def test_neg_enc_dec(mat_element,
                     poly_mod=4096, coeff_mod=0, plain_mod=40961, security=128):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    plain = mat_element * np.ones((2, 2048), int)
    expected = plain

    cipher_1 = cs.encrypt(pk, plain)
    cipher_2 = -(-cipher_1)

    decrypted = cipher_2.decrypt(sk)

    assert np.linalg.norm(np.subtract(expected, decrypted), ord=1) <= 0.5 * poly_mod


@pytest.mark.parametrize("mat_element", (1, 3, 7))
def test_mul_enc_dec(mat_element,
                     poly_mod=4096, coeff_mod=0, plain_mod=40961, security=128):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    plain = mat_element * np.ones((2, 2048), int)
    expected = np.multiply(plain, plain)

    cipher_1 = cs.encrypt(pk, plain)
    cipher_2 = cipher_1 * cipher_1

    decrypted = cipher_2.decrypt(sk)

    assert np.linalg.norm(np.subtract(expected, decrypted), ord=1) <= 0.5 * poly_mod


@pytest.mark.parametrize("mat_element, plain_mul", ((1, 1), (3, 3), (7, 4)))
def test_mul_by_plain_enc_dec(mat_element, plain_mul,
                              poly_mod=4096, coeff_mod=0, plain_mod=40961, security=128):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    plain = mat_element * np.ones((2, 2048), int)
    mul = plain_mul * np.ones((2, 2048), int)
    expected = np.multiply(mul, plain)

    cipher_1 = cs.encrypt(pk, plain)
    cipher_2 = cipher_1 * mul

    decrypted = cipher_2.decrypt(sk)

    assert np.linalg.norm(np.subtract(expected, decrypted), ord=1) <= 0.5 * poly_mod


@pytest.mark.parametrize("mat_element, power", ((1, 1), (3, 3), (7, 2)))
def test_pow_enc_dec(mat_element, power,
                     poly_mod=4096, coeff_mod=0, plain_mod=40961, security=128):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    plain = mat_element * np.ones((2, 2048), int)
    expected = np.power(plain, power)

    cipher_1 = cs.encrypt(pk, plain)
    cipher_2 = cipher_1 ** power

    decrypted = cipher_2.decrypt(sk)

    assert np.linalg.norm(np.subtract(expected, decrypted), ord=1) <= 0.5 * poly_mod


@pytest.mark.parametrize("shift", ((-1, 9), (1, -7), (0, 0)))
def test_rotation_enc_dec(shift,
                          poly_mod=4096, coeff_mod=0, plain_mod=40961, security=128):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, gk = cs.generate_keys()

    plain = np.asarray(list(range(poly_mod))).reshape((2, 2048))
    expected = np.roll(plain, shift, (0, 1))

    cipher_1 = cs.encrypt(pk, plain)
    cipher_2 = cipher_1.roll(gk, shift)

    decrypted = cipher_2.decrypt(sk)

    assert np.linalg.norm(np.subtract(expected, decrypted), ord=1) <= 0.5 * poly_mod
