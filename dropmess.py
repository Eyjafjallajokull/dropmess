import ConfigParser
import os
import time

fileTypes = {
  'Applications' : [ 'exe', 'bin', 'sh', 'deb' ],
  
  'Music' : [ 'mp3', 'mp2', 'wav', 'rm', 'flac' ],
  
  'Video' : [ 'avi', 'mpg', 'mov', 'mp4', 'ogv', 'flv' ],
  
  'Documents' : [
    # ms
    'doc', 'xls', 'ppt',
    # oo
    'odt', 'odp',
    # other
    'psd', 'xfc', 
    'txt', 'pdf'
  ],
  
  'Compressed' : [ 'tar', 'rar', 'zip', 'gz', '7z' ],
  
  'Images' : [ 'jpg', 'png', 'gif', 'jpeg', 'tiff', 'raw', 'nef', 'svg' ],
  
  'Sources' : [
    'rb', 'py', 'c', 'java', 'php', 
    'css', 'html', 'js'
  ],
  
  'Unknown' : [],
  'Dictionary' : []
}

dirs = []
diffs = {}

configFile = './dropmess.ini'
config = None

def detectType(name):
    if (os.path.isfile(name)):
        ext = os.path.splitext(name)[1][1:]
        for (name, exts) in fileTypes.items():
            if ext in exts:
                return name
        return 'Unknown';
    elif (os.path.isdir(name)):
        return 'Dictionary';

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
    diff = diffs[name] = os.listdir(name)
    for entry in diff:
        if entry in fileTypes.keys():
            continue
        path = os.path.join(name, entry)
        ftype = detectType(path)
        targetDir = os.path.join(name, ftype) + os.sep
        if not os.path.isdir(targetDir):
            os.mkdir(targetDir)
        target = os.path.join(targetDir, entry)
        move(path, target, 0)

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(file(os.path.expandvars(configFile)))
    dirs = config.sections()
    
    print dirs
    
    while True:
        for dir in dirs:
            dropMess(dir)
        time.sleep(1)
