"""Unit testing of the "memoize" function."""

from azepi._helpers import memoize


@memoize
def _function1(a_str):
    return a_str


def test_memoize():
    """Unit test for the "memoize" function."""

    assert _function1("asd") is _function1("asd")
    assert _function1("asd") is _function1("asd")
    assert _function1("asd") is _function1("asd")

    assert _function1("zxc") is _function1("zxc")
    assert _function1("zxc") is _function1("zxc")
    assert _function1("zxc") is _function1("zxc")

    assert _function1("asd") is not _function1("zxc")

    memo = getattr(_function1, "memo")

    assert len(memo) == 2

    assert _function1("asd") is memo["asd"]
    assert _function1("zxc") is memo["zxc"]
