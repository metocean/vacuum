import os
import tempfile
import time
import datetime
import mock
import pytest
import shutil
import stat
import six

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
    getmtime.return_value = timestamp(datetime.datetime.now()\
                            - datetime.timedelta(days=20))
    with tempfile.NamedTemporaryFile() as tmpfile:
        assert is_older_then(tmpfile.name, pastdt('15d'))
        assert not is_older_then(tmpfile.name, pastdt('21d'))

def test_flister_re():
    with tempfile.NamedTemporaryFile() as tmpfile:
        filename = os.path.basename(tmpfile.name)
        root = os.path.dirname(tmpfile.name)
        assert tmpfile.name in list(flister(root, '.+'+filename[4:]))
        files = list(flister(root, filename))
        assert tmpfile.name in files and len(files) == 1

def test_flister_links():
    tmpdir1 = tempfile.mkdtemp()
    with tempfile.NamedTemporaryFile(dir=tmpdir1) as tmpfile:
        tmpfilelnk = tmpfile.name+'.lnk'
        os.symlink(tmpfile.name, tmpfilelnk)
        brknlnk = tmpfile.name+'.broken'+'.lnk'
        os.symlink(tmpfile.name+'.broken', brknlnk)
        filelist = list(flister(tmpdir1))
    assert len(filelist) == 3
    shutil.rmtree(tmpdir1)

def test_flister_recursive():
    tmpdir1 = tempfile.mkdtemp()
    tmpdir2 = tempfile.mkdtemp(dir=tmpdir1)
    tmpdir3 = tempfile.mkdtemp(dir=tmpdir2)
    
    with tempfile.NamedTemporaryFile(prefix='xyz', dir=tmpdir1) as tmpfile1:
        with tempfile.NamedTemporaryFile(prefix='xyz',dir=tmpdir2) as tmpfile2:
            with tempfile.NamedTemporaryFile(prefix='xyz',dir=tmpdir3) as tmpfile3:
                filelist = list(flister(tmpdir1, 'xyz', recursive=True,max_depth=3))
    assert len(filelist) == 3

def test_flister_default():
    assert list(flister(os.path.dirname(__file__)))
    assert not list(flister('/nonexistent'))

def test_flister_empty_dirs():
    # check if flister yields a empty_dir, but not a non empty_one
    tmpdir1 = tempfile.mkdtemp()
    tmpdir11 = tempfile.mkdtemp(dir=tmpdir1)
    tmpdir12 = tempfile.mkdtemp(dir=tmpdir1)
    with tempfile.NamedTemporaryFile(prefix='xyz', dir=tmpdir12) as tmpfile1:
        assert len(list(flister(tmpdir1, 'abc', recursive=True, max_depth=3))) == 1

@mock.patch('vacuum.utils.getmtime')
def test_flister_older_then(getmtime):
    getmtime.return_value = timestamp(datetime.datetime.now()\
                            - datetime.timedelta(days=4))

    with tempfile.NamedTemporaryFile() as tmpfile:
        filename = os.path.basename(tmpfile.name)
        root = os.path.dirname(tmpfile.name)
        assert len(list(flister(root, filename, older_then='2d'))) == 1
        assert len(list(flister(root, filename, older_then='10d'))) == 0

@mock.patch('vacuum.utils.getmtime')
def test_flister_older_then_with_relative_time(getmtime):
    getmtime.return_value = timestamp(datetime.datetime.now()\
                            - datetime.timedelta(days=4))
    with tempfile.NamedTemporaryFile() as tmpfile:
        filename = os.path.basename(tmpfile.name)
        root = os.path.dirname(tmpfile.name)
        assert len(list(flister(root, filename, older_then='2d', 
                                now=datetime.datetime.now()))) == 1
        now = datetime.datetime.now()-datetime.timedelta(days=4)
        assert len(list(flister(root, filename, older_then='2d', now=now))) == 0

def test_delete_link():
    tmpfile = tempfile.NamedTemporaryFile()
    tmpfilelnk = tmpfile.name+'.lnk'
    os.symlink(tmpfile.name, tmpfilelnk)
    assert os.path.exists(tmpfile.name)
    assert os.path.islink(tmpfilelnk)
    delete([tmpfilelnk])
    assert not os.path.exists(tmpfilelnk)

def test_delete_broken_link():
    with tempfile.NamedTemporaryFile() as tmpfile:
        pass
    tmpfilelnk = tmpfile.name+'.link'
    os.symlink(tmpfile.name, tmpfilelnk)
    assert os.path.lexists(tmpfilelnk)
    assert os.path.islink(tmpfilelnk)
    assert not os.path.exists(tmpfilelnk)
    delete([tmpfilelnk])
    assert not os.path.lexists(tmpfilelnk)

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

def test_delete_empty_dir():
    tmpdir = tempfile.mkdtemp()
    _,tmpfile = tempfile.mkstemp(dir=tmpdir)
    delete([tmpfile], delete_empty=False)
    assert os.path.isdir(tmpdir)
    _,tmpfile = tempfile.mkstemp(dir=tmpdir)
    delete([tmpfile], delete_empty=True)
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


def test_datetime_from_filename_parser():
    example = '/data/wrf/gfs_nz8km/wrf20180114/nz_8km_06z.GrbF042'
    expected = datetime.datetime(2018,1,14,6)
    assert path2dt(example, date_strptime='%Y%m%d',time_strptime='%Hz') == expected

    example = '/data/ww3/gfs_glob-st4/ww320180112_18z/glob20180112T18.nc'
    expected = datetime.datetime(2018,1,12,18)
    assert path2dt(example, date_strptime='%Y%m%d_%Hz') == expected

    example = '/data/kd490/global/modisa20180113/A2018013.L3m_DAY_KD490_Kd_490_4km.nc'
    expected = datetime.datetime(2018,1,13,0)
    assert path2dt(example, date_strptime='%Y%m%d') == expected

def test_archive_simple():
    tmpdir = tempfile.mkdtemp()
    try:
        _, tmpfile = tempfile.mkstemp(dir=tmpdir)
        basename = os.path.basename(tmpfile)
        archive([tmpfile], tmpdir)
        assert os.path.exists(tmpfile)
        assert os.path.exists(os.path.join(tmpdir, basename))
    finally:
        shutil.rmtree(tmpdir)


def test_archive_preserve_root():
    tmpdir0 = tempfile.mkdtemp()
    tmpdir1 = tempfile.mkdtemp(dir=tmpdir0)
    tmpdir2 = tempfile.mkdtemp(dir=tmpdir1)
    tmpdir3 = tempfile.mkdtemp(dir=tmpdir2)

    dest = tempfile.mkdtemp()
    try:
        for root_depth in range(1,5):
            _, tmpfile = tempfile.mkstemp(dir=tmpdir3)
            archive([tmpfile], dest, root_depth=root_depth)
            basename = tmpfile.split(os.sep, root_depth+1)[-1]
            assert os.path.exists(os.path.join(dest, basename))
        root_depth = 5
        _, tmpfile = tempfile.mkstemp(dir=tmpdir3)
        archive([tmpfile], dest, root_depth=root_depth)
        basename = os.path.basename(tmpfile)
        assert os.path.exists(os.path.join(dest, basename))
    finally:
        shutil.rmtree(tmpdir0)
        shutil.rmtree(dest)