from typing import Optional

import yaml


def load_cloudformation_template(
    template_file_name: str = "template.yaml",
    base_dir: Optional[str] = None,
) -> dict:
    from aws_testlib.cloudformation.cfn_yaml_tags import CFLoader

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


def transform_template(template_file_name: str, ) -> str:
    with open(template_file_name, mode="r") as f:
        template_raw = f.read()

    return transform_template_str(template_raw)


def transform_template_str(template_raw: str) -> str:
    from aws_testlib.cloudformation.cfn_yaml_tags import CFLoader, CFTransformer
    original_template = yaml.load(template_raw, Loader=CFLoader)
    result = yaml.dump(original_template, Dumper=CFTransformer)
    return result


def _prune_template(template: dict) -> dict:
    pruned_template = template.copy()
    pruned_template.pop("Metadata", None)
    pruned_template.pop("Description", None)

    for resource_name, resource_def in pruned_template.get("Resources", {}).items():
        resource_type = resource_def.get("Type")
        if resource_type not in [
            "AWS::DynamoDB::Table",
            "AWS::SQS::Queue",
            "AWS::SNS::Topic",
            "AWS::SNS::Subscription",
            "AWS::Serverless::Function",
            "AWS::Lambda::Function",
        ]:
            pruned_template.pop(resource_name, None)

    return pruned_template
