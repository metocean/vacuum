import os
import re
import six
import time
import datetime
import yaml
import shutil
import re
import string
import random

import timeparser

from os.path import *
from glob import iglob

__all__ = ['flister', 'is_older_than', 'pastdt', 
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


def rand_chars(lenght=8):
    return ''.join([random.choice(string.ascii_letters) for i in range(lenght)])

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

def pastdt(parseable, utc=False, now=None):
    '''
    Return datetime object giving a py-timeparser parseable period from now.
    '''
    seconds = timeparser.parse(parseable)
    delta = datetime.timedelta(seconds=seconds)
    if now:
        return now-delta
    else:
        if utc:
            return datetime.datetime.utcnow()-delta
        else:
            return datetime.datetime.now()-delta

def is_older_than(filepath, than, date_strptime=None, time_strptime=None):
    """ 
    Verify if a file is older `than` a giving datetime object
    """
    if than is None:
        return True
    elif os.path.exists(filepath):
        mtime = datetime.datetime.fromtimestamp(getmtime(filepath))
        if date_strptime:
            mtime = path2dt(filepath, date_strptime, time_strptime) or mtime
        return True if mtime < than else False
    else:
        return False

def str2re(patterns):
    compiled = []
    for patt in  patterns:
        assert isinstance(patt, six.string_types), 'Each pattern must be a string type'
        compiled.append(re.compile(patt))
    return compiled

   
def flister(rootdir=None, patterns=None, older_than=None, recursive=False, max_depth=1,
            depth=1, date_strptime=None, time_strptime=None, now=None, **kwargs):
    """
    Genrates a list of files giving a `rootdir` and a 
    list of matching RE patterns. Also filters for files `older_than` than
    a period parseable by py-timeparser.
    """
    rootdir = rootdir or abspath('.')
    if not isinstance(patterns, (tuple,list)):
        patterns = [patterns or '.+']

    compiled = str2re(patterns)

    than = pastdt(older_than, now=now) if older_than is not None else None
    
    for filepath in iglob(join(rootdir,'*')):
        filename = basename(filepath)
        for pattern in compiled:
            if isfile(filepath) and pattern.match(filename) and \
               is_older_than(filepath, than, date_strptime, time_strptime): 
                yield filepath
            elif islink(filepath) and pattern.match(filename):
                # yield links that match pattern, links ignore older_than
                yield filepath
            elif isdir(filepath) and recursive and depth < max_depth:
                i = 0
                for filepath_ in flister(filepath, patterns, older_than, 
                                        recursive, max_depth, 
                                        depth+1,date_strptime,
                                        time_strptime):
                    yield filepath_
                    i += 1
                if i == 0 and os.path.exists(filepath) and not os.listdir(filepath):
                    # empty dirs are yielded as well regardless of parameters
                    yield filepath

def delete(filelist, raise_errors=False, 
           delete_empty=False,
           **kwargs):
    """
    Delete a list of files and directories
    """
    errors = {}
    success_files, success_directories = [], []
    basedirs = set()
    for filepath in filelist:
        try:
            if isdir(filepath):
                shutil.rmtree(filepath)
                success_directories.append(filepath)
            elif isfile(filepath) or os.path.lexists(filepath):
                os.remove(filepath)
                success_files.append(filepath)
            basedirs.update([dirname(filepath)])
        except Exception as exc:
            errors[filepath] = exc
    if delete_empty:
        for basedir in sorted(list(basedirs), reverse=True):
            if len(basedir.split(sep)) > 2:
                remove_if_empty(basedir)
                success_directories.append(basedir)
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

def archive(filelist, destination, root_depth=0, raise_errors=False, 
            action='copy', **kwargs):
    errors = {}
    success_files, success_directories = [], []
    for filepath in filelist:
        try:
            if root_depth:
                branch = dirname(filepath.split(os.sep, root_depth+1)[-1])
                final_destination = join(destination, branch)
            else:
                final_destination = destination
            maybe_create_dirs(final_destination)
            assert isdir(final_destination)
            filename = os.path.basename(filepath)
            tmp_file = os.path.join(final_destination, filename+'.'+rand_chars())
            final_file = os.path.join(final_destination, filename)
            if isfile(filepath) or islink(filepath):
                shutil.copy2(filepath, tmp_file)
                if os.path.exists(final_file):
                    os.remove(final_file)
                os.rename(tmp_file, final_file)
                if action == 'move' and os.path.exists(final_file):
                    os.remove(filepath)
                success_files.append(filepath)
        except Exception as exc:
            errors[filepath] = exc
    message = 'Some files (%d) could not be archived' % len(errors)        
    if errors and raise_errors:
        raise Exception(message)  
    return success_files, success_directories, errors
