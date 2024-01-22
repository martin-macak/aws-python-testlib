import dataclasses
import os

DEFAULT_AWS_ACCOUNT_ID = "123456789012"


@dataclasses.dataclass
class Context:
    aws_account_id: str
    aws_region_name: str


def get_context() -> Context:
    aws_account_id = os.environ.get("MOTO_ACCOUNT_ID", DEFAULT_AWS_ACCOUNT_ID)
    aws_region_name = "fake"

    return Context(
        aws_account_id="123456789012",
        aws_region_name="us-east-1",
    )
