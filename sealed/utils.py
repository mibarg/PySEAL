def is_pow_of_two(num: int):
    return isinstance(num, int) and ((num & (num - 1)) == 0) and num != 0
