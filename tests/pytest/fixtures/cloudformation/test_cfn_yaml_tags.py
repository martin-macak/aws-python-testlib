import yaml


def test_loader():
    from aws_testlib.pytest.fixtures.cloudformation.cfn_yaml_tags import CFLoader

    got = yaml.load(
        # language=yaml
        """
    Resources:
        MyBucket:
            Type: AWS::S3::Bucket
            Properties:
                BucketName: !Ref BucketName
                AccessControl: !FindInMap [ Env, !Ref EnvName, !Ref PropName ]
                WebsiteConfiguration:
                    IndexDocument: !GetAtt IndexDocument.Arn
        """,
        Loader=CFLoader,
    )

    assert got is not None

