import json
import logging
import os
import time
import uuid
from typing import Any, Optional

import shortuuid

logger = logging.getLogger(__name__)


def evaluate(template: str,
             data: Optional[dict[str, Any]] = None,
             ) -> str:
    from aws_testlib.apigw.airspeed.engine import Template
    t = Template(template)

    result = t.merge(data)
    return result


def evaluate_aws(
    template: str,
    body: dict = None,
    request_parameters: Optional[dict[str, Any]] = None,
    context: Optional[dict[str, Any]] = None,
    stage_variables: Optional[dict[str, Any]] = None,
):
    from aws_testlib.apigw.airspeed.engine import Template
    t = Template(template)

    context = AWSApiGatewayContext(
        request_parameters=request_parameters,
        body=body,
        stage_variables=stage_variables,
        context=context,
    )

    result = t.merge(context)
    return result


def _create_context(
    data: Optional[dict[str, Any]] = None,
    stage_variables: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return _Context(data, stage_variables)


class _Context(dict):
    def __init__(
        self,
        data: dict[str, Any] = None,
        stage_variables: dict[str, Any] = None,
    ):
        super().__init__()
        self.update(data or {})
        self.update(stage_variables or {})


def _eval_json_path(
    path: str,
    obj: dict,
):
    from jsonpath_ng import parse
    # noinspection PyBroadException
    try:
        jp = parse(path)
    except:  # noqa: E722
        return None

    found = jp.find(obj)
    if found is None or len(found) == 0:
        return None

    matching = found[0].value
    return matching


def _eval_request_params(
    request_parameters: dict,
    arg_name: Optional[str] = None
):
    if arg_name is None:
        return request_parameters
    else:
        return request_parameters.get(arg_name)


class AWSApiGatewayUtil:
    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def escapeJavaScript(self, val):
        return str(val or "").replace("'", "\\'")

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def parseJson(self, val):
        return json.loads(str(val or ""))

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def urlEncode(self, val):
        from urllib.parse import quote
        return quote(val or "")

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def urlDecode(self, val):
        from urllib.parse import unquote
        return unquote(val or "")

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def base64Encode(self, val):
        from base64 import urlsafe_b64encode
        return urlsafe_b64encode(val or "")

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def base64Decode(self, val):
        from base64 import urlsafe_b64decode
        return urlsafe_b64decode(val or "")


class AWSApiGatewayContext(dict):
    """

    References:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
    """

    class RequestInput(dict):

        def __init__(self,
                     body: dict = None,
                     request_parameters: dict = None,
                     ):
            super().__init__({
                "body": json.dumps(body),
                "json": lambda path: json.dumps(_eval_json_path(path, body)),
                "path": lambda path: _eval_json_path(path, body),
                "params": lambda *args: _eval_request_params(request_parameters, args[0] if len(args) == 1 else args),
            })

        def __getattribute__(self, item):
            if item.startswith("_"):
                return None

            return super().__getattribute__(item)

    def __init__(self,
                 request_parameters: Optional[dict[str, Any]] = None,
                 body: Optional[dict[str, Any]] = None,
                 stage_variables: Optional[dict[str, Any]] = None,
                 context: Optional[dict[str, Any]] = None,
                 ):
        super().__init__({
            "input": AWSApiGatewayContext.RequestInput(
                request_parameters=request_parameters,
                body=body
            ),
            "util": AWSApiGatewayUtil(),
            "stageVariables": stage_variables or {},
            "context": context or _create_default_context(),
        })

    def __getattribute__(self, item):
        if item.startswith("_"):
            return None

        return super().__getattribute__(item)


def _create_default_context() -> dict[str, Any]:
    request_id = str(uuid.uuid4())
    account_id = (
        os.environ.get("AWS_ACCOUNT_ID")
        or os.environ.get("MOTO_ACCOUNT_ID")
        or "123456789012"
    )

    return {
        "accountId": account_id,
        "apiId": str(shortuuid.random()),
        "authorizer": {
            "principalId": "user",
        },
        "awsEndpointRequestId": "aws",
        "domainName": "domain",
        "domainPrefix": "domainPrefix",
        "extendedRequestId": request_id,
        "httpMethod": "GET",
        "path": "/",
        "protocol": "https",
        "requestId": request_id,
        "requestTime": "01/01/2024:00:00:00",
        "requestTimeEpoch": round(time.time()),
        "resourceId": "resource",
        "resourcePath": "/",
        "stage": "Default",
    }
