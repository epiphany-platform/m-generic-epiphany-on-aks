"""Unit testing of the "dictify" function."""

from azepi._helpers import dictify


INPUT = [
    {
        "name": "key1",
        "must-be-true": True,
    },
    {
        "name": "key2",
        "must-be-false": False,
    },
]

OUTPUT = {
    "key1": {
        "name": "key1",
        "must-be-true": True,
    },
    "key2": {
        "name": "key2",
        "must-be-false": False,
    }
}


def test_dictify():
    """Unit test for the "dictify" function."""

    assert dictify(INPUT) == OUTPUT
