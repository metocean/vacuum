import argparse
import pprint 
import six

from .utils import flister, delete

parser = argparse.ArgumentParser()
parser.add_argument('-r','--recursive', 
                    help='Find files inside sub-folders recursivelly',
                    action='store_true')
parser.add_argument('-f','--force', 
                    help="Don't prompt for confirmation on archive or cleaning operations",
                    action='store_true')
parser.add_argument('-p','--pattern', 
                    help='A RE pattern to search files inside root dir, accept multiple values',
                    action='append',
                    default=None)
parser.add_argument('-o','--older_then', 
                    help='Find files older then a giving period (i.e. 1h or 2min or 5d)',
                    action='store',
                    default=None)
parser.add_argument('-d','--max_depth', 
                    help='Max depth to recurse directories after root dirs',
                    action='store',
                    default=1,
                    type=int)
parser.add_argument('command', help='List files that matches the given conditions',
                    choices=['list', 'clean', 'archive'])
parser.add_argument('root', 
                    help='Root directory to search files for')

def print_filelist(filelist):
    files = []
    for filepath in filelist:
        print(filepath)
        files.append(filepath)
    return files

def _clean(filelist):
    filelist = [f for f in filelist]
    if len(filelist) == 0:
        print('No files found to be cleaned for the given selection.')
        return
    message = 'Were selected %d files or directories to be vacuum cleaned, Are you sure (l/y/N):' % len(filelist)
    while True:
        if force:
            option = 'Y'
        else:
            option = six.moves.input(message) or 'N'
        if option == 'l':
            print_filelist(filelist)
        elif option in ['y','Y']:
            files, dirs, errors = delete(filelist)
            print('Successfully cleaned %d files and %d directories!' %\
                                                     (len(files),len(dirs)))
            if errors:
                print('Some files or directories could not be deleted: %s',
                                            os.linesep.join(errors.keys()))
            break
        elif option in ['n','N']:
            break
        else:
            print('Options available [l]ist, [y]es or [n]o')


def execute(args):
    filelist = flister(args.root, args.pattern, args.older_then, args.recursive, 
                       args.max_depth)
    print 'hi'
    if args.command == 'list':
        return print_filelist(filelist)
    elif args.command == 'clean':
        return _clean(filelist)
    elif args.command == 'archive':
        print('Archiving not implemented yet')

if __name__ == "__main__":
    args = parser.parse_args()
    execute(args)