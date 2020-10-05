from azepi._helpers import sorted_dict


DICT1 = {
    "a": 1,
    "b": 2,
    "c": 3,
}

DICT2 = {
    "b": 2,
    "a": 1,
    "c": 3,
}


def test_sorted_dict():
    assert list(DICT1.items()) != list(DICT2.items())
    assert list(DICT1.items()) == list(sorted_dict(DICT2).items())
