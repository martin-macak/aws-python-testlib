import logging
from typing import Any

logger = logging.getLogger(__name__)


def evaluate(template: str,
             data: dict = None,
             stage_variables: dict = None) -> str:
    from aws_testlib.apigw.airspeed.engine import Template
    t = Template(template)

    result = t.merge(data)
    return result


def _create_context(data: dict[str, Any] = None,
                    stage_variables: dict[str, Any] = None) -> dict[str, Any]:
    return _Context(data, stage_variables)


class _Context(dict):
    def __init__(self, data: dict[str, Any] = None, stage_variables: dict[str, Any] = None):
        super().__init__()
        self.update(data or {})
        self.update(stage_variables or {})
