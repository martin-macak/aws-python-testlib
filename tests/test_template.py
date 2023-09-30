import re


def test_evaluate():
    from aws_testlib.apigw.template import evaluate
    got = evaluate(
        """
        $input.path('foo')
        """,
        {
            'foo': 'bar'
        }
    )

    assert re.sub(r'\s+', '', got) == 'bar'
