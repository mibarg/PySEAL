import pytest

from sealed.models import CipherScheme


@pytest.mark.parametrize("coeff_mod, plain_mod",
                         ((0, 256), (0, 293), (0x7fffffffba0001, 256), (0x7fffffffba0001, 293)))
def test_fresh_size(coeff_mod, plain_mod,
                    poly_mod=2048, security=128, plain=1, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher = cs.encrypt(pk, plain, base)

    assert cipher.size() == 2


@pytest.mark.parametrize("coeff_mod, plain_mod, expected_noise",
                         ((0, 256, 38), (0, 293, 37), (0x7fffffffba0001, 256, 36), (0x7fffffffba0001, 293, 36)))
def test_add_noise_budget(coeff_mod, plain_mod, expected_noise,
                          poly_mod=2048, security=128, plain=1, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = cipher_1 + cipher_1

    # Addition consumes ~ 1 bit of noise
    assert abs(cs.noise_budget(sk, cipher_1) - cs.noise_budget(sk, cipher_2)) <= 1


@pytest.mark.parametrize("coeff_mod, plain_mod, expected_noise",
                         ((0, 256, 38), (0, 293, 37), (0x7fffffffba0001, 256, 36), (0x7fffffffba0001, 293, 36)))
def test_neg_noise_budget(coeff_mod, plain_mod, expected_noise,
                          poly_mod=2048, security=128, plain=1, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = -cipher_1

    # Negation consumes ~ zero noise bits
    assert abs(cs.noise_budget(sk, cipher_1) - cs.noise_budget(sk, cipher_2)) <= 1


@pytest.mark.parametrize("coeff_mod, plain_mod, expected_noise",
                         ((0, 256, 38), (0, 293, 37), (0x7fffffffba0001, 256, 36), (0x7fffffffba0001, 293, 36)))
def test_mult_noise_budget(coeff_mod, plain_mod, expected_noise,
                           poly_mod=2048, security=128, plain=1, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = cipher_1 * cipher_1

    # Multiplication consumes ~ half the noise budget
    assert abs(cs.noise_budget(sk, cipher_1) - (2 * cs.noise_budget(sk, cipher_2))) <= 5


@pytest.mark.parametrize("coeff_mod, plain_mod, expected_noise", ((0, 256, 52), (0, 293, 48)))
def test_pow_noise_budget(coeff_mod, plain_mod, expected_noise,
                          poly_mod=4096, security=128, plain=1, base=2, power=3):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = cipher_1 ** power

    assert abs(expected_noise - cs.noise_budget(sk, cipher_2)) <= 7


@pytest.mark.parametrize("plain, expected", ((0, 0), (1, 2), (3, 6), (0.0, 0.0), (1.1, 2.2), (3.3, 6.6)))
def test_add_enc_dec(plain, expected,
                     poly_mod=2048, coeff_mod=0, plain_mod=256, security=128, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = cipher_1 + cipher_1

    assert expected == cs.decrypt(sk, cipher_2)


@pytest.mark.parametrize("plain", (0, 1, 3, 0.0, 1.1, 3.3))
def test_neg_enc_dec(plain, poly_mod=2048, coeff_mod=0, plain_mod=256, security=128, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = -(-cipher_1)

    assert plain == cs.decrypt(sk, cipher_2)


@pytest.mark.parametrize("plain, expected", ((0, 0), (1, 1), (-1, 1), (3, 9),
                                             (0.0, 0.0), (1.0, 1.0), (-1.0, 1.0), (3.3, 10.89)))
def test_mult_enc_dec(plain, expected,
                      poly_mod=2048, coeff_mod=0, plain_mod=256, security=128, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = cipher_1 * cipher_1

    assert expected == cs.decrypt(sk, cipher_2)


@pytest.mark.parametrize("plain, power, expected", ((0, 1, 0), (0, 2, 0), (3, 1, 3), (3, 2, 9), (3, 3, 27), (3, 5, 243),
                                                    (0.0, 1, 0.0), (0.0, 2, 0.0), (3.3, 1, 3.3), (3.3, 2, 10.89),
                                                    (3.3, 3, 35.937), (3.3, 5, 391.35393)))
def test_pow_enc_dec(plain, power, expected,
                     poly_mod=8192, coeff_mod=0, plain_mod=1024, security=128, base=2):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    cipher_1 = cs.encrypt(pk, plain, base)
    cipher_2 = cipher_1 ** power

    assert expected == cs.decrypt(sk, cipher_2)


@pytest.mark.parametrize("plain_1, base_1, plain_2, base_2", ((1, 2, 1, 3),))
def test_type_inconsistency(plain_1, base_1, plain_2, base_2,
                            poly_mod=2048, coeff_mod=0, plain_mod=256, security=128):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    pk, sk = cs.generate_keys()

    # int in different base
    cipher_1 = cs.encrypt(pk, plain_1, base_1)
    cipher_2 = cs.encrypt(pk, plain_2, base_2)
    with pytest.raises(TypeError):
        _ = cipher_1 + cipher_2
    with pytest.raises(TypeError):
        _ = cipher_1 - cipher_2
    with pytest.raises(TypeError):
        _ = cipher_1 * cipher_2

    # TODO float
