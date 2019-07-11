from seal._primitives import EncryptionParameters, SEALContext, coeff_modulus_128, coeff_modulus_192
from seal.utils import is_pow_of_two


class CipherScheme:
    def __init__(self,
                 poly_mod: int = 2048,
                 coeff_mod: int = 0,
                 plain_mod: int = 256,
                 security: int = 128,
                 noise_st: float = 3.19):

        params = EncryptionParameters()

        # Security
        assert security in (128, 192)

        # Polynomial modulus
        assert is_pow_of_two(poly_mod)
        params.set_poly_modulus("1x^%d + 1" % poly_mod)

        # Coefficient modulus
        assert isinstance(coeff_mod, int)
        assert isinstance(coeff_mod, int)
        if coeff_mod <= 0:
            # Automatically choose by SEAL recommendations
            coeff_mod_func = {128: coeff_modulus_128, 192: coeff_modulus_192}
            params.set_coeff_modulus(coeff_mod_func[security](poly_mod))

        # Plaintext modulus
        assert isinstance(plain_mod, int)
        params.set_plain_modulus(plain_mod)

        self._context = SEALContext(params)

    def __str__(self):
        "CipherScheme(poly_mod={}, coeff_mod_size={} bits, plain_mod={}, noise_std={})".format(
            self._context.poly_modulus(), self._context.total_coeff_modulus().significant_bit_count(),
            self._context.plain_modulus().value(), self._context.noise_standard_deviation())
