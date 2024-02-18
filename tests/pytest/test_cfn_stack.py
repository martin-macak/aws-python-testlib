import json

import boto3
from moto import (
    mock_dynamodb,
    mock_sqs,
    mock_sns,
    mock_lambda_simple,
    mock_iam, mock_dynamodbstreams,
)

from aws_testlib.pytest.cfn_stack import build_cfn_stack


@mock_dynamodb
@mock_iam
@mock_lambda_simple
@mock_dynamodbstreams
def test_build_cfn_stack_1():
    import boto3
    with build_cfn_stack(template_name="test_stack_1.template.yaml",
                         components=["AWS::DynamoDB::Table"], ):
        dynamodb_client = boto3.client('dynamodb')
        response = dynamodb_client.list_tables()
        assert "test-table" in response['TableNames']


@mock_lambda_simple
@mock_iam
@mock_dynamodbstreams
def test_build_cfn_stack_2(monkeypatch, ):
    def mock_some_func():
        return 2

    from tests.src.test_lambda.echo import app
    monkeypatch.setattr(app, "some_func", mock_some_func)

    with build_cfn_stack(template_name="test_stack_2.template.yaml",
                         components=["AWS::Lambda::Function", ],
                         mock_lambda_with_local_packaged=True,
                         ):
        lambda_client = boto3.client('lambda')
        result = lambda_client.invoke(
            FunctionName="test-echo",
            InvocationType="RequestResponse",
            Payload=b'{"foo": "bar"}',
        )

        payload = result["Payload"]
        data = json.loads(payload.read())

        assert data == 2


@mock_sqs
def test_build_cfn_stack_3(monkeypatch, ):
    with build_cfn_stack(template_name="test_stack_3.template.yaml",
                         components=["AWS::SQS::Queue", ],
                         ):
        sqs_client = boto3.client("sqs")
        get_queue_result = sqs_client.get_queue_url(QueueName="test-queue")
        assert get_queue_result["QueueUrl"] is not None


@mock_sns
def test_build_cfn_stack_4(monkeypatch, ):
    with build_cfn_stack(template_name="test_stack_4.template.yaml",
                         components=["AWS::SNS::Topic", ],
                         ):
        sns_client = boto3.client("sns")
        list_topics_result = sns_client.list_topics()
        assert list_topics_result["Topics"] is not None
        assert len(list_topics_result["Topics"]) == 1
