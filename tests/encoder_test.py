import pytest
from itertools import product

from sealed.encode import Encoder, IntEncoder, FloatEncoder
from sealed.models import CipherScheme


# noinspection PyProtectedMember
@pytest.mark.parametrize("plain, encoder_type",
                         [(1, IntEncoder), (0, IntEncoder),
                          (1.0, FloatEncoder), (0.0, FloatEncoder),
                          (int, IntEncoder), (float, FloatEncoder)])
def test_encoding_type(plain, encoder_type):
    cs = CipherScheme()
    _, encoder = Encoder(plain, cs._context)

    assert isinstance(encoder, encoder_type)


# noinspection PyProtectedMember
@pytest.mark.parametrize("plain, base, plain_mod", product([1.0, 0.0, 1, 0], [2, 3], [256, 293]))
def test_encode_decode(plain, base, plain_mod):
    cs = CipherScheme()
    encoded, encoder = Encoder(plain, cs._context, base=base)

    assert plain == encoder.decode(encoded)


# noinspection PyProtectedMember
@pytest.mark.parametrize("encoder_type, plain_mod, base", product([float, int], [256, 293], [2, 3]))
def test_eq(encoder_type, base, plain_mod):
    cs = CipherScheme()
    _, encoder1 = Encoder(encoder_type, cs._context, base=base)
    _, encoder2 = Encoder(encoder_type, cs._context, base=base)

    assert encoder1 == encoder2


# noinspection PyProtectedMember
@pytest.mark.parametrize("kwargs", ({"base": 2, "integral": 0.1, "fractional": 0.85},
                                    {"base": 3, "integral": 0.1, "fractional": 0.85},
                                    {"base": 2, "integral": 100, "fractional": 0.85},
                                    {"base": 3, "integral": 100, "fractional": 0.85},
                                    {"base": 2, "integral": 0.1, "fractional": 1000},
                                    {"base": 3, "integral": 0.1, "fractional": 1000}))
def test_float_coeff_allocation(kwargs, encoder_type=float):
    cs = CipherScheme()
    _ = Encoder(encoder_type, cs._context, **kwargs)
