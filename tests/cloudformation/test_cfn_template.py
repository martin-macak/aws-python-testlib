import logging
import os.path
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

__dir = os.path.abspath(os.path.dirname(__file__))


@pytest.mark.parametrize(
    "depth",
    [i for i in range(10)],
)
def test_find_template_file(depth, monkeypatch, ):
    temp_dir = tempfile.mkdtemp()
    template_file = 'template.yaml'
    work_dir = os.path.join(temp_dir, *[str(i) for i in range(10)])
    os.makedirs(work_dir, exist_ok=False)
    logger.debug(f"work_dir: {work_dir}")
    template_dir = os.path.join(temp_dir, *[str(i) for i in range(depth)])
    template_file = os.path.join(template_dir, template_file)
    logger.debug(f"template_file: {template_file}")
    Path(template_file).touch()

    @contextmanager
    def dir_scope():
        monkeypatch.chdir(work_dir)
        yield

    with dir_scope():
        from aws_testlib.cloudformation.cfn_template import find_template_file
        logger.debug(f"searching for {template_file} in work_dir: {work_dir}")
        template_file_path, ok = find_template_file(template_file)
        logger.debug(f"found template_file_path: {template_file_path}")
        assert ok

        abspath = os.path.abspath(os.path.join(work_dir, template_file))
        assert template_file_path.removeprefix("/private") == abspath.removeprefix("/private")


def test_load_cloudformation_template():
    from aws_testlib.cloudformation.cfn_template import load_cloudformation_template
    template = load_cloudformation_template(base_dir=__dir)

    assert template is not None
