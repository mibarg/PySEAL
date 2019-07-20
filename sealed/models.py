"""
Model
Main class for sealed Python modules CipherScheme and CipherText
"""

from typing import Union, Tuple
import logging
import numpy as np

from sealed.primitives import *
from sealed.encode import Encoder
from sealed.utils import is_pow_of_two


class CipherText:
    """
    Wrapper class for SEAL Ciphertext
    Enables homomorphic operations using Python-native syntax
    """

    def __init__(self,  cipher: Ciphertext,
                 context: SEALContext, encoder: Encoder):
        """
        :param cipher: SEAL Ciphertext
        :param context: Used to recreate Evaluator when loading from pickle
        :param encoder: Used to encode and decode plaintext for (cipher, plain) operations,
        as well as decoding the ciphertext itself
        """

        self._cipher = cipher

        self._context = context
        self._encoder = encoder

        # non-pickelizable properties
        self._evl = Evaluator(self._context)

    def __add__(self, other):
        if isinstance(other, CipherText) and self._encoder == other._encoder:
            res = Ciphertext()
            self._evl.add(self._cipher, other._cipher, res)
            return self.init_new(res)
        elif self._encoder.can_encode(other):
            res = Ciphertext()
            self._evl.add_plain(self._cipher, self._encoder.encode(other), res)
            return self.init_new(res)
        else:
            return NotImplemented

    def __radd__(self, other):
        """
        Handle addition between different types where the second one is CipherText.
        This allows CipherTexts to be added to plaintext from left or right.
        """
        return self.__add__(other)

    def __neg__(self):
        res = Ciphertext()
        self._evl.negate(self._cipher, res)
        return self.init_new(res)

    def __sub__(self, other):
        if isinstance(other, CipherText) and self._encoder == other._encoder:
            return other + (-self)
        else:
            return NotImplemented

    def __mul__(self, other):
        logging.debug("__mul__ got other of type %s." % type(other))
        if isinstance(other, CipherText) and self._encoder == other._encoder:
            res = Ciphertext()
            self._evl.multiply(self._cipher, other._cipher, res)
            return self.init_new(res)
        elif self._encoder.can_encode(other) and other is not 0 and other is not 0.0:
            res = Ciphertext()
            self._evl.multiply_plain(self._cipher, self._encoder.encode(other), res)
            return self.init_new(res)
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
        Handle multiplication between different types where the second one is CipherText.
        This allows CipherTexts to be multiplied by plaintext from left or right.
        """
        return self.__mul__(other)

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

    def __copy__(self):
        return CipherText(self._cipher, self._context, self._encoder)

    def __getstate__(self):
        """
        Enable picklization by ignoring and recreating cpp-generated properties
        """

        return self._cipher, self._context, self._encoder

    def __setstate__(self, state):
        """
        Enable picklization by ignoring and recreating cpp-generated properties
        """

        self._cipher, self._context, self._encoder = state

        # non-pickelizable properties
        self._evl = Evaluator(self._context)

        return True

    def init_new(self, cipher: Ciphertext):
        """
        Initiate a new CipherText instance given a SEAL Ciphertext.
        This method uses self's _context and _encoder to create a new CipherText instance.
        :param cipher: SEAL Ciphertext
        :return: CipherText with self's _context and _encoder
        """

        other = self.__copy__()
        other._cipher = cipher
        return other

    def _square(self):
        return self * self

    def size(self):
        """
        :return: The Ciphertext's current size
        """

        return self._cipher.size()

    def decrypt(self, sk: SecretKey):
        """
        Decrypt and decode Ciphertext into a plain Python object
        :param sk: SEAL SecretKey
        :return: plain Python object
        """

        plain = Plaintext()
        Decryptor(self._context, sk).decrypt(self._cipher, plain)

        decoded = self._encoder.decode(plain)
        return decoded

    def noise_budget(self, sk: SecretKey):
        """
        :param sk: SEAL SecretKey
        :return: The Ciphertext's current noise budget
        """

        dec = Decryptor(self._context, sk)
        return dec.invariant_noise_budget(self._cipher)

    def relinearize(self, ek: EvaluationKeys) -> "CipherText":
        """
        Relinearization reduces the size of the CipherText after homomorphic operations
        back to the initial size (2).
        Thus, relinearizing one or both inputs before the next multiplication,
        or e.g. before serializing the CipherText, can have a huge positive impact on performance.
        :param ek: EvaluationKeys
        :return: relinearized CipherText
        """

        res = Ciphertext()
        self._evl.relinearize(self._cipher, ek, res)

        return self.init_new(res)

    def roll(self, gk: GaloisKeys,
             shift: Union[int, Tuple[int, int]] = 1,
             axis: int = 0) -> "CipherText":
        """
        Roll matrix rows or columns, similar to numpy.roll
        :param gk: GaloisKeys
        :param shift: The number of places by which elements are shifted.
            If a tuple, then axis must be a tuple of the same size,
            and each of the given axes is shifted by the corresponding number.
            If an int while axis is a tuple of ints, then the same value is used for all given axes.
        :param axis: Which way to rotate, rows or columns. Used only when shift is an int.
        """

        assert isinstance(axis, int) and 0 <= axis <= 1, "axis must be 0 or 1, provided %s" % axis

        if isinstance(shift, tuple):
            if shift[0] == 0:
                return self.roll(gk, shift[1], 1)
            elif shift[1] == 0:
                return self.roll(gk, shift[0], 0)
            else:
                rolled_rows = self.roll(gk, shift[0], 0)
                return rolled_rows.roll(gk, shift[1], 1)

        # From here we can assume shift is an int

        if axis == 0 and shift not in (-1, 0, 1):
            # TODO support more than 1 step rotations
            raise TypeError("Only 1 step rotation is supported for row rotation.")

        res = Ciphertext()
        # It seems like SEAL rotations are flipped (columns to rows and rows to columns).
        # We flip them to work like standard numpy dimensions
        if axis == 0:
            self._evl.rotate_columns(self._cipher, gk, res)
        else:
            self._evl.rotate_rows(self._cipher, -shift, gk, res)

        return self.init_new(res)


class CipherScheme:
    """
    Main sealed class which holds encryption parameters, generates keys and encrypts Python objects
    """

    def __init__(self, poly_mod_deg: int = 2048, plain_mod: int = 256, coeff_mod: int = 0, security: int = 128):
        """
        :param poly_mod_deg: Used to define SEAL polynomial modulus to "1x^poly_mod_deg + 1", must be a power of two.
            The polynomial modulus should be thought of mainly affecting the security level of the scheme;
                larger polynomial modulus makes the scheme more secure. At the same time, it
                makes ciphertext sizes larger, and consequently all operations slower.
            Recommended degrees for poly_modulus are 1024, 2048, 4096, 8192, 16384, 32768,
                but it is also possible to go beyond this.
        :param coeff_mod: Leave as default to use SEAL recommended value.
            The size of the coefficient modulus should be thought of as the most significant factor
            in determining the noise budget in a freshly encrypted ciphertext: bigger means
            more noise budget. Unfortunately, a larger coefficient modulus also lowers the
            security level of the scheme. Thus, if a large noise budget is required for
            complicated computations, a large coefficient modulus needs to be used, and the
            reduction in the security level must be countered by simultaneously increasing
            the polynomial modulus.
        :param plain_mod: The plaintext modulus can be any positive integer,
            but it required to be a prime number for batch operations (using IntMatrixEncoder).
            The plaintext modulus determines the size of the plaintext data type, but it also affects
            the noise budget in a freshly encrypted ciphertext, and the consumption of
            the noise budget in homomorphic multiplication.
            Thus, it is essential to try to keep the plaintext data type as small as possible for good performance.
            The noise budget in a freshly encrypted ciphertext is ~ log2(coeff_modulus/plain_modulus) (bits)
            and the noise budget consumption in a homomorphic multiplication is of the
            form log2(plain_modulus) + (other terms).
        :param security: Number of bits used as security parameter. Supported values are 128 and 192.
        """

        try:
            params = EncryptionParameters()

            # Security
            assert security in (128, 192)

            # Polynomial modulus
            assert is_pow_of_two(poly_mod_deg)
            params.set_poly_modulus("1x^%d + 1" % poly_mod_deg)

            # Coefficient modulus
            assert isinstance(coeff_mod, int)
            if coeff_mod <= 0:
                # Automatically choose by SEAL recommendations
                coeff_mod_func = {128: coeff_modulus_128, 192: coeff_modulus_192}
                params.set_coeff_modulus(coeff_mod_func[security](poly_mod_deg))
            else:
                params.set_coeff_modulus([SmallModulus(coeff_mod)])

            # Plaintext modulus
            assert isinstance(plain_mod, int)
            params.set_plain_modulus(plain_mod)

            self._context = SEALContext(params)

            # non-pickelizable properties
            self._keygen = KeyGenerator(self._context)
            self._evl = Evaluator(self._context)
        except AssertionError as e:
            raise ValueError("Illegal parameters, %s" % e)

    def generate_keys(self, dbc: int = 16, eval_keys: int = 1) \
            -> Tuple[PublicKey, SecretKey, EvaluationKeys, Union[GaloisKeys, None]]:
        """
        :param dbc: decomposition bit count, any integer at least 1 [dbc_min()] and at most 60 [dbc_max()]
            A large decomposition bit count makes relinearization fast, but consumes more noise budget.
            A small decomposition bit count can make relinearization slower,
            but might not change the noise budget by any observable amount.
        :param eval_keys: M-2 evaluation keys to relinearize a ciphertext of size M >= 2 back to size 2
        :return: (PublicKey, SecretKey, EvaluationKeys, GaloisKeys)
            In case context parameters do not allow batching, None is returned instead of GaloisKeys
        """

        assert dbc_min() <= dbc <= dbc_max()
        assert eval_keys > 0

        pk = self._keygen.public_key()
        sk = self._keygen.secret_key()

        ek = EvaluationKeys()
        self._keygen.generate_evaluation_keys(dbc, eval_keys, ek)

        try:
            gk = GaloisKeys()
            self._keygen.generate_galois_keys(dbc, gk)
        except RuntimeError as e:
            if str(e) != "encryption parameters are not valid for batching":
                raise
            gk = None

        return pk, sk, ek, gk

    def encrypt(self, pk: PublicKey, plain: Union[int, float, np.ndarray], **kwargs):
        """
        Encodes and encrypts Python objects
        :param pk: PublicKey
        :param plain: Python object
        :param kwargs: additional arguments to adjust encoding
        :return: CipherText
        """

        encoded, encoder = Encoder(plain, self._context, **kwargs)

        cipher = Ciphertext()
        Encryptor(self._context, pk).encrypt(encoded, cipher)

        return CipherText(cipher, self._context, encoder)

    def __str__(self) -> str:
        return "CipherScheme(poly_mod={}, coeff_mod_size={} bits, plain_mod={}, noise_std={})".format(
            self._context.poly_modulus().coeff_count(), self._context.total_coeff_modulus().significant_bit_count(),
            self._context.plain_modulus().value(), self._context.noise_standard_deviation())

    def __eq__(self, other) -> bool:
        if isinstance(other, CipherScheme) and self._context == other._context:
            return True
        else:
            return False

    def __getstate__(self):
        """
        Enable picklization by ignoring and recreating cpp-generated properties
        """

        return self._context

    def __setstate__(self, state):
        """
        Enable picklization by ignoring and recreating cpp-generated properties
        """

        self._context = state

        # non-pickelizable properties
        self._keygen = KeyGenerator(self._context)
        self._evl = Evaluator(self._context)
