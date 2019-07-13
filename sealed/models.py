from typing import Union, Tuple, Type
import logging

from sealed._primitives import *


class Encoder:
    # TODO support matrices (PolyCRTBuilder), float (FractionalEncoder)
    _TYPE_MAP = {int: IntegerEncoder, float: FractionalEncoder}
    _PLAIN_TYPES = Union[int, float]
    _ENCODER_TYPES = Union[Type[IntegerEncoder], Type[FractionalEncoder]]

    def __init__(self, encoder_type: _ENCODER_TYPES, plain_mod: int, base: int):
        self._encoder_type = encoder_type
        self._plain_mod = plain_mod
        self._base = base
        # noinspection PyCallingNonCallable
        self._encoder = encoder_type(SmallModulus(plain_mod), base)

    def __eq__(self, other) -> bool:
        if (isinstance(other, Encoder)
                and self._encoder_type.__class__ == other._encoder_type.__class__
                and self._plain_mod == other._plain_mod
                and self._base == other._base):
            return True
        else:
            return False

    @staticmethod
    def encoding_type(plain: _PLAIN_TYPES) -> _ENCODER_TYPES:
        logging.debug("encoding_type(plain={},type(plain)={})".format(plain, type(plain)))
        for typ in Encoder._TYPE_MAP:
            if isinstance(plain, typ):
                return Encoder._TYPE_MAP[typ]
        return NotImplemented

    @staticmethod
    def from_plain(plain: _PLAIN_TYPES, plain_mod: int, base: int) -> Tuple[Plaintext, "Encoder"]:
        typ = Encoder.encoding_type(plain)
        encoder = Encoder(typ, plain_mod, base)
        encoded = encoder.encode(plain)
        return encoded, encoder

    def encode(self, plain: _PLAIN_TYPES) -> Plaintext:
        return self._encoder.encode(plain)

    def decode(self, encoded: Plaintext) -> _PLAIN_TYPES:
        logging.debug("decode(encoded={},self._encoder_type={})".format(encoded, self._encoder_type))
        if self._encoder_type == IntegerEncoder:
            # TODO non int 32
            return self._encoder.decode_int32(encoded)
        return NotImplemented
