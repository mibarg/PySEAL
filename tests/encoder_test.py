import pytest
from itertools import product

from seal._primitives import IntegerEncoder, FractionalEncoder
from seal.models import Encoder


@pytest.mark.parametrize("plain, encoding_type",
                         [(1, IntegerEncoder), (0, IntegerEncoder), (-1, IntegerEncoder),
                          (1.0, FractionalEncoder), (0.0, FractionalEncoder), (-1.0, FractionalEncoder)])
def test_encoding_type(plain, encoding_type):
    assert encoding_type == Encoder.encoding_type(plain)


@pytest.mark.parametrize("plain, base, plain_mod", product([1, 0, -1], [2, 3], [256, 293]))
def test_implicit_explicit_init(plain, base, plain_mod):
    encoder1 = Encoder(Encoder.encoding_type(plain), plain_mod, base)
    _, encoder2 = Encoder.from_plain(plain, plain_mod, base)

    assert encoder1 == encoder2


@pytest.mark.parametrize("plain, base, plain_mod", product([1, 0, -1], [2, 3], [256, 293]))
def test_encode_decode(plain, base, plain_mod):
    encoded, encoder = Encoder.from_plain(plain, plain_mod, base)

    assert plain == encoder.decode(encoded)


@pytest.mark.parametrize("encoding_type, plain_mod, base", product([IntegerEncoder], [256, 293], [2, 3]))
def test_eq(encoding_type, base, plain_mod):
    encoder1 = Encoder(encoding_type, plain_mod, base)
    encoder2 = Encoder(encoding_type, plain_mod, base)

    assert encoder1 == encoder2
