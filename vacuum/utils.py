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

DATE_RE = re.compile('(20|19)\d{6}')
HOURMIN_RE = re.compile('\d{4}z')
HOUR_RE = re.compile('\d{2}z')
DATE_STRPTIME = '%Y%m%d'
HOURMIN_STRPTIME = '%H%Mz'
HOUR_STRPTIME = '%Hz'

def path2dt(filepath):
    """
    Parse datetime from the filepath following some pre-defined search re and
    format.

    Expect `date` part to be %Y%m%d and `time` part can be %Hz or %H%Mz
 
    return: datetime object if find date (and time) and None if no match
    """
    finddate = DATE_RE.search(filepath)
    if finddate:
        date_obj = datetime.datetime.strptime(finddate.group(), DATE_STRPTIME)
        findhourmin = HOURMIN_RE.search(filepath)
        time_obj = date_obj.time()
        if findhourmin:
            time_obj = datetime.datetime.strptime(findhourmin.group(),
                                                     HOURMIN_STRPTIME).time()
        else:
            findhour = HOUR_RE.search(filepath)
            if findhour:
                time_obj = datetime.datetime.strptime(findhour.group(),
                                                      HOUR_STRPTIME).time()
        timedelta_obj = datetime.timedelta(hours=time_obj.hour,
                                           minutes=time_obj.minute)
        return date_obj + timedelta_obj

def timestamp(dtobj):
    if six.PY2:
        return time.mktime(dtobj.timetuple())+dtobj.microsecond/1e6
    elif six.PY3:
        return dtobj.timetuple()

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
def older_then(filepath, then, datetime_from_filepath=False):
    """ 
    Verify if a file is older `then` a giving datetime object
    """
    if os.path.exists(filepath):
        if datetime_from_filepath:
            mtime = path2dt(filepath)
        else:    
            mtime = datetime.datetime.fromtimestamp(getmtime(filepath))
        return True if mtime < then else False
    else:
        return False
   
def flister(rootdir=None, patterns=None, older=None, recursive=False, max_depth=1,
            depth=1, **kwargs):
    """
    Genrates a list of files and dirs giving `rootdir` directory and a 
    list of matching RE patterns. Also filters for files `older` then
    a period parseable by py-timeparser.
    """
    rootdir = rootdir or abspath('.')
    if not isinstance(patterns, (tuple,list)):
        patterns = [patterns or '.+']

    compiled = []
    for patt in  patterns:
        assert isinstance(patt, six.string_types), 'Each pattern must be a string type'
        compiled.append(re.compile(patt))
    
    then = pastdt(older) if older is not None else None
    
    for filepath in iglob(join(rootdir,'*')):
        filename = basename(filepath)
        for patt in compiled:
            if patt.match(filename):
                if older is None or (older is not None \
                                     and older_then(filepath, then)):        
                    yield filepath
            if recursive and depth < max_depth and os.path.isdir(filepath) :
                for filepath in flister(filepath, patterns, older, 
                                        recursive, max_depth, 
                                        depth+1):
                    yield filepath    

def delete(filelist, raise_errors=False, **kwargs):
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
