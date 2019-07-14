import pytest
from itertools import product

from sealed.models import CipherScheme


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security", product([2**11, 2**12, 2**13, 2**14], [-1, 0, 0x7fffffffba0001, 0x7fffffffaa0001], [256, 293], [128, 192]))
def test_eq(poly_mod, coeff_mod, plain_mod, security):
    cs1 = CipherScheme(poly_mod, coeff_mod, plain_mod, security)
    cs2 = CipherScheme(poly_mod, coeff_mod, plain_mod, security)

    assert cs1 == cs2


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security", product([2**11, 2**12, 2**13, 2**14], [-1, 0, 0x7fffffffba0001, 0x7fffffffaa0001], [256, 293], [128, 192]))
def test_str(poly_mod, coeff_mod, plain_mod, security):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)

    _ = str(cs)


@pytest.mark.parametrize("poly_mod, coeff_mod, plain_mod, security", product([2**11, 2**12, 2**13, 2**14], [-1, 0, 0x7fffffffba0001, 0x7fffffffaa0001], [256, 293], [128, 192]))
def test_key_generation(poly_mod, coeff_mod, plain_mod, security):
    cs = CipherScheme(poly_mod, coeff_mod, plain_mod, security)

    assert cs.generate_keys() != cs.generate_keys()
