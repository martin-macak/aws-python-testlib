import boto3
from moto import (
    mock_dynamodb,
    mock_sqs,
    mock_sns,
    mock_lambda_simple,
    mock_iam,
)

from aws_testlib.pytest.cfn_stack import build_cfn_stack


@mock_dynamodb
def test_build_cfn_stack_1():
    import boto3
    with build_cfn_stack(template_name="test_stack_1.template.yaml",
                         components=["AWS::DynamoDB::Table"], ):
        dynamodb_client = boto3.client('dynamodb')
        response = dynamodb_client.list_tables()
        assert "test-table" in response['TableNames']


@mock_dynamodb
@mock_sqs
@mock_lambda_simple
@mock_sns
@mock_iam
def test_build_cfn_stack_2(monkeypatch, ):
    def mock_some_func():
        return 2

    from tests.test_lambda.echo import app
    monkeypatch.setattr(app, "some_func", mock_some_func)

    with build_cfn_stack(template_name="test_stack_2.template.yaml",
                         components=["AWS::DynamoDB::Table", "AWS::SQS::Queue", "AWS::SNS::Topic",
                                     "AWS::Lambda::Function"],
                         mock_lambda_with_local_packaged=True,
                         ):

        lambda_client = boto3.client('lambda')
        result = lambda_client.invoke(
            FunctionName="test-echo",
            InvocationType="RequestResponse",
            Payload=b'{"foo": "bar"}',
        )

        payload = result["Payload"]
        data = payload.read()

        print(result)
