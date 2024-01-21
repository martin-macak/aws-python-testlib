import os
from typing import Literal, Optional, Any, Type

import boto3
from moto.cloudformation.models import CloudFormationModel
from moto.cloudformation.parsing import ResourceMap, parse_resource

__dir = os.path.abspath(os.path.dirname(__file__))

SupportedComponents = Literal[
    "AWS::DynamoDB::Table",
    "AWS::SQS::Queue",
    "AWS::SNS::Topic",
    "AWS::S3::Bucket",
    "AWS::Lambda::Function",
]

DEFAULT_DEPLOYED_COMPONENTS = [
    "AWS::DynamoDB::Table",
]


def deploy_template(
    template: dict,
    deployed_components: Optional[list[SupportedComponents]] = None,
    additional_tags: Optional[dict[str]] = None,
    additional_parameters: Optional[dict[str]] = None,
):
    if deployed_components is None:
        deployed_components = DEFAULT_DEPLOYED_COMPONENTS

    import uuid
    stack_resource_id = uuid.uuid4()
    stack_name = "test-stack"
    aws_account_id = os.environ.get("MOTO_ACCOUNT_ID", "123456789012")
    aws_region = os.environ.get("AWS_REGION", "fake")
    rm = ResourceMap(
        stack_id=f"arn:aws:cloudformation:{aws_region}:{aws_account_id}:stack/{stack_name}/{stack_resource_id}",
        stack_name=stack_name,
        parameters=additional_parameters or {},
        tags=additional_tags or {},
        region_name=aws_region,
        account_id=aws_account_id,
        template=template,
        cross_stack_resources=None,
    )
    rm.load()

    resource_names = rm.resources
    created_resources = set()

    for resource_name in resource_names:
        if resource_name in created_resources:
            continue

        resource_def_json = template["Resources"][resource_name]
        resource = parse_resource(resource_def_json, rm)
        if resource is None:
            alternate_resource = find_alternate_resource(
                resource_name=resource_name,
                resource_def_json=resource_def_json,
                rm=rm,
            )
            if alternate_resource is None:
                continue
            else:
                resource = alternate_resource

        resource_class, resource_json, resource_type = resource
        created = check_and_create_resource(resource_name=resource_name,
                                            resource_json=resource_json,
                                            resource_type=resource_type,
                                            resource_class=resource_class,
                                            resource_map=rm,
                                            account_id=aws_account_id,
                                            region_name=aws_region,
                                            deployed_components=deployed_components, )

        if created:
            created_resources.add(resource_name)


def check_and_create_resource(resource_name: str,
                              resource_json: dict[str, Any],
                              resource_type: str,
                              resource_class: type[CloudFormationModel],
                              resource_map: ResourceMap,
                              account_id: str,
                              region_name: str,
                              deployed_components: Optional[list[SupportedComponents]] = None,
                              ) -> bool:
    if deployed_components is None:
        deployed_components = DEFAULT_DEPLOYED_COMPONENTS

    if resource_type not in deployed_components:
        return False

    # Create
    match resource_type:
        case "AWS::DynamoDB::Table":
            _create_dynamodb_table(
                table_name=resource_json["Properties"]["TableName"],
                definition=resource_json,
            )
            return True
        case "AWS::Lambda::Function":
            _create_lambda(
                function_name=resource_json["Properties"]["FunctionName"],
                definition=resource_json,
            )
        case _:
            return False


def find_alternate_resource(
    resource_name: str,
    resource_def_json: dict[str, Any],
    rm: ResourceMap,
) -> Optional[tuple[Type[CloudFormationModel], Any, str]]:
    resource_type = resource_def_json["Type"]
    match resource_type:
        case "AWS::Serverless::Function":
            alternate_def = {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": resource_def_json["Properties"]["FunctionName"],
                    # "Code": {
                    #     "S3Bucket": "fake",
                    #     "S3Key": "fake",
                    # },
                    "Code": {
                        "ImageUri": "http://foo.fake",
                    },
                },
            }
            alternate_resource = parse_resource(
                alternate_def,
                rm,
            )

            return alternate_resource
        case _:
            return None


def _create_dynamodb_table(
    table_name: str,
    definition: dict[str, Any],
):
    dynamodb_client = boto3.client('dynamodb')
    try:
        dynamodb_client.create_table(
            TableName=table_name,
            AttributeDefinitions=definition["Properties"]["AttributeDefinitions"],
            KeySchema=definition["Properties"]["KeySchema"],
            BillingMode="PAY_PER_REQUEST",
        )
        table = boto3.resource('dynamodb').Table(table_name)
        table.wait_until_exists()
    except dynamodb_client.exceptions.TableAlreadyExistsException:
        pass
    except dynamodb_client.exceptions.ResourceInUseException:
        pass


def _create_lambda(
    function_name: str,
    definition: dict[str, Any],
):
    iam_client = boto3.client('iam')
    iam_client.create_role(
        RoleName=f"lambda-role-{function_name}",
        Path="/service-role/tests/",
        AssumeRolePolicyDocument="""
        {
            "Version":"2012-10-17",
            "Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]
        }
            """,
    )

    lambda_client = boto3.client('lambda')
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime="python3.11",
        Handler="app.lambda_handler",
        Role=f"arn:aws:iam::123456789012:role/service-role/tests/lambda-role-{function_name}",
        Code={
            "ZipFile": "",
        },
    )
