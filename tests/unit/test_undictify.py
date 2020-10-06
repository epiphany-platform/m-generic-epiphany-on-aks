"""Unit testing of the "undictify" function."""

from azepi._helpers import undictify


INPUT = {
    "key1": {
        "name": "key1",
        "must-be-true": True,
    },
    "key2": {
        "name": "key2",
        "must-be-false": False,
    }
}

OUTPUT = [
    {
        "name": "key1",
        "must-be-true": True,
    },
    {
        "name": "key2",
        "must-be-false": False,
    },
]


def test_undictify():
    """Unit test for the "undictify" function."""

    assert undictify(INPUT) == OUTPUT
