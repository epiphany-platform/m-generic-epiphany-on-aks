# pylint: disable=missing-module-docstring,missing-function-docstring

from azepi._helpers import select, q_kind


INPUT = [
    {
        "kind": "kind1",
        "index": 0,
    },
    {
        "kind": "kind2",
        "index": 1,
    },
    {
        "kind": "kind1",
        "index": 2,
    },
]

OUTPUT1 = INPUT

OUTPUT2 = [
    {
        "kind": "kind1",
        "index": 0,
    },
    {
        "kind": "kind1",
        "index": 2,
    },
]


def test_select_without_query():
    assert select(INPUT, lambda _: False) == []

    assert select(INPUT, lambda _: False, exactly=1) is None

    assert select(INPUT, lambda _: True) == OUTPUT1

    assert select(INPUT, lambda _: True, exactly=1) == OUTPUT1[0]

    assert select(INPUT, lambda _: True, exactly=2) == OUTPUT1[:2]

    assert select(INPUT, lambda _: True, exactly=3) == OUTPUT1

    assert select(INPUT, lambda _: True, exactly=4) is None


def test_select_with_query():
    assert select(INPUT, q_kind("kind1")) == OUTPUT2

    assert select(INPUT, q_kind("kind1"), exactly=1) == OUTPUT2[0]

    assert select(INPUT, q_kind("kind1"), exactly=2) == OUTPUT2

    assert select(INPUT, q_kind("kind1"), exactly=3) is None
