import os
from typing import Literal, Optional, Any

import boto3
import moto.dynamodb.models as dynamodb_models
from moto.cloudformation.models import CloudFormationModel
from moto.cloudformation.parsing import ResourceMap, parse_resource

SupportedComponents = Literal[
    "AWS::DynamoDB::Table",
    "AWS::SQS::Queue",
    "AWS::SNS::Topic",
    "AWS::S3::Bucket",
    "AWS::Serverless::Function",
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
        resource_class, resource_json, resource_type = parse_resource(resource_def_json, rm)
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
    model = resource_class.create_from_cloudformation_json(resource_name=resource_name,
                                                           cloudformation_json=resource_json,
                                                           account_id=account_id,
                                                           region_name=region_name,
                                                           )

    if deployed_components is None:
        deployed_components = DEFAULT_DEPLOYED_COMPONENTS

    if resource_type not in deployed_components:
        return False

    # Create
    match resource_type:
        case "AWS::DynamoDB::Table":
            _create_dynamodb_table(
                table_name=resource_json["Properties"]["TableName"],
                model=model,
            )
            return True
        case _:
            return False


def _create_dynamodb_table(
    table_name: str,
    model: dynamodb_models.table.Table,
):
    dynamodb_client = boto3.client('dynamodb')
    try:
        dynamodb_client.create_table(
            TableName=table_name,
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=model.attr,
            KeySchema=list(filter(lambda x: x is not None, [
                {
                    "AttributeName": model.hash_key_names[0],
                    "KeyType": "HASH",
                },
                {
                    "AttributeName": model.range_key_names[0],
                    "KeyType": "RANGE",
                } if model.has_range_key else None,
            ])),
            Tags=[
                {
                    "Key": tag.key,
                    "Value": tag.value,
                }
                for tag in model.tags
            ],
        )
        table = boto3.resource('dynamodb').Table(table_name)
        table.wait_until_exists()
    except dynamodb_client.exceptions.TableAlreadyExistsException:
        pass
    except dynamodb_client.exceptions.ResourceInUseException:
        pass
