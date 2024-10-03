import random

'''
Generates a random boolean with probability p of being True and (1 - p) of being False
'''
def generate_boolean_with_probability(p: float) -> bool:
    return True if random.random() < p else False
