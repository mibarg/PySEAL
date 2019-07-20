"""
Primitives
Python wrappers to pybind11 generated shared objects
Add Python-native functionality to cpp-originated classes such as pickle, compare and init
"""

# noinspection PyProtectedMember
from sealed._primitives import *


class SEALContext(SEALContext):
    def __eq__(self, other) -> bool:
        """
        SEALContext equality is determined by the underlying SEAL parameters:
        poly_modulus, coeff_modulus and plain_modulus
        """
        if (isinstance(other, SEALContext)
                and self.poly_modulus().coeff_count() == other.poly_modulus().coeff_count()
                and self.total_coeff_modulus().significant_bit_count() ==
                other.total_coeff_modulus().significant_bit_count()
                and self.plain_modulus().value() == other.plain_modulus().value()):
            return True
        else:
            return False

    def poly_mod_deg(self):
        return self.poly_modulus().coeff_count() - 1


class ChooserEncoder(ChooserEncoder):
    def __init__(self, base: int = 2):
        super().__init__(base)


class ChooserPoly(ChooserPoly):
    def __init__(self, max_num_coeff: int = None, max_coeff_abs_val: int = None):
        if max_num_coeff is None and max_coeff_abs_val is None:
            super().__init__()
        else:
            super().__init__(max_num_coeff, max_coeff_abs_val)
