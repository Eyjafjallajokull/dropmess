import core.config as config
import mimetypes
import os
import time

dirs = []
diffs = {}

types = {}
for (ext,type) in mimetypes.types_map.items():
    types[type[0:type.find('/')]] = 1
types = types.keys()
types.append('dir')
types.append('unknown')

def dropFile(filename):
    pass

def dropDir(dirname):
    pass

def detectMime(name):
    if (os.path.isfile(name)):
        mime = mimetypes.guess_type(name)[0]
        if mime == None:
            return 'unknown';
        return mime[0 : mime.find('/')]
    
    elif (os.path.isdir(name)):
        return 'dir';
        for root, dirs, files in os.walk(name):
            for file in files:
                pass

def move(src, dst, attempt = 0):
    #print src,dst,attempt
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
        move(src, dst, attempt+1)

def dropMess(name):
    global diffs
    diff = diffs[name] = os.listdir(name)
    for entry in diff:
        if entry in types:
            continue
        path = os.path.join(name, entry)
        mime = detectMime(path)
        targetDir = os.path.join(name, mime) + os.sep
        if not os.path.isdir(targetDir):
            os.mkdir(targetDir)
        target = os.path.join(targetDir, entry)
        move(path, target, 0)

if __name__ == '__main__':
    config.load()
    dirs = config.config.sections()
    print dirs
    
    while True:
        for dir in dirs:
            dropMess(dir)
        time.sleep(1)