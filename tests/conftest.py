import logging
import os
from tempfile import TemporaryDirectory

import pytest

log = logging.getLogger(__name__)


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    pass


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    pass


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    pass


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    pass


@pytest.fixture(autouse=False)
def sam_project():
    class Project:
        def __init__(self):
            self._cur_dir = None
            self._project_dir = None

        def __enter__(self):
            self._cur_dir = os.getcwd()
            self._project_dir = TemporaryDirectory()
            os.chdir(self._project_dir.name)
            log.debug(f"Changed directory to {self._project_dir.name}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            os.chdir(self._cur_dir)
            log.debug(f"Changed directory back to {self._cur_dir}")
            self._project_dir.cleanup()

        @property
        def cur_dir(self) -> str:
            return self._cur_dir

        @property
        def project_dir(self) -> str:
            return self._project_dir.name

        def write_sam_template(
            self,
            content: str,
            template_file_name: str = "template.yaml",
        ):
            with open(f"{self._project_dir.name}/{template_file_name}", "w") as f:
                f.write(content)
                f.flush()

    with Project() as project:
        project.write_sam_template("AWSTemplateFormatVersion: '2010-09-09'\n")
        yield project
        pass
