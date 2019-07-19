from typing import Union, Tuple, Type
import numpy as np
from sympy import isprime

from sealed.primitives import *


class Encoder:
    # TODO support matrices (PolyCRTBuilder)

    # used for object comparison
    _ATTRIBUTES = {}

    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def __new__(cls,
                plain: Union[int, float, np.ndarray, Type[int], Type[float], Type[np.ndarray]],
                context: SEALContext,
                **kwargs) -> Tuple[Union[None, Plaintext], "Encoder"]:

        # numpy test must be first because comparison is calculated element-wise on int, float
        if isinstance(plain, np.ndarray) or plain == np.ndarray:
            encoder = IntMatrixEncoder(context, **kwargs)
            encoded = encoder.encode(plain) if plain is not np.ndarray else None
            return encoded, encoder

        if isinstance(plain, int) or plain is int:
            encoder = IntEncoder(context, **kwargs)
            encoded = encoder.encode(plain) if plain is not int else None
            return encoded, encoder

        if isinstance(plain, float) or plain == float:
            encoder = FloatEncoder(context, **kwargs)
            encoded = encoder.encode(plain) if plain is not float else None
            return encoded, encoder

        raise NotImplementedError("Encoder supports only int, float or np.ndarray.")

    def encode(self, plain) -> Plaintext:
        raise NotImplementedError

    def decode(self, encoded: Plaintext):
        raise NotImplementedError

    def can_encode(self, plain) -> bool:
        try:
            _ = self.encode(plain)
        except TypeError:
            return False
        else:
            return True

    def __eq__(self, other):
        if (isinstance(other, self.__class__)
                and all((getattr(self, attr) == getattr(other, attr) for attr in self._ATTRIBUTES))):
            return True
        else:
            return False

    def __getstate__(self):
        return [getattr(self, attr) for attr in self._ATTRIBUTES]

    def __setstate__(self, state):
        attrs = dict(zip(self._ATTRIBUTES, state))

        for attr, val in attrs.items():
            setattr(self, attr, val)

        # remove underscore from attribute names
        attrs_no_underscore = {k[1:]: v for k, v in attrs.items()}

        # self.__class__ is dynamically assigned with the child class, and thus we find the right __init__
        self.__class__.__init__(self, **attrs_no_underscore)
        return True

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.__dict__)


class IntEncoder(IntegerEncoder, Encoder):
    """
    Given an integer base b, encodes integers as plaintext polynomials as follows.
    First, a base-b expansion of the integer is computed. This expansion uses a `balanced' set of representatives
        of integers modulo b as the coefficients. Namely, when b is odd the coefficients are integers between -(b-1)/2
        and (b-1)/2. When b is even, the integers are between -b/2 and (b-1)/2, except when b is two and the usual
        binary expansion is used (coefficients 0 and 1).
    Decoding amounts to evaluating the polynomial at x=b.
    For example,
        if b=2, the integer 26 = 2^4 + 2^3 + 2^1 is encoded as the polynomial 1x^4 + 1x^3 + 1x^1.
        When b=3, 26 = 3^3 - 3^0 is encoded as the polynomial 1x^3 - 1.
    In memory polynomial coefficients are always stored as unsigned integers by storing their smallest non-negative
        representatives modulo plain_modulus. To create a base-b integer encoder,
        use the constructor IntegerEncoder(plain_modulus, b). If no b is given, b=2is used.
    """

    _ATTRIBUTES = {"_context", "_base", "_unsigned"}

    # noinspection PyUnusedLocal
    def __init__(self, context: SEALContext, base: int = 2, unsigned: bool = False, **kwargs):
        """
        :param context: SEALContext
        :param base: base for integer encoding
        :param unsigned: signed or unsigned int
        :param kwargs: not used, allows using Encoder parent class with kwargs each child class
        """

        super().__init__(context.plain_modulus(), base)
        self._context = context
        self._base = base
        self._unsigned = unsigned

    def encode(self, plain: int) -> Plaintext:
        if not isinstance(plain, int):
            raise TypeError("IntEncoder cannot encode %s." % type(plain))
        if self._unsigned and plain < 0:
            raise TypeError("IntEncoder for unsigned ints can encode only non-negative ints. See unsigned parameter.")
        return super().encode(plain)

    def decode(self, encoded: Plaintext):
        if self._unsigned:
            return super().decode_uint64(encoded)
        else:
            return super().decode_int64(encoded)


