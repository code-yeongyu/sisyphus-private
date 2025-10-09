import pytest

from sisyphus.main import print_hello_world

pytestmark = [pytest.mark.anyio]


def test_print_hello_world(capsys: pytest.CaptureFixture[str]) -> None:
    # given
    expected_output = "Hello, World!\n"

    # when
    print_hello_world()

    # then
    captured = capsys.readouterr()
    assert captured.out == expected_output
