import os
import tempfile
import time
import datetime
import mock
import pytest
import shutil
import stat

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
        assert tmpfile.name in list(flister(root, '.+'+filename[4:]))
        files = list(flister(root, filename))
        assert tmpfile.name in files and len(files) == 1

def test_flister_recursive():
    tmpdir1 = tempfile.mkdtemp()
    tmpdir2 = tempfile.mkdtemp(dir=tmpdir1)
    tmpdir3 = tempfile.mkdtemp(dir=tmpdir2)
    
    with tempfile.NamedTemporaryFile(prefix='xyz', dir=tmpdir1) as tmpfile1:
        with tempfile.NamedTemporaryFile(prefix='xyz',dir=tmpdir2) as tmpfile2:
            with tempfile.NamedTemporaryFile(prefix='xyz',dir=tmpdir3) as tmpfile3:
                filelist = list(flister(tmpdir1, 'xyz', recursive=True))
    assert len(filelist) == 3

def test_flister_default():
    assert list(flister(os.path.dirname(__file__)))
    assert not list(flister('/nonexistent'))

@mock.patch('vacuum.utils.getmtime')
def test_flister_older_then(getmtime):
    getmtime.return_value = (datetime.datetime.now()\
                            - datetime.timedelta(days=4)).timestamp()

    with tempfile.NamedTemporaryFile() as tmpfile:
        filename = os.path.basename(tmpfile.name)
        root = os.path.dirname(tmpfile.name)
        assert len(list(flister(root, filename, older='2d'))) == 1
        assert len(list(flister(root, filename, older='10d'))) == 0

def test_delete_file():
    tmpfile = tempfile.NamedTemporaryFile()
    assert os.path.exists(tmpfile.name)
    delete([tmpfile.name])
    assert not os.path.exists(tmpfile.name)

def test_delete_dir():
    tmpdir = tempfile.mkdtemp()
    assert os.path.isdir(tmpdir)
    delete([tmpdir])
    assert not os.path.isdir(tmpdir)

@mock.patch('shutil.rmtree')
def test_delete_error(rmtree):
    tmpdir = tempfile.mkdtemp()
    rmtree.side_effect = OSError('Some OS Error')
    with pytest.raises(Exception) as e_info:
        delete([tmpdir], raise_errors=True)
    os.removedirs(tmpdir)
    assert not os.path.isdir(tmpdir)

@mock.patch('shutil.rmtree')
def test_delete_error_print(rmtree):
    tmpdir = tempfile.mkdtemp()
    rmtree.side_effect = OSError('Some OS Error')
    delete([tmpdir], raise_errors=False)
    assert os.path.isdir(tmpdir)
    os.removedirs(tmpdir)
    assert not os.path.isdir(tmpdir)