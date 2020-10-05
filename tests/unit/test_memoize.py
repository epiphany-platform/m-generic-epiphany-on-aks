from azepi._helpers import memoize


@memoize
def function1(a_str):
    return a_str


def test_memoize():
    assert function1("asd") is function1("asd")
    assert function1("asd") is function1("asd")
    assert function1("asd") is function1("asd")

    assert function1("zxc") is function1("zxc")
    assert function1("zxc") is function1("zxc")
    assert function1("zxc") is function1("zxc")

    assert function1("asd") is not function1("zxc")

    memo = getattr(function1, "memo")

    assert len(memo) == 2

    assert function1("asd") is memo["asd"]
    assert function1("zxc") is memo["zxc"]
