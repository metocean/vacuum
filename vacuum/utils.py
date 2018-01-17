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
           'delete', 'follow_links','path2dt',
           'timestamp']

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

def follow_links(path):
    def follow(linkto):
        if os.path.isfile(linkto) or os.path.isdir(linkto):
            return linkto
        elif os.path.islink(linkto):
            return follow_links(linkto)
        else:
            return path
    if os.path.islink(path):
        linkto = os.readlink(path)
        if linkto.startswith('/'):
            return follow(linkto)
        else:
            basedir = os.path.dirname(path)
            linkpath = os.path.join(basedir, linkto)
            return follow(linkpath)
    
def flister(root=None, patterns=None, older=None, recursive=False, max_depth=1,
            depth=1):
    """
    Genrates a list of files and dirs giving root directory and a 
    list of matching RE patterns. Also filters for files `older` then
    a period parseable by py-timeparser.
    """
    root = root or abspath('.')
    if not isinstance(patterns, (tuple,list)):
        patterns = [patterns or '.+']

    compiled = []
    for patt in  patterns:
        assert isinstance(patt, six.string_types), 'Each pattern must be a string type'
        compiled.append(re.compile(patt))
    
    then = pastdt(older) if older is not None else None
    
    for filepath in iglob(join(root,'*')):
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

def delete(filelist, raise_errors=False):
    """
    Delete a list of files and directories
    """
    deleted_dirs = []
    deleted_files = []
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

def archive(filelist, destination, follow_links=False, ignore=[]):
    ignore_func = ignore_paterns(*ignore) if ignore else None
    for filepath in filelist:
        if isdir(filepath):
            shutil.copytree(filepath, destination, ignore=ignore_func)
        elif isfile(filepath):
            shutil.move(filepath, destination)
        elif follow_links and islink(filepath):
            basename()
