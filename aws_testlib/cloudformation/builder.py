import json
import os
from typing import Literal, Optional, Any, Type

import boto3
from moto.cloudformation.models import CloudFormationModel
from moto.cloudformation.parsing import ResourceMap, parse_resource

from aws_testlib.cloudformation.stack import Stack

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
    stack: Stack,
    template_file_name: str,
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
                stack=stack,
                resource_name=resource_name,
                resource_def_json=resource_def_json,
                rm=rm,
            )
            if alternate_resource is None:
                continue
            else:
                resource = alternate_resource

        resource_class, resource_json, resource_type = resource
        created = check_and_create_resource(
            stack=stack,
            template_file_name=template_file_name,
            resource_name=resource_name,
            resource_json=resource_json,
            resource_type=resource_type,
            resource_class=resource_class,
            resource_map=rm,
            account_id=aws_account_id,
            region_name=aws_region,
            deployed_components=deployed_components,
        )

        if created:
            created_resources.add(resource_name)


def check_and_create_resource(
    stack: Stack,
    template_file_name: str,
    resource_name: str,
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
                stack=stack,
                table_name=resource_json["Properties"]["TableName"],
                definition=resource_json,
            )
            return True
        case "AWS::Lambda::Function":
            _create_lambda(
                stack=stack,
                template_file_name=template_file_name,
                function_name=resource_json["Properties"]["FunctionName"],
                definition=resource_json,
            )
        case "AWS::SQS::Queue":
            _create_queue(
                stack=stack,
                template_file_name=template_file_name,
                queue_name=resource_json["Properties"]["QueueName"],
                definition=resource_json,
            )
        case "AWS::SNS::Topic":
            _create_topic(
                stack=stack,
                template_file_name=template_file_name,
                topic_name=resource_json["Properties"]["TopicName"],
                definition=resource_json,
            )
        case _:
            return False


def find_alternate_resource(
    stack: Stack,
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
                    "Code": {
                        "ImageUri": f"{resource_def_json['Properties']['CodeUri']}:"
                                    f"{resource_def_json['Properties']['Handler']}",
                    },
                },
            }
            alternate_resource = parse_resource(
                alternate_def,
                rm,
            )

            _handle_serverless_extensions(
                rm=rm,
                stack=stack,
                resource_name=resource_name,
                resource_def_json=resource_def_json,
                alternate_resource=alternate_resource,
            )

            return alternate_resource
        case _:
            return None


def _create_dynamodb_table(
    stack: Stack,
    table_name: str,
    definition: dict[str, Any],
):
    dynamodb_client = boto3.client("dynamodb")

    spec = {
        "TableName": table_name,
        "AttributeDefinitions": definition["Properties"]["AttributeDefinitions"],
        "KeySchema": definition["Properties"]["KeySchema"],
        "BillingMode": "PAY_PER_REQUEST",
        "Tags": definition.get("Tags"),
        "StreamSpecification": definition["Properties"].get("StreamSpecification"),
        "GlobalSecondaryIndexes": definition["Properties"].get("GlobalSecondaryIndexes"),
    }

    _delete_empty_keys(spec)

    if "StreamSpecification" in spec:
        spec["StreamSpecification"]["StreamEnabled"] = True

    try:
        dynamodb_client.create_table(**spec)
        table = boto3.resource("dynamodb").Table(table_name)
        table.wait_until_exists()
    except dynamodb_client.exceptions.TableAlreadyExistsException:
        pass
    except dynamodb_client.exceptions.ResourceInUseException:
        pass

    if "StreamSpecification" in spec:
        dynamodb_stream = boto3.client("dynamodbstreams")
        list_streams_response = dynamodb_stream.list_streams(
            TableName=table_name,
        )
        streams = list_streams_response["Streams"]
        stream = streams[0]

        stream_spec = dynamodb_stream.describe_stream(
            StreamArn=stream["StreamArn"],
        )["StreamDescription"]

        shards = stream_spec["Shards"]
        shard = shards[0]

        iterator = dynamodb_stream.get_shard_iterator(
            StreamArn=stream["StreamArn"],
            ShardId=shard["ShardId"],
            ShardIteratorType="TRIM_HORIZON",
        )

        def handle(ctx):
            iterator_arn = iterator["ShardIterator"]
            if ctx.get_state("next_shard_iterator") is not None:
                iterator_arn = ctx.get_state("next_shard_iterator")

            get_records_result = dynamodb_stream.get_records(
                ShardIterator=iterator_arn,
            )
            records = get_records_result["Records"]
            next_shard_iterator = get_records_result["NextShardIterator"]
            ctx.add_state("next_shard_iterator", next_shard_iterator)

            ctx.signal(
                resource_name=table_name,
                signal_type="DynamoDBStream",
                event={
                    "records": records,
                }
            )

        stack.register_to_event_loop(
            handle_id=shard["ShardId"],
            resource_name=table_name,
            resource_handle=handle,
        )


