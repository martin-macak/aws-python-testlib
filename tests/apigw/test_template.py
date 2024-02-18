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


def test_aws_api_gateway_context():
    from aws_testlib.apigw.template import AWSApiGatewayContext
    context = AWSApiGatewayContext()

    request_context = context._request_context
    assert request_context is None


def test_evaluate_aws_input_body():
    from aws_testlib.apigw.template import evaluate_aws
    got = evaluate_aws(
        """
        $input.body
    """,
        body={"foo": {"bar": "baz"}},
    )

    assert _clean_output(got) == '{"foo": {"bar": "baz"}}'


def test_evaluate_aws_input_json():
    from aws_testlib.apigw.template import evaluate_aws
    got = evaluate_aws(
        """
        $input.json("$.foo.bar")
    """,
        body={"foo": {"bar": "baz"}},
    )

    assert _clean_output(got) == '"baz"'


def test_evaluate_aws_input_path():
    from aws_testlib.apigw.template import evaluate_aws
    got = evaluate_aws(
        """
        $input.path("$.foo.bar")
    """,
        body={"foo": {"bar": "baz"}},
    )

    assert _clean_output(got) == 'baz'


def test_evaluate_aws_input_path_and_stage_variables():
    from aws_testlib.apigw.template import evaluate_aws
    got = evaluate_aws(
        """
        $input.path("$.foo.bar"),$stageVariables.stg
    """,
        body={"foo": {"bar": "baz"}},
        stage_variables={"stg": "dev"},
    )

    assert _clean_output(got) == 'baz,dev'
