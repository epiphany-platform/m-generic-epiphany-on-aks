import sys
import copy
import pathlib
import difflib
import ruamel.yaml


def memoize(function):
    """Simple memoize implementation (single str argument)."""

    def _memoize(a_str):
        if not hasattr(_memoize, "memo"):
            setattr(_memoize, "memo", {})

        memo = getattr(_memoize, "memo")

        if a_str not in memo:
            memo[a_str] = function(a_str)

        return memo[a_str]

    return _memoize


@memoize
def get_path(a_str):
    """Memoized path getter."""
    return pathlib.Path(a_str).resolve()


def combine(to_merge, extend_by):
    """Merge nested dictionaries."""

    # Implementation taken from Epiphany's helpers
    def _combine(to_merge, extend_by):
        for key, value in extend_by.items():
            if key in to_merge:
                if isinstance(to_merge[key], dict):
                    _combine(to_merge[key], value)
                else:
                    to_merge[key] = value
            else:
                to_merge[key] = value

    to_merge = copy.deepcopy(to_merge)

    _combine(to_merge, extend_by)

    return to_merge


def dictify(a_list, *, key_name="name"):
    """Convert a list-based dictionary to a dictionary."""
    return {
        item[key_name]: item
        for item in copy.deepcopy(a_list)
    }


def undictify(a_dict, *, key_name="name"):
    """Convert a dictionary to a list-based dictionary."""
    # Please note the "name" key is not removed
    return [
        combine(value, {key_name: key})
        for key, value in copy.deepcopy(a_dict).items()
    ]


def select(a_list, query, *, exactly=0):
    """Scan a list of dictionaries and pick ones that match the query."""

    documents = []
    counter = 0

    for item in a_list:
        if not query(item):
            continue

        documents.append(copy.deepcopy(item))

        if bool(exactly):
            counter += 1
            if counter >= exactly:
                break

    if counter >= exactly:
        if exactly == 1:
            return documents[0]
        else:
            return documents


def q_kind(kind):
    """Retun simple kind query."""
    return lambda item: item["kind"] == kind


def load_yaml(path_or_str):
    """Load and parse yaml document(s)."""

    # This removes all ruamel comments (TODO: fix the "combine" function)
    def clean(something):
        if isinstance(something, dict):
            return dict(
                (key, clean(value))
                for key, value in something.items()
            )
        if isinstance(something, list):
            return list(
                clean(value)
                for value in something
            )
        return copy.deepcopy(something)

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    loaded = list(yaml.load_all(path_or_str))

    if len(loaded) == 1:
        return clean(loaded[0])

    return clean(loaded)


def dump_yaml(list_or_str, *, stream=sys.stdout):
    """Print yaml document(s)."""

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)

    if isinstance(list_or_str, list):
        yaml.dump_all(list_or_str, stream)
        return

    yaml.dump(list_or_str, stream)


def to_literal_scalar(a_str):
    """Helper function to enforce literal scalar block (ruamel.yaml)."""
    return ruamel.yaml.scalarstring.LiteralScalarString(a_str)


def udiff(str_a, str_b, *, number_of_context_lines=0):
    """Compute unified diff of two strings."""

    # "True" preserves line endings
    lines_a = str_a.splitlines(True)
    lines_b = str_b.splitlines(True)

    diff_generator = difflib.unified_diff(lines_a,
                                          lines_b,
                                          n=number_of_context_lines)
    # Skip two unneeded lines
    diff_lines = list(diff_generator)[2:]

    diff_str = "".join(diff_lines)

    return diff_str