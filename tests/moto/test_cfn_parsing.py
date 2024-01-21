import yaml
from moto.cloudformation.parsing import ResourceMap, parse_resource


def test_parsing():
    # language=yaml
    template_def = """
    AWSTemplateFormatVersion: '2010-09-09'
    Transform:
      - AWS::Serverless-2016-10-31

    Parameters:
      ServiceName:
        Type: String
        Default: test

    Resources:
      DynamoDBTable:
        Type: AWS::DynamoDB::Table
        Properties:
          TableName: !Sub [ "${prefix}-table", { "prefix": !Ref ServiceName } ]
          AttributeDefinitions:
            - AttributeName: id
              AttributeType: S
          KeySchema:
            - AttributeName: id
              KeyType: HASH
          BillingMode: PAY_PER_REQUEST
          StreamSpecification:
            StreamViewType: NEW_AND_OLD_IMAGES
    """

    from aws_testlib.cloudformation.cfn_template import transform_template_str
    template = yaml.safe_load(transform_template_str(template_def))

    rm = ResourceMap(
        stack_id="arn:aws:cloudformation:fake:123456789012:stack/test-stack-1/514900cb-73fd-481f-93d0-fbf5b6abd973",
        stack_name="test",
        parameters={},
        tags={},
        region_name="eu-west-1",
        account_id="123456789012",
        template=template,
        cross_stack_resources=None,
        )
    rm.load()

    resource = template['Resources']['DynamoDBTable']
    parsed = parse_resource(resource, rm)
    assert parsed is not None
