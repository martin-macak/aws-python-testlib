from contextlib import contextmanager
from typing import Optional
from unittest.mock import patch

import yaml

from aws_testlib.cloudformation.builder import SupportedComponents
from aws_testlib.cloudformation.stack import Stack


# def build_cfn_stack(template_name: Optional[str] = None,
#                     components: Optional[list[SupportedComponents]] = None,
#                     mock_lambda_with_local_packaged: bool = False,
#                     ):
#     from aws_testlib.cloudformation.cfn_template import find_template_file, transform_template_str
#     from aws_testlib.cloudformation.builder import deploy_template
#     from aws_testlib.cloudformation.local_lambda import mock_invoke_local_lambda
#
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             # from aws_testlib.cloudformation.cfn_template import deploy_template
#             template_file_name, ok = find_template_file(template_file_name=template_name)
#             if not ok:
#                 raise FileNotFoundError(template_file_name)
#
#             with open(template_file_name, mode="r") as f:
#                 template_raw = f.read()
#
#             transformed_template_raw = transform_template_str(template_raw=template_raw)
#             template = yaml.safe_load(transformed_template_raw)
#             deploy_template(
#                 template_file_name=template_file_name,
#                 template=template,
#                 deployed_components=components,
#             )
#
#             import botocore.client
#
#             # noinspection PyProtectedMember
#             orig = botocore.client.BaseClient._make_api_call
#
#             # noinspection PyShadowingNames
#             def mock_make_api_call(self, operation_name, kwargs):
#                 if operation_name == "Invoke" and mock_lambda_with_local_packaged:
#                     return mock_invoke_local_lambda(**kwargs)
#                 else:
#                     return orig(self, operation_name, kwargs)
#
#             with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
#                 func(*args, **kwargs)
#
#         return wrapper
#
#     return decorator

@contextmanager
def build_cfn_stack(template_name: Optional[str] = None,
                    components: Optional[list[SupportedComponents]] = None,
                    mock_lambda_with_local_packaged: bool = False,
                    ) -> Stack:
    from aws_testlib.cloudformation.cfn_template import find_template_file, transform_template_str
    from aws_testlib.cloudformation.builder import deploy_template
    from aws_testlib.cloudformation.local_lambda import mock_invoke_local_lambda

    stack = Stack()

    # from aws_testlib.cloudformation.cfn_template import deploy_template
    template_file_name, ok = find_template_file(template_file_name=template_name)
    if not ok:
        raise FileNotFoundError(template_file_name)

    with open(template_file_name, mode="r") as f:
        template_raw = f.read()

    transformed_template_raw = transform_template_str(template_raw=template_raw)
    template = yaml.safe_load(transformed_template_raw)
    deploy_template(
        stack=stack,
        template_file_name=template_file_name,
        template=template,
        deployed_components=components,
    )

    import botocore.client

    # noinspection PyProtectedMember
    orig = botocore.client.BaseClient._make_api_call

    # noinspection PyShadowingNames
    def mock_make_api_call(self, operation_name, kwargs):
        if operation_name == "Invoke" and mock_lambda_with_local_packaged:
            return mock_invoke_local_lambda(**kwargs)
        else:
            return orig(self, operation_name, kwargs)

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        yield stack
