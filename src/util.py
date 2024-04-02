def flatten(list):
    return [x for sublist in list for x in sublist]


def clamp(x, minimum, maximum):
    return min(maximum, max(x, minimum))
