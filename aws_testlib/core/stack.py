import contextlib
import dataclasses
import os.path
import random
import shutil
from abc import ABC
from typing import Literal, Optional, Callable

import boto3

from aws_testlib.core.introspection import get_sam_project_info
from aws_testlib.core.process import run_cmd

DeploymentType = Literal["aws-sam-build"]


def _void_finalizer(_):
    pass


@dataclasses.dataclass(
    frozen=True,
    eq=True,
    order=False,
)
class StackConfig:
    template_file_name: str = "template.yaml"
    deploy_template_file_name: str = "template.yaml"
    deploy_capabilities: list[str] = dataclasses.field(
        default_factory=lambda: ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"],
    )
    build_dir: str = os.path.join(".aws", "build")
    autoname: bool = True
    naming_strategy: Literal["rand"] = "rand"
    deploy_additional_args: list[str] = dataclasses.field(default_factory=list)
    deploy_wait_time: int = 300
    deploy_env_vars: dict[str, str] = dataclasses.field(default_factory=dict)


class StackContext:
    def __init__(self, add_finalizer: Callable = None):
        self._add_finalizer = add_finalizer

    def add_finalizer(self, finalizer: Callable):
        if self._add_finalizer is not None:
            self._add_finalizer(finalizer)


class Stack(ABC):
    def __init__(
        self,
        config: StackConfig = StackConfig(),
        context: StackContext = None,
        name: Optional[str] = None,
    ):
        self._config: StackConfig = config
        self._name: str = name
        self._context: StackContext = context
        self._status: Literal[
            "new",
            "deploying",
            "deployed",
            "instrumented",
            "disposing",
            "disposed",
        ] = "new"

        sam_project_info = get_sam_project_info(template_file_name=self._config.template_file_name)
        self._sam_project_info = sam_project_info

        if self._name is None and self._config.autoname is True:
            match self._config.naming_strategy:
                case "rand":
                    rnd = random.randint(10000000, 99999999)
                    self._name = f"{sam_project_info.project_name}-{rnd}"

        if self._context is None:
            self._context = StackContext(add_finalizer=_void_finalizer)

        self._context.add_finalizer(self.dispose)

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> StackConfig:
        return self._config

    @contextlib.contextmanager
    def run_on_stack(
        self,
    ):
        self.initialize()
        yield self

    def initialize(self):
        match self._status:
            case "new":
                try:
                    self._status = "deploying"
                    self._deploy()
                    self._status = "deployed"
                    self._instrument()
                    self._status = "instrumented"
                except:  # noqa E722
                    self.dispose()
                    raise
            case "disposing":
                raise RuntimeError("Stack is disposing")
            case "disposed":
                raise RuntimeError("Stack is disposed")

    def dispose(self):
        self._status = "disposing"
        self._force_delete_stack()
        self._status = "disposed"

    # noinspection PyMethodMayBeStatic
    def create_boto_client(self, resource: str):
        return boto3.client(resource)

    # noinspection PyMethodMayBeStatic
    def create_boto_resource(self, resource: str):
        return boto3.resource(resource)

    def _deploy(
        self,
        deployment_type: DeploymentType = "aws-sam-build",
    ):
        match deployment_type:
            case "aws-sam-build":
                self._deploy_sam_build()

    def _deploy_sam_build(self):
        sam_executable = shutil.which("sam")
        if sam_executable is None:
            raise RuntimeError("AWS SAM CLI is not installed")

        template_file_path = os.path.join(
            self._sam_project_info.root_dir,
            self._config.build_dir,
            self._config.deploy_template_file_name,
        )

        stack_name = self._name

        run_cmd(
            [
                sam_executable,
                "deploy",
                "--template",
                template_file_path,
                "--stack-name",
                stack_name,
                "--capabilities",
                self._config.deploy_capabilities,
                *self._config.deploy_additional_args,
            ],
            exception_on_error=True,
            print_output=True,
            wait=True,
            wait_timeout=self._config.deploy_wait_time,
            env=self._config.deploy_env_vars,
            prompt="SAM >>",
            finalizer=self._context.add_finalizer,
        )

    def _instrument(self):
        pass

    def _force_delete_stack(self):
        cf = self.create_boto_client("cloudformation")
        s3 = self.create_boto_resource("s3")
        dynamodb = self.create_boto_client("dynamodb")

        try:
            stacks = cf.describe_stacks(StackName=self._name).get("Stacks", [])
        except cf.exceptions.ClientError as e:
            if "does not exist" in str(e):
                return
            raise

        stack = next(iter(stacks), None)
        if stack is None:
            return

        def empty_bucket(bucket_name: str):
            bucket = s3.Bucket(bucket_name)
            bucket.objects.all().delete()

        def remove_dynamodb_table_protection(table_name: str):
            try:
                dynamodb.update_table(
                    TableName=table_name,
                    BillingMode="PAY_PER_REQUEST",
                )
            except dynamodb.exceptions.ResourceInUseException:
                pass

        stack_resources = cf.list_stack_resources(StackName=self._name).get("StackResourceSummaries", [])
        for stack_resource in stack_resources:
            match stack_resource["ResourceType"]:
                case "AWS::S3::Bucket":
                    empty_bucket(bucket_name=stack_resource["PhysicalResourceId"])
                case "AWS::DynamoDB::Table":
                    remove_dynamodb_table_protection(table_name=stack_resource["PhysicalResourceId"])
                case _:
                    continue
