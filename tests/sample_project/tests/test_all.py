import os.path
import sys

from moto import mock_dynamodb, mock_lambda_simple, mock_iam, mock_dynamodbstreams

from aws_testlib.pytest.cfn_stack import build_cfn_stack

_dir = os.path.abspath(os.path.dirname(__file__))


@mock_dynamodb
@mock_dynamodbstreams
@mock_lambda_simple
@mock_iam
def test(monkeypatch, ):
    state = {
        "calls": {
            "process_cdc": [],
        },
    }

    base_dir = os.path.abspath(os.path.join(_dir, ".."))

    try:
        sys.path.append(base_dir)
        # noinspection PyUnresolvedReferences
        from cdc_lambda_handler import cdc as cdc_module

        def mock_process_cdc(event):
            state["calls"]["process_cdc"].append(event)

        monkeypatch.setattr(cdc_module, "process_cdc", mock_process_cdc)

        # noinspection PyArgumentList
        with build_cfn_stack(
            template_name="template.yaml",
            components=["AWS::DynamoDB::Table", "AWS::Lambda::Function"],
            mock_lambda_with_local_packaged=True,
        ) as stack:
            stack.process_event_loop()
    finally:
        sys.path.pop()

    assert len(state["calls"]["process_cdc"]) == 1
