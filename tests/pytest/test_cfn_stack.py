from moto import (
    mock_cloudformation,
    mock_dynamodb,
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
