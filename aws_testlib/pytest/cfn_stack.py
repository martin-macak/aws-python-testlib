from typing import Optional


def build_cfn_stack(template_name: Optional[str] = None,):
    def decorator(func):
        def wrapper(*args, **kwargs):
            from aws_testlib.cloudformation.cfn_template import deploy_template
            deploy_template(template_file_name=template_name)
            func(*args, **kwargs)

        return wrapper

    return decorator