class FloatEncoder(FractionalEncoder, Encoder):
    """
    The FractionalEncoder encodes fixed-precision rational numbers as follows.
    It expands the number in a given base b,
        possibly truncating an infinite fractional part to finite precision,
        e.g. 26.75 = 2^4 + 2^3 + 2^1 + 2^(-1) + 2^(-2) when b=2.
    For the sake of the example, suppose poly_modulus is 1x^1024 + 1.
        It then represents the integer part of the number in the same way as in
        IntegerEncoder (with b=2 here), and moves the fractional part instead to the
        highest degree part of the polynomial, but with signs of the coefficients changed.
    In this example we would represent 26.75 as the polynomial
        -1x^1023 - 1x^1022 + 1x^4 + 1x^3 + 1x^1.
    In memory the negative coefficients of the polynomial will be represented
        as their negatives modulo plain_modulus.
    """

    _ATTRIBUTES = {"_context", "_integral", "_fractional", "_base"}

    # noinspection PyUnusedLocal
    def __init__(self, context: SEALContext,
                 integral: Union[int, float] = 0.4,
                 fractional: Union[int, float] = 0.4,
                 base: int = 2, **kwargs):
        """
        :param context: SEALContext
        :param integral: number of coefficients kept for the integral part of the rational number
        :param fractional: number of coefficients kept for the fractional part of the rational number
        :param base: base for integer encoding
        :param kwargs: not used, allows using Encoder parent class with kwargs each child class
        """

        # enable easy access to context attributes
        plain_mod = context.plain_modulus()
        poly_mod = context.poly_modulus()
        poly_mod_deg = context.poly_mod_deg()

        # validate integral argument
        if isinstance(integral, float):
            if not(0 <= integral <= 1):
                raise TypeError("Invalid argument for integral.")

            # take integral as a fraction of available polynomial coefficients
            integral = int(integral * poly_mod_deg)

        # validate fractional argument
        if isinstance(fractional, float):
            if not (0 <= fractional <= 1):
                raise TypeError("Invalid argument for fractional.")

            # take integral as a fraction of available polynomial coefficients
            fractional = int(fractional * poly_mod_deg)

        # validate fractional and integral combination is valid
        if integral + fractional > poly_mod_deg:
            raise TypeError("Invalid combination of arguments for integral and fractional.")

        super().__init__(plain_mod, poly_mod, integral, fractional, base)

        self._context = context
        self._integral = integral
        self._fractional = fractional
        self._base = base

    def encode(self, plain: float) -> Plaintext:
        if not isinstance(plain, float):
            raise TypeError("FloatEncoder cannot encode %s." % type(plain))
        return super().encode(plain)

    # noinspection PyMethodOverriding
    def decode(self, encoded: Plaintext):
        return super().decode(encoded)


class IntMatrixEncoder(PolyCRTBuilder, Encoder):
    """
    If plain_modulus is a prime congruent to 1 modulo 2*degree(poly_modulus), the
        plaintext elements can be viewed as 2-by-(degree(poly_modulus) / 2) matrices
        with elements integers modulo plain_modulus.
    When a desired computation can be vectorized, using PolyCRTBuilder can result in
        massive performance improvements over naively encrypting and operating on each
        input number separately. Thus, in more complicated computations this is likely
        to be by far the most important and useful encoder.
    """

    _ATTRIBUTES = {"_context", "_rows", "_cols"}

    # noinspection PyUnusedLocal
    def __init__(self, context: SEALContext, rows: int = 0, cols: int = 0, **kwargs):
        """
        :param context: SEALContext
        :param rows: number of rows in the matrix. evaluated on first call to encode() if not provided.
        :param cols: number of columns in the matrix. evaluated on first call to encode() if not provided.
        :param kwargs: not used, allows using Encoder parent class with kwargs each child class
        """

        # Verify parameters allow cipher batching
        n = context.poly_mod_deg()
        t = context.plain_modulus().value()
        if not (isprime(t) and t % (2 * n) == 1):
            raise TypeError("Batching requires that plain_mod degree be prime and congruent to 1 modulo 2 * poly_mod.")

        # In case rows and cols were not provided (i.e. zero), they will be lazy evaluated at first encode() call
        if rows > 0 and cols > 0:
            # Matrix size should align with poly_mod_deg
            if not rows * cols == self._context.poly_mod_deg():
                raise TypeError("matrix rows * cols must equal poly_mod.")

        super().__init__(context)

        self._context = context
        self._rows = rows
        self._cols = cols

    def encode(self, plain: np.ndarray) -> Plaintext:
        if (isinstance(plain, np.ndarray)
                and len(plain.shape) == 2
                and plain.dtype == np.dtype(int)):

            # In case _rows and _cols are are not known yet
            if self._rows <= 0 and self._cols <= 0:
                # evaluate them from 'plain'
                self._rows, self._cols = plain.shape

                # Matrix size should align with poly_mod_deg
                if not self._rows * self._cols == self._context.poly_mod_deg():
                    raise TypeError("matrix rows * cols must equal poly_mod.")

            # Once _rows and _cols are known, 'plain' should align to them
            if plain.shape[0] == self._rows and plain.shape[1] == self._cols:

                # Input is valid, we can start encoding

                # numpy to list
                flat_list = plain.flatten().tolist()

                # list to Plaintext
                plain_mat = Plaintext()
                self.compose(flat_list, plain_mat)

                return plain_mat

        # Invalid input
        raise TypeError("IntMatrixEncoder can only encode integer matrices "
                        "with two dimensions where rows * cols equals poly_mod.")

    # noinspection PyMethodOverriding
    def decode(self, encoded: Plaintext):
        # WARNING: this function currently has the side affect of decomposing 'encoded'
        # TODO deal with side affect

        # Plaintext to list
        self.decompose(encoded)
        plain_list = [encoded.coeff_at(i) for i in range(encoded.coeff_count())]

        # list to numpy
        plain = np.asarray(plain_list).reshape((self._rows, self._cols))

        return plain
