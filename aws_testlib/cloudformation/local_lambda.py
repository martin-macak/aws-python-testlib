import json
import os
from io import StringIO

import boto3
from botocore.response import StreamingBody


class LambdaContext:
    def __init__(self,
                 function_name: str,
                 ):
        self.function_name = function_name
        self.function_version = "1"
        self.invoked_function_arn = f"arn:aws:lambda:fake:123456789012:function:{function_name}"
        self.memory_limit_in_mb = "128"
        self.aws_request_id = "12345678-1234-1234-1234-123456789012"
        self.log_group_name = "/aws/lambda/test-echo"
        self.log_stream_name = "2021/07/31/[$LATEST]12345678901234567890123456789012"
        self.identity = None
        self.client_context = None

    # noinspection PyMethodMayBeStatic
    def get_remaining_time_in_millis(self):
        return 10000


def mock_invoke_local_lambda(**kwargs):
    lambda_client = boto3.client('lambda')

    function_arn = kwargs["FunctionName"]
    function_name = function_arn.split(":")[-1]
    invocation_type = kwargs["InvocationType"]
    payload = kwargs["Payload"]

    try:
        f_def = lambda_client.get_function(FunctionName=function_name)
    except lambda_client.exceptions.ResourceNotFoundException:
        return {
            "StatusCode": 404,
            "FunctionError": "Function not found",
        }

    template_file_name = f_def.get("Tags", {}).get("testlib:template_file_name")
    code_uri = f_def.get("Tags", {}).get("testlib:lambda:code-uri")
    code_folder_name, handler_uri = code_uri.split(":")
    handler_module, handler_func_name = handler_uri.split(".")

    base_dir = os.path.dirname(template_file_name)
    code_dir = os.path.join(base_dir, code_folder_name)

    import importlib.util
    import sys

    data = json.loads(payload) if payload is not None else None

    if code_dir not in sys.path:
        sys_path_altered = True
        sys.path.append(code_dir)
    else:
        sys_path_altered = False

    # check if already imported (how???)
    # and call already imported module so mocks are still properly applied

    try:
        imported = importlib.import_module(handler_module)
        handler_func = getattr(imported, handler_func_name)

        if handler_func is None:
            raise ValueError(f"handler_func is None: {handler_uri}")

        handler_result = handler_func(
            event=data,
            context=LambdaContext(function_name=function_name),
        )

        result_dump = json.dumps(handler_result)
        return {
            "StatusCode": 200,
            "Payload": StreamingBody(StringIO(result_dump), len(result_dump)),
        }
    finally:
        if sys_path_altered:
            sys.path.remove(code_dir)
