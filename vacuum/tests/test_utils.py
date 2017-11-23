import os
import tempfile
import time
import datetime
import mock

from ..utils import *

def test_pastdt():
    past = pastdt('10s')
    now = datetime.datetime.now()
    assert now-past > datetime.timedelta(seconds=10)
    assert now-past < datetime.timedelta(seconds=11)
    past = pastdt('1d')
    now = datetime.datetime.now()
    assert now-past > datetime.timedelta(days=1)
    assert now-past < datetime.timedelta(days=2)

@mock.patch('vacuum.utils.getmtime')
def test_older_then(getmtime):
    getmtime.return_value = (datetime.datetime.now()\
                            - datetime.timedelta(days=20)).timestamp()
    with tempfile.NamedTemporaryFile() as tmpfile:
        assert older_then(tmpfile.name, pastdt('15d'))
        assert not older_then(tmpfile.name, pastdt('21d'))


def test_flister_re():
    with tempfile.NamedTemporaryFile() as tmpfile:
        filename = os.path.basename(tmpfile.name)
        root = os.path.dirname(tmpfile.name)
        assert filename in list(flister(root, '.+'+filename[4:]))
        files = list(flister(root, filename))
        assert filename in files and len(files) == 1

@mock.patch('vacuum.utils.getmtime')
def test_flister_older_then(getmtime):
    getmtime.return_value = (datetime.datetime.now()\
                            - datetime.timedelta(days=4)).timestamp()

    with tempfile.NamedTemporaryFile() as tmpfile:
        filename = os.path.basename(tmpfile.name)
        root = os.path.dirname(tmpfile.name)
        assert len(list(flister(root, filename, older='2d'))) == 1
        assert len(list(flister(root, filename, older='10d'))) == 0
