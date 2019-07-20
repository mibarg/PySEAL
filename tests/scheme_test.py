import pytest
from itertools import product

from sealed.models import CipherScheme


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security",
                         product([2**11, 2**14], [0, 0x7fffffffaa0001], [256, 293], [128, 192]))
def test_eq(poly_mod, coeff_mod, plain_mod, security):
    cs1 = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    cs2 = CipherScheme(poly_mod, plain_mod, coeff_mod, security)

    assert cs1 == cs2


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security",
                         product([2**11, 2**14], [0, 0x7fffffffaa0001], [256, 293], [128, 192]))
def test_str(poly_mod, coeff_mod, plain_mod, security):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)

    _ = str(cs)


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security",
                         product([2**11, 2**14], [0, 0x7fffffffaa0001], [256, 293], [128, 192]))
def test_key_generation(poly_mod, coeff_mod, plain_mod, security):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)

    assert cs.generate_keys() != cs.generate_keys()


@pytest.mark.parametrize("coeff_mod, plain_mod, expected_noise",
                         ((0, 256, 38), (0, 293, 37), (0x7fffffffba0001, 256, 36), (0x7fffffffba0001, 293, 36)))
def test_fresh_noise_budget(coeff_mod, plain_mod, expected_noise,
                            poly_mod=2048, security=128, plain=1, base=2):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    cipher = cs.encrypt(pk, plain, base=base)

    # Noise budget in bits ~ log2(coeff_modulus/plain_modulus)
    assert abs(expected_noise - cipher.noise_budget(sk)) <= 1


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security, plain, base",
                         product([2**11, 2**14], [0, 0x7fffffffaa0001], [256, 293],
                                 [128, 192], [1, 0, 1.1, 0.43], [2, 3]))
def test_enc_dec(poly_mod, coeff_mod, plain_mod, security, plain, base):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, _, _ = cs.generate_keys()

    assert abs(plain - cs.encrypt(pk, plain, base=base).decrypt(sk)) <= 0.5


@pytest.mark.parametrize("dbc, expected_noise",
                         ((7, 175), (12, 175), (22, 175), (32, 166), (47, 151), (52, 146), (57, 142)))
def test_relinearize(dbc, expected_noise,
                     poly_mod=8192, coeff_mod=0, plain_mod=1024, security=128, plain=700, base=2):
    cs = CipherScheme(poly_mod, plain_mod, coeff_mod, security)
    pk, sk, ek, _ = cs.generate_keys(dbc=dbc)

    cipher_1 = cs.encrypt(pk, plain, base=base)
    cipher_2 = (cipher_1 * cipher_1).relinearize(ek)

    assert abs(expected_noise - cipher_2.noise_budget(sk)) <= 2