def _create_lambda(
    stack: Stack,
    template_file_name: str,
    function_name: str,
    definition: dict[str, Any],
):
    iam_client = boto3.client("iam")
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

    code_uri = definition["Properties"]["Code"]["ImageUri"]

    lambda_client = boto3.client("lambda")
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime="python3.11",
        Handler="app.lambda_handler",
        Role=f"arn:aws:iam::123456789012:role/service-role/tests/lambda-role-{function_name}",
        Code={
            "ZipFile": f"""{json.dumps(
                {
                    "TemplateFileName": template_file_name,
                }
            )}""",
        },
        Tags={
            "testlib:template_file_name": template_file_name,
            "testlib:lambda:code-uri": code_uri,
            **definition.get("Tags", {}),
        },
    )


def _create_queue(
    stack: Stack,
    template_file_name: str,
    queue_name: str,
    definition: dict[str, Any],
):
    sqs_client = boto3.client("sqs")

    spec = {
        "QueueName": queue_name,
        "Tags": definition.get("Tags")
    }

    _delete_empty_keys(spec)

    sqs_client.create_queue(**spec)


def _create_topic(
    stack: Stack,
    template_file_name: str,
    topic_name: str,
    definition: dict[str, Any],
):
    sns_client = boto3.client("sns")

    spec = {
        "Name": topic_name,
        "Tags": definition.get("Tags")
    }

    _delete_empty_keys(spec)

    sns_client.create_topic(**spec)


def _handle_serverless_extensions(
    stack: Stack,
    rm: ResourceMap,
    resource_name: str,
    resource_def_json: dict[str, Any],
    alternate_resource: tuple[Type[CloudFormationModel], Any, str],
):
    serverless_type = resource_def_json["Type"]
    match serverless_type:
        case "AWS::Serverless::Function":
            _handle_serverless_function_extension(
                stack=stack,
                rm=rm,
                resource_name=resource_name,
                resource_def_json=resource_def_json,
                alternate_resource=alternate_resource,
            )


def _handle_serverless_function_extension(
    stack: Stack,
    rm: ResourceMap,
    resource_name: str,
    resource_def_json: dict[str, Any],
    alternate_resource: tuple[Type[CloudFormationModel], Any, str],
):
    aws_lambda = boto3.client("lambda")

    properties = resource_def_json["Properties"]
    if "Events" in properties:
        for event_name, event in properties["Events"].items():
            event_type = event["Type"]
            match event_type:
                case "DynamoDB":
                    stream = event["Properties"]["Stream"]
                    if "Fn::GetAtt" in stream:
                        table_logical_resource_id = stream["Fn::GetAtt"].split(".")[0]
                    elif "Ref" in stream:
                        table_logical_resource_id = stream["Ref"]
                    else:
                        table_logical_resource_id = str(stream)
                    table = rm.get(table_logical_resource_id)
                    table_name = table.name

                    def handle(ev):
                        function_name = alternate_resource[1]["Properties"]["FunctionName"]
                        aws_lambda.invoke(
                            FunctionName=function_name,
                            InvocationType="RequestResponse",
                            Payload=json.dumps({}),
                        )

                    stack.register_signal_handler(
                        resource_name=table_name,
                        signal_type="DynamoDBStream",
                        handler=handle,
                    )


def _delete_empty_keys(d: dict[str, Any]):
    for k, v in list(d.items()):
        if isinstance(v, dict):
            _delete_empty_keys(v)
        elif v is None:
            del d[k]
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    _delete_empty_keys(i)
