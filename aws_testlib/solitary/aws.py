from typing import Optional

import pytest
from pytest import StashKey

from aws_testlib.core.stack import Stack, StackConfig, StackContext

STASH_KEY_AWS_SOLITARY_STACK = StashKey[Stack]()


class AWSSolitaryStack(Stack):
    def __init__(
        self,
        name: Optional[str] = None,
        config: StackConfig = StackConfig(),
        context=None,
    ):
        super().__init__(
            name=name,
            config=config,
            context=context,
        )

    def _instrument(self):
        super()._instrument()


@pytest.fixture(autouse=False)
def aws_solitary_stack(
    request,
):
    return fixture_aws_solitary_stack(request)


def fixture_aws_solitary_stack(request: pytest.FixtureRequest):
    session = request.session
    stack = session.stash.get(STASH_KEY_AWS_SOLITARY_STACK, None)
    if stack is not None:
        return stack

    def add_finalizer(finalizer):
        request.addfinalizer(finalizer)

    stack = AWSSolitaryStack(
        context=StackContext(
            add_finalizer=add_finalizer,
        )
    )
    session.stash[STASH_KEY_AWS_SOLITARY_STACK] = stack
    yield stack
