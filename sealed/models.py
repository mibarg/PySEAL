from typing import Union, Tuple, Type
import logging

# noinspection PyProtectedMember
from sealed._primitives import *
from sealed.utils import is_pow_of_two


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
        # TODO force non-negative?
        return self._encoder.encode(plain)

    def decode(self, encoded: Plaintext) -> _PLAIN_TYPES:
        logging.debug("decode(encoded={},self._encoder_type={})".format(encoded, self._encoder_type))
        if self._encoder_type == IntegerEncoder:
            # TODO non int 32
            return self._encoder.decode_int32(encoded)
        return NotImplemented


class CipherText:
    def __init__(self, cipher: Ciphertext, evl: Evaluator, encoder: Encoder):
        self._cipher = cipher
        self._evl = evl
        self._encoder = encoder

    def __add__(self, other):
        if isinstance(other, CipherText) and self._encoder == other._encoder:
            res = Ciphertext()
            self._evl.add(self._cipher, other._cipher, res)
            return CipherText(res, self._evl, self._encoder)
        else:
            return NotImplemented

    def __neg__(self):
        res = Ciphertext()
        self._evl.negate(self._cipher, res)
        return CipherText(res, self._evl, self._encoder)

    def __sub__(self, other):
        if isinstance(other, CipherText) and self._encoder == other._encoder:
            return other + (-self)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, CipherText) and self._encoder == other._encoder:
            res = Ciphertext()
            self._evl.multiply(self._cipher, other._cipher, res)
            return CipherText(res, self._evl, self._encoder)
        else:
            return NotImplemented

    def __pow__(self, power):
        if isinstance(power, int) and power >= 1:

            if power == 1:
                return self

            if power % 2 == 0:
                return self._square() ** (power // 2)
            else:
                return self * (self._square() ** ((power - 1) // 2))
        else:
            return NotImplemented

    def _square(self):
        return self * self

    def size(self):
        return self._cipher.size()


class CipherScheme:
    def __init__(self,
                 poly_mod: int = 2048, coeff_mod: int = 0,
                 plain_mod: int = 256, security: int = 128):

        try:
            params = EncryptionParameters()

            # Security
            assert security in (128, 192)

            # Polynomial modulus
            assert is_pow_of_two(poly_mod)
            params.set_poly_modulus("1x^%d + 1" % poly_mod)

            # Coefficient modulus
            assert isinstance(coeff_mod, int)
            if coeff_mod <= 0:
                # Automatically choose by SEAL recommendations
                coeff_mod_func = {128: coeff_modulus_128, 192: coeff_modulus_192}
                params.set_coeff_modulus(coeff_mod_func[security](poly_mod))
            else:
                params.set_coeff_modulus([SmallModulus(coeff_mod)])

            # Plaintext modulus
            assert isinstance(plain_mod, int)
            params.set_plain_modulus(plain_mod)

            self._context = SEALContext(params)
            self._keygen = KeyGenerator(self._context)
            self._evl = Evaluator(self._context)
        except AssertionError as e:
            raise ValueError("Illegal parameters, %s" % e)

    def generate_keys(self):
        pk = self._keygen.public_key()
        sk = self._keygen.secret_key()
        return pk, sk

    def encrypt(self, pk: PublicKey, plain: Union[int, float], base: int):
        # TODO force non-negative?
        encoded, encoder = Encoder.from_plain(plain, self._context.poly_modulus().coeff_count() - 1, base)

        cipher = Ciphertext()
        Encryptor(self._context, pk).encrypt(encoded, cipher)

        return CipherText(cipher, self._evl, encoder)

    # noinspection PyProtectedMember
    def decrypt(self, sk: SecretKey, cipher: CipherText):
        plain = Plaintext()
        Decryptor(self._context, sk).decrypt(cipher._cipher, plain)

        decoded = cipher._encoder.decode(plain)
        return decoded

    # noinspection PyProtectedMember
    def noise_budget(self, sk: SecretKey, cipher: CipherText):
        dec = Decryptor(self._context, sk)
        return dec.invariant_noise_budget(cipher._cipher)

    # noinspection PyProtectedMember
    def relinearize(self, cipher: CipherText, dbc: int = 16) -> CipherText:
        """
        :param cipher: CipherText
        :param dbc: decomposition bit count, any integer at least 1 [dbc_min()] and at most 60 [dbc_max()]
            A large decomposition bit count makes relinearization fast, but consumes more noise budget.
            A small decomposition bit count can make relinearization slower, but might not change the noise budget by any observable amount.
        """

        assert dbc_min() <= dbc <= dbc_max()

        # M-2 evaluation keys to relinearize a ciphertext of size M >= 2 back to size 2
        num_keys = max(cipher.size() - 2, 1)

        ek = EvaluationKeys()
        self._keygen.generate_evaluation_keys(dbc, num_keys, ek)

        res = Ciphertext()
        self._evl.relinearize(cipher._cipher, ek, res)

        return CipherText(res, cipher._evl, cipher._encoder)

    def __str__(self) -> str:
        return "CipherScheme(poly_mod={}, coeff_mod_size={} bits, plain_mod={}, noise_std={})".format(
            self._context.poly_modulus().coeff_count(), self._context.total_coeff_modulus().significant_bit_count(),
            self._context.plain_modulus().value(), self._context.noise_standard_deviation())

    def __eq__(self, other) -> bool:
        if (isinstance(other, CipherScheme)
                and self._context.poly_modulus().coeff_count() == other._context.poly_modulus().coeff_count()
                and self._context.total_coeff_modulus().significant_bit_count() == other._context.total_coeff_modulus().significant_bit_count()
                and self._context.plain_modulus().value() == other._context.plain_modulus().value()):
            return True
        else:
            return False
