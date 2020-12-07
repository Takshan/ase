import pytest
from ase.utils import xwopen


poem = 'Wer reitet so spät durch Nacht und Wind\n'.encode('utf-8')
filename = 'poem.txt'


def test_xwopen():
    with xwopen(filename) as fd:
        fd.write(poem)

    assert fd.closed

    with open(filename, 'rb') as fd:
        assert fd.read() == poem


def test_xwopen_locked():
    with xwopen(filename) as fd:
        with xwopen(filename) as fd2:
            assert fd2 is None


def test_xwopen_fail(tmp_path):
    with pytest.raises(OSError):
        with xwopen(tmp_path / 'does_not_exist/file') as fd:
            pass
