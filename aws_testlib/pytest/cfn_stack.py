from typing import Optional

import yaml

from aws_testlib.cloudformation.builder import SupportedComponents


def build_cfn_stack(template_name: Optional[str] = None,
                    components: Optional[list[SupportedComponents]] = None,
                    ):
    from aws_testlib.cloudformation.cfn_template import find_template_file, transform_template_str
    from aws_testlib.cloudformation.builder import deploy_template

    def decorator(func):
        def wrapper(*args, **kwargs):
            # from aws_testlib.cloudformation.cfn_template import deploy_template
            template_file_name, ok = find_template_file(template_file_name=template_name)
            if not ok:
                raise FileNotFoundError(template_file_name)

            with open(template_file_name, mode="r") as f:
                template_raw = f.read()

            transformed_template_raw = transform_template_str(template_raw=template_raw)
            template = yaml.safe_load(transformed_template_raw)
            deploy_template(template=template, deployed_components=components)

            func(*args, **kwargs)

        return wrapper

    return decorator
