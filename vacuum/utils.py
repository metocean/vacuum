import os
import re
import six
import time
import datetime
import yaml
import shutil
import re

import timeparser

from os.path import *
from glob import iglob

__all__ = ['flister', 'older_then', 'pastdt', 
           'delete', 'path2dt',
           'timestamp','archive']

STRPTIME_RE = re.compile('\%[YymdHMSaAwbBIpfzZjUW]')

STPTIME_TO_RE = {
    '%Y' : '(19|20)\d{2}',
    '%p': '(AM|PM|am|pm)',
    '%f': '\d{6}',
    '%j': '\d{3}',
    '%Z': '[A-Z]{3,5}',
    '%z': '(\+|\-)\d{4}',
}

for i in ['%y','%m','%d','%H','%M','%S','%W']:
    STPTIME_TO_RE[i] = '\d{2}'


def strptime_re(strptime):
    prepattern = []
    repattern = []
    for i in STRPTIME_RE.findall(strptime):
        strptime = re.sub(i, STPTIME_TO_RE[i], strptime)
    return re.compile(strptime)


def path2dt(filepath, date_strptime, time_strptime=None):
    """
    Parse datetime from the filepath following some pre-defined search re and
    format.

    Expect `date` part to be %Y%m%d and `time` part can be %Hz or %H%Mz
 
    return: datetime object if find date (and time) and None if no match
    """
    finddate = strptime_re(date_strptime).search(filepath)
    if finddate:
        date_obj = datetime.datetime.strptime(finddate.group(), date_strptime)
        if time_strptime:            
            findtime = strptime_re(time_strptime).search(filepath)
            if findtime:
                time_obj = datetime.datetime.strptime(findtime.group(),
                                                      time_strptime).time()
                timedelta_obj = datetime.timedelta(hours=time_obj.hour,
                                                   minutes=time_obj.minute,
                                                   seconds=time_obj.second,
                                                   microseconds=time_obj.microsecond)
                date_obj = date_obj + timedelta_obj
        return date_obj

def timestamp(dtobj):
    if six.PY2:
        return time.mktime(dtobj.timetuple())+dtobj.microsecond/1e6
    elif six.PY3:
        return dtobj.timestamp()

def pastdt(parseable, utc=False):
    '''
    Return datetime object giving a py-timeparser parseable period from now.
    '''
    seconds = timeparser.parse(parseable)
    then = datetime.timedelta(seconds=seconds)
    if utc:
        return datetime.datetime.utcnow()-then
    else:
        return datetime.datetime.now()-then 

def older_then(filepath, then, date_strptime=None, time_strptime=None):
    """ 
    Verify if a file is older `then` a giving datetime object
    """
    if then is None:
        return True
    elif os.path.exists(filepath):
        mtime = datetime.datetime.fromtimestamp(getmtime(filepath))
        if date_strptime:
            mtime = path2dt(filepath, date_strptime, time_strptime) or mtime
        return True if mtime < then else False
    else:
        return False

def str2re(patterns):
    compiled = []
    for patt in  patterns:
        assert isinstance(patt, six.string_types), 'Each pattern must be a string type'
        compiled.append(re.compile(patt))
    return compiled

   
def flister(rootdir=None, patterns=None, older=None, recursive=False, max_depth=1,
            depth=1, date_strptime=None, time_strptime=None, **kwargs):
    """
    Genrates a list of files giving a `rootdir` and a 
    list of matching RE patterns. Also filters for files `older` then
    a period parseable by py-timeparser.
    """
    rootdir = rootdir or abspath('.')
    if not isinstance(patterns, (tuple,list)):
        patterns = [patterns or '.+']

    compiled = str2re(patterns)

    then = pastdt(older) if older is not None else None
    
    for filepath in iglob(join(rootdir,'*')):
        filename = basename(filepath)
        for pattern in compiled:
            if isfile(filepath) and pattern.match(filename) and older_then(filepath,
                                            then, date_strptime,time_strptime): 
                yield filepath
            elif isdir(filepath) and recursive and depth < max_depth:
                i = 0
                for filepath in flister(filepath, patterns, older, 
                                        recursive, max_depth, 
                                        depth+1,date_strptime,
                                        time_strptime):
                    yield filepath
                if i == 0:
                    # maybe an empty dir lying around so subject to cleaning
                    yield filepath

def delete(filelist, raise_errors=False, 
           delete_empty=False,
           **kwargs):
    """
    Delete a list of files and directories
    """
    errors = {}
    success_files, success_directories = [], []
    for filepath in filelist:
        try:
            if isdir(filepath):
                shutil.rmtree(filepath)
                success_directories.append(filepath)
            elif isfile(filepath):
                os.remove(filepath)
                success_files.append(filepath)
            if delete_empty:
                remove_if_empty(dirname(filepath))

        except Exception as exc:
            errors[filepath] = exc
    message = 'Some files (%d) could not be deleted' % len(errors)
    if errors and raise_errors:
        raise Exception(message)
    return success_files, success_directories, errors

def maybe_create_dirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno not in [17]:
            raise

def remove_if_empty(dirpath):
    try:
        os.rmdir(dirpath)
    except:
        pass

def archive(filelist, destination, root_depth=0, raise_errors=False, **kwargs):
    errors = {}
    success_files, success_directories = [], []
    for filepath in filelist:
        try:
            if root_depth:
                branch = dirname(filepath.split(os.sep, root_depth+1)[-1])
                destination = join(destination, branch)
            maybe_create_dirs(destination)
            assert isdir(destination)
            if isfile(filepath) or islink(filepath):
                shutil.move(filepath, destination)
        except Exception as exc:
            errors[filepath] = exc
    message = 'Some files (%d) could not be archived' % len(errors)        
    if errors and raise_errors:
        raise Exception(message)  
    return success_files, success_directories, errors
