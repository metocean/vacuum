from os.path import *
import mock
import tempfile
import shutil
import datetime

from ..command import execute, parser
from ..utils import timestamp

@mock.patch('vacuum.command.print_filelist')
def test_list_command_with_pattern(pflist):
    args = parser.parse_args(['-p','var','list','/'])
    execute(args)
    pflist.assert_called()

@mock.patch('vacuum.utils.getmtime')
def test_list_older_then(getmtime):
    getmtime.return_value = timestamp(datetime.datetime.now()\
                            - datetime.timedelta(days=11))
    with tempfile.NamedTemporaryFile() as tmpfile:
        fname = basename(tmpfile.name)
        args = parser.parse_args(['-p',fname,'-o','10d','list',
                                  tempfile.gettempdir()])
        found = execute(args) 
        assert found
        args = parser.parse_args(['-p',fname,'-o','12d','list',
                                  tempfile.gettempdir()])
        found = execute(args) 
        assert not found

def test_clean_files_with_pattern():
    files = []
    rootdir = tempfile.mkdtemp()
    try:
        for i in range(5):
            tmpfile = tempfile.NamedTemporaryFile(dir=rootdir,
                                                  suffix='test_clean')
            tmpfile.file.close()
            files.append(tmpfile.name)
            assert exists(tmpfile.name)
        args = parser.parse_args(['-f','-p','test_clean','clean',rootdir])
        execute(args)
        assert not all([exists(f) for f in files])
    finally:
        shutil.rmtree(rootdir)

