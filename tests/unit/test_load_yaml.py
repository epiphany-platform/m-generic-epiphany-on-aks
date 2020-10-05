import io
from azepi._helpers import load_yaml, dump_yaml


INPUT1 = '''
# comment1
key0:
  - name: key1  # comment2
    must-be-true: True
  # comment3
  - name: key2
    # comment4
    must-be-false: false
must-be-string: yes
must-be-literal: |
  1
  2
  3
'''

OUTPUT1 = {
    "key0": [
        {
            "name": "key1",
            "must-be-true": True,
        },
        {
            "name": "key2",
            "must-be-false": False,
        },
    ],
    "must-be-string": "yes",
    "must-be-literal": "1\n2\n3\n",
}

OUTPUT2 = '''
key0:
  - name: key1
    must-be-true: true
  - name: key2
    must-be-false: false
must-be-string: yes
must-be-literal: |
  1
  2
  3
'''

INPUT2 = '''
aaa:
---
bbb:
'''

OUTPUT3 = [
    {
        "aaa": None,
    },
    {
        "bbb": None,
    },
]


def test_load_yaml_with_single_document():
    assert load_yaml(INPUT1) == OUTPUT1

    try:
        stream = io.StringIO()
        dump_yaml(load_yaml(INPUT1), stream=stream)
        dumped = stream.getvalue()
    finally:
        stream.close()

    assert dumped.strip() == OUTPUT2.strip()


def test_load_yaml_with_multiple_documents():
    assert load_yaml(INPUT2) == OUTPUT3
