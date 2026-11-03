import pytest

from incidentdesk.cli import main


def test_version_prints_package_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "incidentdesk 1.4.0\n"
