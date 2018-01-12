import os
import re
import six
import datetime
import yaml
import shutil

import timeparser

from os.path import *
from glob import iglob

__all__ = ['flister', 'older_then', 'pastdt', 'delete']

def pastdt(parseable):
    '''
    Return datetime object giving a py-timeparser parseable period from now.
    '''
    seconds = timeparser.parse(parseable)
    then = datetime.timedelta(seconds=seconds)
    return datetime.datetime.now()-then


def older_then(filepath, then):
    """ 
    Verify if a file is older `then` a giving datetime object
    """
    mtime = datetime.datetime.fromtimestamp(getmtime(filepath))
    return True if mtime < then else False
    
def flister(root=None, patterns=None, older=None, recursive=False, max_depth=1,
            depth=1):
    """Genrates a list of files and dirs giving root directory and a 
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
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
                success_directories.append(filepath)
            elif os.path.isfile(filepath):
                os.remove(filepath)
                success_files.append(filepath)
        except Exception as exc:
            errors[filepath] = exc
    message = 'Some files (%d) could not be deleted' % len(errors)
    if errors and raise_errors:
        raise Exception(message)
    return success_files, success_directories, errors