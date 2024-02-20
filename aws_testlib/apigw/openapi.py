import io
import json
from contextlib import contextmanager
from typing import Optional

import yaml

from aws_testlib.apigw.template import evaluate_aws


@contextmanager
def rest_api(src):
    match src:
        case io.TextIOBase():
            openapi_spec = src.read()
        case str():
            openapi_spec = src
        case _:
            raise ValueError("value type is not supported")

    try:
        openapi = yaml.safe_load(openapi_spec)
    except yaml.YAMLError as e:
        openapi = json.loads(openapi_spec)

    yield RestApiContext(openapi)


class RestApiContext:
    def __init__(self, spec: dict):
        self._spec = spec
        self._operations = {
            None if method_def.get("operationId") is None else method_def["operationId"]: method_def
            for path, path_spec in spec["paths"].items()
            for method, method_def in path_spec.items() if method.lower() in ["get", "post", "put", "delete"]
        }

    class IntegrationContext:
        def __init__(
            self,
            spec: dict,
        ):
            self._spec = spec

        def evaluate_request(
            self,
            mime_type: Optional[str] = None,
            body: Optional[dict] = None,
            stage_variables: Optional[dict] = None,
            request_parameters: Optional[dict] = None,
            context: Optional[dict] = None,
        ) -> dict | str:
            request_templates = self._spec["x-amazon-apigateway-integration"]["requestTemplates"]
            if mime_type is None:
                keys = list(request_templates.keys())
                mime_type = keys[0]

            template = request_templates[mime_type]
            return self._evaluate_template(
                template=template,
                mime_type=mime_type,
                body=body,
                stage_variables=stage_variables,
                request_parameters=request_parameters,
                context=context,
            )

        def evaluate_response(
            self,
            response_mapping: Optional[str] = None,
            mime_type: Optional[str] = None,
            body: Optional[dict] = None,
            stage_variables: Optional[dict] = None,
            request_parameters: Optional[dict] = None,
            context: Optional[dict] = None,
        ):
            responses = self._spec["x-amazon-apigateway-integration"]["responses"]
            response_keys = list(responses.keys())
            if response_mapping is None:
                response_mapping = response_keys[0]
            response = responses[response_mapping]
            response_templates = response["responseTemplates"]
            if mime_type is None:
                keys = list(response_templates.keys())
                mime_type = keys[0]

            template = response_templates[mime_type]
            return self._evaluate_template(
                template=template,
                mime_type=mime_type,
                body=body,
                stage_variables=stage_variables,
                request_parameters=request_parameters,
                context=context,
            )

        @staticmethod
        def _evaluate_template(
            template: str,
            mime_type: str,
            body: Optional[dict] = None,
            stage_variables: Optional[dict] = None,
            request_parameters: Optional[dict] = None,
            context: Optional[dict] = None,
        ) -> dict | str:
            evaluated = evaluate_aws(
                template=template,
                body=body,
                request_parameters=request_parameters,
                context=context,
                stage_variables=stage_variables,
            )

            match mime_type:
                case "application/json":
                    return json.loads(evaluated)
                case _:
                    return evaluated

    def with_operation(self, operation_id: str) -> IntegrationContext:
        spec = self._operations.get(operation_id)
        if spec is None:
            raise ValueError(f"operation_id '{operation_id}' not found in spec")

        return RestApiContext.IntegrationContext(spec)
