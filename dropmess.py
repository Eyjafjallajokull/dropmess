import ConfigParser
import argparse
import os
import time
import glob

'''The list of known file extensions grouped by type'''
fileTypes = {
    'Applications' : [ 
        'exe', 'bin', 'deb', 'msi'
    ],
    
    'Music' : [ 
        'mp3', 'mp2', 'wav', 'rm', 'flac',
        'gp3', 'gp4', 'gp5'
    ],
    
    'Video' : [
        'avi', 'mpg', 'mov', 'mp4', 'ogv', 'flv', 'm4v','wmv'
    ],
    
    'Documents' : [
        # ms
        'doc', 'docx', 'xls', 'ppt',
        # oo
        'odt', 'odp',
        # other
        'psd', 'xcf', 
        'txt', 'rtf', 'csv', 'pdf'
    ],
    
    'Compressed' : [
        'tar', 'rar', 'zip', 'gz', '7z', 'iso'
    ],
    
    'Images' : [
        'jpg', 'png', 'gif', 'jpeg', 'tiff', 'raw', 'nef', 'svg', 'tga'
    ],
    
    'Sources' : [
        'rb', 'py', 'c', 'java', 'php', 'sh', 
        'css', 'html', 'js'
    ],
    
    'Unknown' : []
}

configFile = './config.ini'
config = None

dirs = []
prevDiffs = {}

def detectType(name):
    '''Return type of `name` node'''
    return _detectType(name)[0]
    
def _detectType(name):
    '''Return touple: (type of specified file or directory, number of matches).
    
    If `name` is a path to directory script will go recursively 
    tough all files and return most matched file type.'''
    if (os.path.isfile(name)):
        ext = os.path.splitext(name)[1][1:]
        for (name, exts) in fileTypes.items():
            if ext.lower() in exts:
                return (name,1)
        return ('Unknown',1)
    
    elif (os.path.isdir(name)):
        '''Go Go Recursion'''
        collector = {}
        for entry in os.listdir(name):
            #print os.path.join(name,entry)
            (type,count) = _detectType(os.path.join(name,entry))
            if type in collector:
                collector[type] += count
            else:
                collector[type] = count
        max = 0
        maxType = 'Unknown'
        for type, count in collector.items():
            if max < count:
                max = count
                maxType = type
        return (maxType,max)

def move(src, dst, attempt = 0):
    '''Move `src` to `dst`.
    If `dst` already exists, script will add incrementally number to `dst`'''
    if args.debug:
        print src, ' = > ',dst 
    
    tmpdst = dst
    if attempt > 0:
        p1 = dst.rfind('.')
        p2 = dst.rfind('/')
        if p1 == -1 or p1 < p2:
            tmpdst += ' '+str(attempt)
        else:
            (a,b,c) = dst.rpartition('.')
            b = ' '+str(attempt)+'.'
            tmpdst = a + b + c
    
    try:
        if os.path.isfile(tmpdst):
            raise OSError
        os.rename(src, tmpdst)
        
    except OSError:
        # TODO: what if dst is not writable? infinite loop?
        move(src, dst, attempt+1)

def dropMess(name):
    '''Tidy given directory.'''
    newDiff = {}
    try:
        for entry in os.listdir(name):
            if entry in fileTypes.keys():
                continue    
            path = os.path.join(name, entry)
            newDiff[name] = os.stat(path).st_mtime
            if newDiff[name] > time.time()-10:
                continue

            ftype = detectType(path)
            targetDir = os.path.join(name, ftype) + os.sep
            if not os.path.isdir(targetDir):
                os.mkdir(targetDir)

            target = os.path.join(targetDir, entry)
            move(path, target, 0)
    except OSError as err:
    	print err
    	exit(1)
    prevDiffs[name] = newDiff
    
def main():
    try:
        while True:
            for dir in dirs:
                dropMess(dir)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(file(os.path.expandvars(configFile)))
    dirs = config.sections()
    for i in range(len(dirs)):
        dirs[i] = os.path.expandvars(dirs[i])
    
    parser = argparse.ArgumentParser(description='Automated filesystem selforganisation.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-n', action='store_true', help='Ninja mode (run in background)', dest='daemon')
    parser.add_argument('-d', action='store_true', help='Log actions', dest='debug')
    args = parser.parse_args()
    
    
    if args.daemon == True:
        from daemon import DaemonContext
        print 'Ninja mode activated.'
        with DaemonContext():
            main()
    else:
        print 'Started watching directories:'
        print dirs
        main()
