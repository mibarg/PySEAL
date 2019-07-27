import pytest
from itertools import product
import numpy as np

from sealed.encode import Encoder, IntEncoder, FloatEncoder, IntMatrixEncoder
from sealed.models import CipherScheme


@pytest.mark.parametrize("plain, encoder_type",
                         [(1, IntEncoder), (0, IntEncoder),
                          (1.0, FloatEncoder), (0.0, FloatEncoder),
                          (np.ones((2, 2048), int), IntMatrixEncoder),
                          (int, IntEncoder), (float, FloatEncoder),
                          (np.ndarray, IntMatrixEncoder)])
def test_encoding_type(plain, encoder_type, poly_mod=4096, plain_mod=40961):
    cs = CipherScheme(poly_mod, plain_mod)
    _, encoder = Encoder(plain, cs.context)

    assert isinstance(encoder, encoder_type)


@pytest.mark.parametrize("plain, base", product([1.0, 0.0, 1, 0, np.ones((2, 2048), int)], [2, 3]))
def test_encode_decode(plain, base, poly_mod=4096, plain_mod=40961):
    cs = CipherScheme(poly_mod, plain_mod)
    encoded, encoder = Encoder(plain, cs.context, base=base)

    if isinstance(plain, np.ndarray):
        assert (plain == encoder.decode(encoded)).all()
    else:
        assert plain == encoder.decode(encoded)


@pytest.mark.parametrize("encoder_type, base", product([float, int, np.ndarray], [2, 3]))
def test_eq(encoder_type, base, poly_mod=4096, plain_mod=40961):
    cs = CipherScheme(poly_mod, plain_mod)
    _, encoder1 = Encoder(encoder_type, cs.context, base=base)
    _, encoder2 = Encoder(encoder_type, cs.context, base=base)

    assert encoder1 == encoder2


@pytest.mark.parametrize("kwargs", ({"base": 2, "integral": 0.1, "fractional": 0.85},
                                    {"base": 3, "integral": 0.1, "fractional": 0.85},
                                    {"base": 2, "integral": 100, "fractional": 0.85},
                                    {"base": 3, "integral": 100, "fractional": 0.85},
                                    {"base": 2, "integral": 0.1, "fractional": 1000},
                                    {"base": 3, "integral": 0.1, "fractional": 1000}))
def test_float_coeff_allocation(kwargs, encoder_type=float):
    cs = CipherScheme()
    _ = Encoder(encoder_type, cs.context, **kwargs)
