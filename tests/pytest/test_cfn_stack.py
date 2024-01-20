from moto import (
    mock_cloudformation,
    mock_dynamodb,
    mock_sqs,
    mock_sns,
    mock_lambda_simple,
)

from aws_testlib.pytest.cfn_stack import build_cfn_stack


@mock_cloudformation
@mock_dynamodb
@build_cfn_stack(template_name="test_stack_1.template.yaml")
def test_build_cfn_stack():
    import boto3
    dynamodb_client = boto3.client('dynamodb')
    response = dynamodb_client.list_tables()
    assert "test-table" in response['TableNames']


@mock_cloudformation
@mock_dynamodb
@mock_sqs
@mock_lambda_simple
@mock_sns
@build_cfn_stack(template_name="test_stack_2.template.yaml")
def test_build_cfn_stack():
    import boto3
    dynamodb_client = boto3.client('dynamodb')
    sns_client = boto3.client('sns')
    sqs_client = boto3.client('sqs')
    lambda_client = boto3.client('lambda')

    response = dynamodb_client.list_tables()
    assert "test-table" in response['TableNames']

    response = sns_client.list_topics()
    topics = response['Topics']
    assert "test-topic" in [t['TopicArn'].split(":")[5] for t in topics]

    response = sqs_client.list_queues()
    queue_urls = response['QueueUrls']
    assert "test-queue" in [q.removeprefix("https://").split("/")[2] for q in queue_urls]

    topic_arn = topics[0]['TopicArn']
    queue_arn = "arn:aws:sqs:fake:123456789012:test-queue"

    sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='sqs',
        Endpoint=queue_arn,
    )

    sns_client.publish(
        TopicArn=topic_arn,
        Message="test message",
    )

    response = sqs_client.receive_message(
        QueueUrl=queue_urls[0],
    )
    messages = response['Messages']
    assert len(messages) == 1
