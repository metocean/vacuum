import os
from os.path import *
import mock
import tempfile
import shutil
import datetime
import pytest
import unittest

from ..command import parser
from ..utils import timestamp

def test_list_command_with_pattern():
    args = parser.parse_args(['list','/var/log','-p','.+\.log'])
    files = args.func(args)
    assert files

@mock.patch('vacuum.utils.getmtime')
def test_list_older_than(getmtime):
    getmtime.return_value = timestamp(datetime.datetime.now()\
                            - datetime.timedelta(days=11))
    with tempfile.NamedTemporaryFile() as tmpfile:
        fname = basename(tmpfile.name)
        args = parser.parse_args(['list', tempfile.gettempdir(),
                                  '-p',fname,'-o','10d',])
        found = args.func(args) 
        assert found
        args = parser.parse_args(['list', tempfile.gettempdir(),
                                  '-p',fname,'-o','12d',])
        found = args.func(args) 
        assert not found

class CleanFilesTestCase(unittest.TestCase):
    def setUp(self):
        self.rootdir = tempfile.mkdtemp()

    def tearDown(self):
        if exists(self.rootdir): 
            shutil.rmtree(self.rootdir)

    def test_clean_files_with_pattern(self):
        files = []
        for i in range(5):
            tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir,
                                                  suffix='test_clean')
            tmpfile.file.close()
            files.append(tmpfile.name)
            assert exists(tmpfile.name)
        args = parser.parse_args(['clean',self.rootdir,'-f','-p','test_clean',])
        args.func(args)
        assert not all([exists(f) for f in files])

    @mock.patch('os.remove', side_effect=OSError('Not permitted'))
    def test_clean_files_with_errors(self, remove):
        files = []
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir,
                                              suffix='test_clean')
        tmpfile.file.close()

        files.append(tmpfile.name)
        args = parser.parse_args(['clean',self.rootdir,'-f'])
        args.func(args)
        assert all([exists(f) for f in files])

    def test_clean_remove_empty(self):
        files = []
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir,
                                              suffix='test_clean')
        tmpfile.file.close()
        files.append(tmpfile.name)
        args = parser.parse_args(['clean',self.rootdir,'-fe'])
        args.func(args)
        assert not exists(self.rootdir)

class ArchiveFilesTestCase(unittest.TestCase):
    def setUp(self):
        self.rootdir = tempfile.mkdtemp()
        self.destination = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.rootdir)
        shutil.rmtree(self.destination)

    def test_archive_copy(self):
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir, suffix='test_archive', 
                                              delete=False)
        tmpfile.close()
        args = parser.parse_args(['archive', '-f', self.rootdir, self.destination])
        args.func(args)
        assert os.listdir(self.rootdir)
        assert os.listdir(self.destination)

    def test_archive_move(self):
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir, suffix='test_archive', 
                                              delete=False)
        tmpfile.close()
        args = parser.parse_args(['archive','-a','move','-f', self.rootdir, self.destination])
        args.func(args)
        assert not os.listdir(self.rootdir)
        assert os.listdir(self.destination)

    def test_archive_links_as_links(self):
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir, suffix='test_archive', 
                                              delete=False)
        tmpfile.close()
        os.symlink(basename(tmpfile.name), tmpfile.name+'.link')
        args = parser.parse_args(['archive','-f', self.rootdir, self.destination])
        args.func(args)
        assert os.listdir(self.destination)
        dst = join(self.destination, basename(tmpfile.name))
        assert islink(dst+'.link')
        assert os.readlink(dst+'.link') == basename(tmpfile.name)
        assert isfile(dst)
        


