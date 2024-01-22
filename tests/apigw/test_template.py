def test_evaluate_simple():
    from aws_testlib.apigw.template import evaluate
    got = evaluate(
        """
$a
    """,
        {"a": "Hello, World!"},
    )

    assert _clean_output(got) == "Hello, World!"


def test_evaluate_int_conversion():
    from aws_testlib.apigw.template import evaluate
    got = evaluate(
        """
    #set($Integer = 0)
    #set($val = "9")
    $Integer.parseInt($val)
    """,
        {"a": "Hello, World!"},
    )

    assert _clean_output(got) == "9"


def _clean_output(val: str) -> str:
    import re

    cleaned = re.sub(r"^\s+$", "", val)
    lines = list(filter(lambda x: x != "", map(lambda x: x.strip(), cleaned.split("\n"))))
    cleaned = "\n".join(lines)

    return cleaned
