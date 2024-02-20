import os

_dir = os.path.dirname(os.path.realpath(__file__))


def test_rest_api():
    api_file = os.path.abspath(os.path.join(_dir, "..", "test.openapi.yaml"))
    from aws_testlib.apigw.openapi import rest_api
    with open(api_file, "r") as f:
        with rest_api(f) as api:
            assert api._spec is not None

            got = (
                api
                .with_operation("GetExistingSCIMTokenStatus")
                .evaluate_request(
                    request_parameters={
                        "accountId": "acc1",
                    },
                )
            )

            print(got)

            got = (
                api
                .with_operation("GetExistingSCIMTokenStatus")
                .evaluate_response(
                    body={
                        "TokenStatus": "ACTIVE",
                    },
                )
            )

            print(got)
