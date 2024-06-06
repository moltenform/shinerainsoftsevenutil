# shinerainsoftsevenutil
# Released under the LGPLv3 License

import os
from .m1_files_wrappers import *

def _listChildrenUnsorted(path, *, filenamesOnly=False, allowedExts=None):
    "list directory contents. allowedExts in the form ['png', 'gif']"
    for filename in os.listdir(path):
        if not allowedExts or getExt(filename) in allowedExts:
            yield filename if filenamesOnly else (path + os.path.sep + filename, filename)


if sys.platform.startswith('win'):
    exeSuffix = '.exe'
    listChildren = _listChildrenUnsorted
else:
    exeSuffix = ''

    def listChildren(*args, **kwargs):
        return sorted(_listChildrenUnsorted(*args, **kwargs))

def listDirs(path, *, filenamesOnly=False, allowedExts=None, recurse=False):
    "Return directories within a directory"
    if recurse:
        return recurseDirs(
            path, filenamesOnly=filenamesOnly, allowedExts=allowedExts, recurse=recurse
        )

    for full, name in listChildren(path, allowedExts=allowedExts):
        if os.path.isdir(full):
            yield name if filenamesOnly else (full, name)

def listFiles(path, *, filenamesOnly=False, allowedExts=None, recurse=False):
    "Return files within a directory"
    if recurse:
        return recurseFiles(
            path, filenamesOnly=filenamesOnly, allowedExts=allowedExts, recurse=recurse
        )

    for full, name in listChildren(path, allowedExts=allowedExts):
        if not os.path.isdir(full):
            yield name if filenamesOnly else (full, name)

def recurseFiles(
    root,
    *,
    filenamesOnly=False,
    allowedExts=None,
    fnFilterDirs=None,
    includeFiles=True,
    includeDirs=False,
    topDown=True,
    followSymlinks=False,
):
    """Return files within a directory (recursively).
    You can provide a fnFilterDirs to filter out any directories not to traverse into."""
    assert isDir(root)

    for dirPath, dirNames, fileNames in os.walk(root, topdown=topDown, followlinks=followSymlinks):
        if fnFilterDirs:
            filteredDirs = [dir for dir in dirNames if fnFilterDirs(join(dirPath, dir))]
            dirNames[:] = filteredDirs

        if includeFiles:
            iterFilenames = fileNames if sys.platform.startswith('win') else sorted(fileNames)
            for filename in iterFilenames:
                if not allowedExts or getExt(filename) in allowedExts:
                    yield (
                        filename if filenamesOnly else (dirPath + os.path.sep + filename, filename)
                    )

        if includeDirs:
            yield getName(dirPath) if filenamesOnly else (dirPath, getName(dirPath))

def recurseDirs(
    root, *, filenamesOnly=False, fnFilterDirs=None, topdown=True, followSymlinks=False
):
    """Return directories within a directory (recursively).
    You can provide a fnFilterDirs to filter out any directories not to traverse into."""
    return recurseFiles(
        root,
        filenamesOnly=filenamesOnly,
        fnFilterDirs=fnFilterDirs,
        includeFiles=False,
        includeDirs=True,
        topdown=topdown,
        followSymlinks=followSymlinks,
    )

class FileInfoEntryWrapper:
    "Helper class to make recurseFileInfo more convenient to use."

    def __init__(self, obj):
        self.obj = obj
        self.path = obj.path

    def isDir(self, *args):
        return self.obj.is_dir(*args)

    def isFile(self, *args):
        return self.obj.is_file(*args)

    def short(self):
        return os.path.split(self.path)[1]

    def size(self):
        return self.obj.stat().st_size

    def mtime(self):
        return self.obj.stat().st_mtime

    def getLastModifiedTime(self, units=TimeUnits.Seconds):
        mtime = self.obj.stat().st_mtime

        if units == TimeUnits.Nanoseconds:
            return int(mtime * 1.0e6)
        elif units == TimeUnits.Milliseconds:
            return int(mtime * 1000)
        elif units == TimeUnits.Seconds:
            return int(mtime)
        else:
            raise ValueError('unknown unit')

    def getMetadataChangeTime(self):
        assertTrue(not sys.platform.startswith('win'))
        return self.obj.stat().st_ctime

    def getCreateTime(self):
        assertTrue(sys.platform.startswith('win'))
        return self.obj.stat().st_ctime

def recurseFileInfo(
    root,
    recurse=True,
    followSymlinks=False,
    filesOnly=True,
    fnFilterDirs=None,
    fnDirectExceptionsTo=None,
):
    """Convenient interface to python 3's file iterator.
    On Windows this can be very fast because calls to get file properties like size
    don't require an extra system call.
    You can provide a fnFilterDirs to filter out any directories not to traverse into."""

    # note that scandir's resources are released in a destructor,
    # so do not create circular references holding it.
    for entry in os.scandir(root):
        if entry.is_dir(follow_symlinks=followSymlinks):
            if not filesOnly:
                yield FileInfoEntryWrapper(entry)
            if recurse and (not fnFilterDirs or fnFilterDirs(entry.path)):
                try:
                    for subentry in recurseFileInfo(
                        entry.path,
                        recurse=recurse,
                        followSymlinks=followSymlinks,
                        filesOnly=filesOnly,
                        fnFilterDirs=fnFilterDirs,
                        fnDirectExceptionsTo=fnDirectExceptionsTo,
                    ):
                        yield subentry
                except:
                    e = getCurrentException()
                    if fnDirectExceptionsTo and isinstance(e, OSError):
                        fnDirectExceptionsTo(entry.path, e)
                    else:
                        raise

        if entry.is_file():
            yield FileInfoEntryWrapper(entry)

def listFileInfo(root, followSymlinks=False, filesOnly=True):
    "Like recurseFileInfo, but does not recurse."
    return recurseFileInfo(root, recurse=False, followSymlinks=followSymlinks, filesOnly=filesOnly)
