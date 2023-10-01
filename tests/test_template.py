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


def test_evaluate_with_stage_variables():
    from aws_testlib.apigw.template import evaluate
    got = evaluate(
        """
        $input.path('foo'),$stageVariables.stage
        """,
        {
            'foo': 'bar'
        },
        {
            "stage": "dev",
        }
    )

    assert re.sub(r'\s+', '', got) == 'bar,dev'
