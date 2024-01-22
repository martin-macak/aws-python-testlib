import json
import logging
import random
import uuid
from typing import Any, Optional

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


class AWSApiGatewayContext:
    """

    References:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
    """

    class RequestContext:
        def __init__(self,
                     account_id: Optional[str] = None,
                     api_id: Optional[str] = None,
                     authorizer_claims: Optional[dict[str, Any]] = None,
                     authorizer_principal_id: Optional[str] = None,
                     authorizer_additional_properties: Optional[dict[str, Any]] = None,
                     domain_name: Optional[str] = None,
                     domain_prefix: Optional[str] = None,
                     http_method: Optional[str] = None,
                     identity_account_id: Optional[str] = None,
                     identity_api_key: Optional[str] = None,
                     identity_api_key_id: Optional[str] = None,
                     identity_caller: Optional[str] = None,
                     identity_cognito_authentication_provider: Optional[str] = None,
                     identity_cognito_authentication_type: Optional[str] = None,
                     identity_cognito_identity_id: Optional[str] = None,
                     identity_cognito_identity_pool_id: Optional[str] = None,
                     identity_principal_org_id: Optional[str] = None,
                     identity_source_ip: Optional[str] = None,
                     identity_user: Optional[str] = None,
                     path: Optional[str] = None,
                     protocol: Optional[str] = None,
                     ):
            from aws_testlib.common.aws_context import get_context
            default_context = get_context()

            self.account_id = account_id or default_context.aws_account_id
            self.api_id = api_id or f"api{random.randint(10000000, 99999999)}"
            self.requestId = str(uuid.uuid4())
            self.extendedRequestId = self.requestId
            self.authorizer = {
                "claims": authorizer_claims or {},
                "principalId": authorizer_principal_id or str(uuid.uuid4()),
                **(authorizer_additional_properties or {}),
            }
            self.identity = {
                "accountId": identity_account_id or self.account_id,
                "apiKey": identity_api_key or str(uuid.uuid4()),
                "apiKeyId": identity_api_key_id or str(uuid.uuid4()),
                "caller": identity_caller or "123456789012",
                "cognitoAuthenticationProvider": identity_cognito_authentication_provider or None,
                "cognitoAuthenticationType": identity_cognito_authentication_type or None,
                "cognitoIdentityId": identity_cognito_identity_id or str(uuid.uuid4()),
                "cognitoIdentityPoolId": identity_cognito_identity_pool_id or str(uuid.uuid4()),
                "principalOrgId": identity_principal_org_id or None,
                "sourceIp": identity_source_ip or "192.168.1.1",
            }
            self.domainName = domain_name or f"api.{default_context.aws_region_name}.amazonaws.com"
            self.domainPrefix = domain_prefix or "api"
            self.httpMethod = http_method or "GET"

    class RequestInput:
        def __init__(self,
                     body: dict = None):
            self._body = body

        @property
        def body(self):
            return json.dumps(super().__getattribute__("_body"))

        def json(self, path: str):
            from jsonpath_ng import parse
            # noinspection PyBroadException
            try:
                jp = parse(path)
            except:
                return None

            data = json.loads(self.body)
            if data is None:
                return None

            found = jp.find(data)
            if len(found) == 0:
                return None

            matching = found[0].value
            return matching

        def __getattribute__(self, item):
            if item.startswith("_"):
                return None

            return super().__getattribute__(item)

    def __init__(self,
                 body: Optional[dict] = None,
                 account_id: Optional[str] = None,
                 api_id: Optional[str] = None,
                 authorizer_claims: Optional[dict[str, Any]] = None,
                 authorizer_principal_id: Optional[str] = None,
                 authorizer_additional_properties: Optional[dict[str, Any]] = None,
                 domain_name: Optional[str] = None,
                 domain_prefix: Optional[str] = None,
                 http_method: Optional[str] = None,
                 identity_account_id: Optional[str] = None,
                 identity_api_key: Optional[str] = None,
                 identity_api_key_id: Optional[str] = None,
                 identity_caller: Optional[str] = None,
                 identity_cognito_authentication_provider: Optional[str] = None,
                 identity_cognito_authentication_type: Optional[str] = None,
                 identity_cognito_identity_id: Optional[str] = None,
                 identity_cognito_identity_pool_id: Optional[str] = None,
                 identity_principal_org_id: Optional[str] = None,
                 identity_source_ip: Optional[str] = None,
                 ):
        self._request_context = AWSApiGatewayContext.RequestContext(
            account_id=account_id,
            api_id=api_id,
            authorizer_claims=authorizer_claims,
            authorizer_principal_id=authorizer_principal_id,
            authorizer_additional_properties=authorizer_additional_properties,
            domain_name=domain_name,
            domain_prefix=domain_prefix,
            http_method=http_method,
            identity_api_key_id=identity_api_key_id,
            identity_account_id=identity_account_id,
            identity_api_key=identity_api_key,
            identity_caller=identity_caller,
            identity_cognito_authentication_provider=identity_cognito_authentication_provider,
            identity_cognito_authentication_type=identity_cognito_authentication_type,
            identity_cognito_identity_id=identity_cognito_identity_id,
            identity_cognito_identity_pool_id=identity_cognito_identity_pool_id,
            identity_principal_org_id=identity_principal_org_id,
            identity_source_ip=identity_source_ip,
        )

        self._request_input = AWSApiGatewayContext.RequestInput(body=body)

    @property
    def context(self):
        return super().__getattribute__("_request_context")

    @property
    def input(self):
        return super().__getattribute__("_request_input")

    def __getattribute__(self, item):
        if item.startswith("_"):
            return None

        return super().__getattribute__(item)
