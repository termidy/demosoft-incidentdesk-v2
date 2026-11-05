import pytest

from incidentdesk import __version__
from incidentdesk.cli import main


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out == f"incidentdesk {__version__}\n"
