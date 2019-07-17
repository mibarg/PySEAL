# noinspection PyProtectedMember
from sealed._primitives import *


class SEALContext(SEALContext):
    def __eq__(self, other) -> bool:
        if (isinstance(other, SEALContext)
                and self.poly_modulus().coeff_count() == other.poly_modulus().coeff_count()
                and self.total_coeff_modulus().significant_bit_count() == other.total_coeff_modulus().significant_bit_count()
                and self.plain_modulus().value() == other.plain_modulus().value()):
            return True
        else:
            return False
