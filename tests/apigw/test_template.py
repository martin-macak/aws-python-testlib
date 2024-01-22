def test_evaluate_simple():
    from aws_testlib.apigw.template import evaluate
    got = evaluate(
        """
$a
    """,
        {"a": "Hello, World!"},
    )

    import re
    cleaned = re.sub(r"^\s+$", "", got)
    lines = list(filter(lambda x: x != "", map(lambda x: x.strip(), cleaned.split("\n"))))
    cleaned = "\n".join(lines)
    assert cleaned == "Hello, World!"
