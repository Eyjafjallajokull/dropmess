import ConfigParser
import os
import time
import glob

fileTypes = {
    'Applications' : [ 
        'exe', 'bin', 'deb'
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
        'doc', 'xls', 'ppt',
        # oo
        'odt', 'odp',
        # other
        'psd', 'xcf', 
        'txt', 'pdf'
    ],
    
    'Compressed' : [
        'tar', 'rar', 'zip', 'gz', '7z', 'iso'
    ],
    
    'Images' : [
        'jpg', 'png', 'gif', 'jpeg', 'tiff', 'raw', 'nef', 'svg'
    ],
    
    'Sources' : [
        'rb', 'py', 'c', 'java', 'php', 'sh', 
        'css', 'html', 'js'
    ],
    
    'Unknown' : []
}

dirs = []
prevDiffs = {}

configFile = './dropmess.ini'
config = None

def detectType(name):
    if (os.path.isfile(name)):
        ext = os.path.splitext(name)[1][1:]
        for (name, exts) in fileTypes.items():
            if ext.lower() in exts:
                return (name,1)
        return ('Unknown',1)
    elif (os.path.isdir(name)):
        collector = {}
        for entry in os.listdir(name):
            #print os.path.join(name,entry)
            (type,count) = detectType(os.path.join(name,entry))
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
    newDiff = {}
    for entry in os.listdir(name):
        if entry in fileTypes.keys():
            continue    
        path = os.path.join(name, entry)
        newDiff[name] = os.stat(path).st_mtime
        if newDiff[name] > time.time()-10:
            continue
        
        ftype = detectType(path)[0]
        targetDir = os.path.join(name, ftype) + os.sep
        if not os.path.isdir(targetDir):
            os.mkdir(targetDir)
        
        target = os.path.join(targetDir, entry)
        move(path, target, 0)
        
    prevDiffs[name] = newDiff

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(file(os.path.expandvars(configFile)))
    dirs = config.sections()
    for i in range(len(dirs)):
        dirs[i] = os.path.expandvars(dirs[i])
    
    print dirs
    
    while True:
        for dir in dirs:
            dropMess(dir)
        time.sleep(1)
