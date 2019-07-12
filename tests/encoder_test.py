import pytest

from seal._primitives import IntegerEncoder, FractionalEncoder
from seal.models import Encoder


@pytest.mark.parametrize("plain, encoding_type",
                         [(1, IntegerEncoder), (0, IntegerEncoder), (-1, IntegerEncoder),
                          (1.0, FractionalEncoder), (0.0, FractionalEncoder), (-1.0, FractionalEncoder)])
def test_encoding_type(plain, encoding_type):
    assert encoding_type == Encoder.encoding_type(plain)


_PARAMS_DESC = "plain, base, plain_mod"
# 256 is a power of two, 293 is prime
_PARAMS = [(1, 2, 256), (0, 2, 256), (-1, 2, 256),
           (1, 3, 256), (0, 3, 256), (-1, 3, 256),
           (1, 2, 293), (0, 2, 293), (-1, 2, 293),
           (1, 3, 293), (0, 3, 293), (-1, 3, 293)]


@pytest.mark.parametrize(_PARAMS_DESC, _PARAMS)
def test_implicit_explicit_init(plain, base, plain_mod):
    encoder1 = Encoder(Encoder.encoding_type(plain), plain_mod, base)
    _, encoder2 = Encoder.from_plain(plain, plain_mod, base)

    assert encoder1 == encoder2


@pytest.mark.parametrize(_PARAMS_DESC, _PARAMS)
def test_encode_decode(plain, base, plain_mod):
    encoded, encoder = Encoder.from_plain(plain, plain_mod, base)

    assert plain == encoder.decode(encoded)
