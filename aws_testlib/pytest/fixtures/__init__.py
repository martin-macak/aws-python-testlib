import pytest


@pytest.fixture(autouse=False)
def build_cf_stack():
    return 1
