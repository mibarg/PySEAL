from sealed._primitives import SEALContext


def is_pow_of_two(num: int):
    return isinstance(num, int) and ((num & (num - 1)) == 0) and num != 0


def get_plain_mod(context: SEALContext):
    return context.poly_modulus().coeff_count() - 1
