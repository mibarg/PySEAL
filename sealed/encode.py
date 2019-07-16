from typing import Union, Tuple, Type

# noinspection PyProtectedMember
from sealed._primitives import *


class Encoder:
    # TODO support matrices (PolyCRTBuilder)

    # used for object comparison
    _ATTRIBUTES = {}

    def __new__(cls,
                plain: Union[int, float, Type[int], Type[float]],
                context: SEALContext,
                **kwargs) -> Tuple[Union[None, Plaintext], "Encoder"]:

        if isinstance(plain, int) or plain is int:
            encoder = IntEncoder(context, **kwargs)
            encoded = encoder.encode(plain) if plain is not int else None
            return encoded, encoder

        if isinstance(plain, float) or plain == float:
            encoder = FloatEncoder(context, **kwargs)
            encoded = encoder.encode(plain) if plain is not float else None
            return encoded, encoder

        raise NotImplementedError("Encoder supports only int or float.")

    def encode(self, plain) -> Plaintext:
        raise NotImplementedError

    def decode(self, encoded: Plaintext):
        raise NotImplementedError

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

        super().__init__(self, **attrs)
        return True


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

    def __init__(self, context: SEALContext, base: int = 2, unsigned: bool = False, **kwargs):
        super().__init__(context.plain_modulus(), base)
        self._context = context
        self._base = base
        self._unsigned = unsigned

    def encode(self, plain: int) -> Plaintext:
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

    def __init__(self, context: SEALContext,
                 integral: Union[int, float] = 0.4,
                 fractional: Union[int, float] = 0.4,
                 base: int = 2, **kwargs):

        # enable easy access to context attributes
        plain_mod = context.plain_modulus()
        poly_mod = context.poly_modulus()
        poly_num_coeff = (poly_mod.coeff_count() - 1)

        # validate integral argument
        if isinstance(integral, float):
            if not(0 <= integral <= 1):
                raise TypeError("Invalid argument for integral.")

            # take integral as a fraction of available polynomial coefficients
            integral = int(integral * poly_num_coeff)

        # validate fractional argument
        if isinstance(fractional, float):
            if not (0 <= fractional <= 1):
                raise TypeError("Invalid argument for fractional.")

            # take integral as a fraction of available polynomial coefficients
            fractional = int(fractional * poly_num_coeff)

        # validate fractional and integral combination is valid
        if integral + fractional > poly_num_coeff:
            raise TypeError("Invalid combination of arguments for integral and fractional.")

        super().__init__(plain_mod, poly_mod, integral, fractional, base)

        self._context = context
        self._integral = integral
        self._fractional = fractional
        self._base = base

    def encode(self, plain: float) -> Plaintext:
        return super().encode(plain)

    # noinspection PyMethodOverriding
    def decode(self, encoded: Plaintext):
        return super().decode(encoded)
