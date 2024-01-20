from typing import Optional

import yaml


def load_cloudformation_template(
    template_file_name: str = "template.yaml",
    base_dir: Optional[str] = None,
) -> dict:
    from aws_testlib.pytest.fixtures.cloudformation.cfn_yaml_tags import CFLoader

    template_file_name, ok = find_template_file(template_file_name, base_dir)
    if not ok:
        raise FileNotFoundError(template_file_name)

    with open(template_file_name, mode="r") as f:
        template = yaml.load(f, Loader=CFLoader)
        return template


def find_template_file(
    template_file_name: str,
    base_dir: Optional[str] = None,
) -> tuple[Optional[str], bool]:
    import os
    import pathlib

    if base_dir is None:
        base_dir = os.getcwd()

    template_file_path = pathlib.Path(base_dir).joinpath(template_file_name)

    if template_file_path.exists():
        return os.path.abspath(str(template_file_path)), True

    if not os.path.dirname(base_dir) == base_dir:
        return find_template_file(template_file_name, os.path.dirname(base_dir))

    return None, False


def deploy_template(
    template_file_name: str = "template.yaml",
    base_dir: Optional[str] = None,
    parameter_overrides: dict = None,
):
    template_file, ok = find_template_file(template_file_name, base_dir)
    if not ok:
        raise FileNotFoundError(template_file_name)

    with open(template_file, mode="r") as f:
        template_raw = f.read()

    from aws_testlib.pytest.fixtures.cloudformation.cfn_yaml_tags import CFLoader, CFTransformer
    original_template = yaml.load(template_raw, Loader=CFLoader)
    pruned_template = _prune_template(original_template)
    pruned_template_raw = yaml.dump(pruned_template, Dumper=CFTransformer)

    import boto3
    cfn = boto3.client('cloudformation')
    cfn.create_stack(
        StackName="test-stack-1",
        TemplateBody=pruned_template_raw,
        Parameters=[
            {
                "ParameterKey": key,
                "ParameterValue": value,
            }
            for key, value in parameter_overrides.items()
        ] if parameter_overrides else [],
    )


def _prune_template(template: dict) -> dict:
    pruned_template = template.copy()
    pruned_template.pop("Metadata", None)
    pruned_template.pop("Description", None)

    for resource_name, resource_def in pruned_template.get("Resources", {}).items():
        resource_type = resource_def.get("Type")
        if resource_type not in [
            "AWS::DynamoDB::Table",
        ]:
            pruned_template.pop(resource_name, None)

    return pruned_template
