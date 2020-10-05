from azepi._helpers import combine


INPUT = {
    "must-be-present-1": None,
    "must-be-true": False,
    "must-be-nested" : {
        "must-be-present-1": None,
        "must-be-true": False,
    },
    "must-be-empty": ["must-be-absent"],
    "must-be-non-empty": [],
}

UPDATE = {
    "must-be-present-2": None,
    "must-be-true": True,
    "must-be-nested": {
        "must-be-present-2": None,
        "must-be-true": True,
    },
    "must-be-empty": [],
    "must-be-non-empty": ["must-be-present"],
}

OUTPUT = {
    "must-be-present-1": None,
    "must-be-present-2": None,
    "must-be-true": True,
    "must-be-nested" : {
        "must-be-present-1": None,
        "must-be-present-2": None,
        "must-be-true": True,
    },
    "must-be-empty": [],
    "must-be-non-empty": ["must-be-present"],
}


def test_combine():
    assert combine(INPUT, UPDATE) == OUTPUT
