import pytest
import pickle
import logging
import numpy as np

from sealed.encode import Encoder
from sealed import CipherScheme


def test_scheme_pickle():
    cs_1 = CipherScheme()

    cs_2 = pickle.loads(pickle.dumps(cs_1))

    assert cs_1 == cs_2


def test_keys_pickle():
    cs = CipherScheme()
    pk_1, sk_1, _, _ = cs.generate_keys()

    _ = pickle.loads(pickle.dumps(pk_1))
    _ = pickle.loads(pickle.dumps(sk_1))


@pytest.mark.parametrize("plain", (7, 7.21, np.ones((2, 2048), int)))
def test_cipher_pickle(plain, poly_mod=4096, plain_mod=40961, base=2):
    cs = CipherScheme(poly_mod, plain_mod)
    pk, sk, _, _ = cs.generate_keys()

    e_1 = cs.encrypt(pk, plain, base=base)
    e_2 = pickle.loads(pickle.dumps(e_1))

    if isinstance(plain, np.ndarray):
        assert (e_2.decrypt(sk) == plain).all()
    else:
        assert e_2.decrypt(sk) == plain

    # noinspection PyProtectedMember
    assert e_1._encoder == e_1._encoder


# noinspection PyProtectedMember
@pytest.mark.parametrize("plain", (7, 7.21, np.ones((2, 2048), int)))
def test_encoder_pickle(plain, poly_mod=4096, plain_mod=40961):
    context = CipherScheme(poly_mod, plain_mod)._context

    _, e_1 = Encoder(plain, context)
    e_2 = pickle.loads(pickle.dumps(e_1))

    logging.debug("test_encoder_pickle e_1=%s, e_2=%s" % (e_1, e_2))
    assert e_1 == e_2
