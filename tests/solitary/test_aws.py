def test_solitary_stack(
    monkeypatch,
    mocker,
    sam_project,
):
    mocker.patch("aws_testlib.core.process.run_cmd", autospec=True)

    from aws_testlib.solitary.aws import AWSSolitaryStack

    stack = AWSSolitaryStack()
    with stack.run_on_stack():
        pass

    from aws_testlib.core.process import run_cmd

    # noinspection PyUnresolvedReferences
    run_cmd.assert_called_once()


def test_fixture_aws_solitary_stack(
    request,
    sam_project,
    monkeypatch,
    mocker,
):
    mocker.patch("aws_testlib.core.process.run_cmd", autospec=True)

    from aws_testlib.solitary.aws import fixture_aws_solitary_stack

    gen = fixture_aws_solitary_stack(request)
    stack = next(gen)

    with stack.run_on_stack():
        pass
