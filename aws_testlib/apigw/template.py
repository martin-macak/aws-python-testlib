import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def evaluate(template: str,
             data: dict = None,
             stage_variables: dict = None,
             ) -> str:
    from aws_testlib.apigw.airspeed.engine import Template
    t = Template(template)

    result = t.merge(data)
    return result


def evaluate_aws(
    template: str,
    body: dict = None,
):
    from aws_testlib.apigw.airspeed.engine import Template
    t = Template(template)

    context = AWSApiGatewayContext(body=body)
    result = t.merge(context)
    return result


def _create_context(data: dict[str, Any] = None,
                    stage_variables: dict[str, Any] = None) -> dict[str, Any]:
    return _Context(data, stage_variables)


class _Context(dict):
    def __init__(self, data: dict[str, Any] = None, stage_variables: dict[str, Any] = None):
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


class AWSApiGatewayContext(dict):
    """

    References:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
    """

    class RequestInput(dict):
        def __init__(self,
                     body: dict = None,
                     ):
            super().__init__({
                "body": json.dumps(body),
                "json": lambda path: _eval_json_path(path, body),
            })

        # noinspection PyMethodMayBeStatic
        def _eval_json_path(self, obj: dict, path: str):
            return "pepa"

        def __getattribute__(self, item):
            if item.startswith("_"):
                return None

            return super().__getattribute__(item)

    def __init__(self,
                 body: dict = None, ):
        super().__init__({
            "input": AWSApiGatewayContext.RequestInput(body=body),
        })

    def __getattribute__(self, item):
        if item.startswith("_"):
            return None

        return super().__getattribute__(item)
