from difflib import SequenceMatcher


def similar(a, b):
    """
    Determine how similar two strings are.

    :param a: First string to compare.
    :param b: Second string to compare.
    :return: Similarity ratio between 0 and 1.
    """
    return SequenceMatcher(None, a, b).ratio()


print(similar('Active area', 'test active area'))