import ConfigParser
import argparse
import os
import time

configFile = './config.ini'
config = None

watchDirs = []
prevDiffs = {}

ifPossibleDigArchives = True
delay = 1

class Detector:
    '''The list of known file extensions grouped by type'''
    types = {
        'Applications' : [ 
            'exe', 'bin', 'deb', 'msi'
        ],
        
        'Music' : [ 
            'mp3', 'mp2', 'wav', 'rm', 'flac',
            'gp3', 'gp4', 'gp5'
        ],
        
        'Video' : [
            'avi', 'mpg', 'mov', 'mp4', 'ogv', 'flv', 'm4v', 'wmv', 'mkv'
        ],
        
        'Documents' : [
            # ms
            'doc', 'docx', 'xls', 'ppt',
            # oo
            'odt', 'odp',
            # other
            'psd', 'xcf',
            'txt', 'rtf', 'csv', 'pdf', 'tex'
        ],
        
        'Compressed' : [
            'tar', 'rar', 'zip', 'gz', '7z', 'iso'
        ],
        
        'Images' : [
            'jpg', 'png', 'gif', 'jpeg', 'tiff', 'raw', 'nef', 'svg', 'tga'
        ],
        
        'Sources' : [
            'rb', 'py', 'c', 'h', 'java', 'php', 'sh',
            'css', 'html', 'js'
        ],
        
        'Unknown' : []
    }
    
    def _getBest(self, typesWithScores):
        ''' Return most recurrent type from dictionary variable with structure:
            {'Video':1, 'Audio':3}'''
        maxScore = 0
        maxType = 'Unknown'
        for fileType, score in typesWithScores.items():
            if maxScore < score:
                maxScore = score
                maxType = fileType
        return (maxType, maxScore)
    
    def _extensionToType(self, ext):
        ''' Return type associated with given extension '''
        for (name, exts) in self.types.items():
            if ext in exts:
                return (name, 1)
        return ('Unknown', 1)
    
    def _fileExtension(self, path):
        ''' Extract extension from path '''
        return os.path.splitext(path)[1][1:].lower()
        
    
    def filesystem(self, name):
        ''' Return type of file or directory `name` '''
        return self._filesystem(name)[0]
    
    def _filesystem(self, name):
        if (os.path.isfile(name)):
            return self._file(name)
        
        elif (os.path.isdir(name)):
            return self._directory(name)
            
    def _file(self, name):
        ''' Return type of file '''
        ext = self._fileExtension(name)
        
        try:
            custom_handler = getattr(self, '_handle_'+ext)
            return custom_handler(name)
        except AttributeError:
            return self._extensionToType(ext)
    
    def _handle_rar(self, name):
        ''' Special handler for rar files '''
        try:
            rarfile
            archive = rarfile.RarFile(name)
            filesInArchive = [ f.filename for f in archive.infolist() ]
            archiveType = Detector().paths(filesInArchive)
            if archiveType == 'Unknown': 
                return ('Compressed', 1)
            else: 
                return (archiveType, 1)
        except NameError:
            return ('Compressed', 1)
        
    def _handle_zip(self, name):
        ''' Special handler for zip files '''
        try:
            zipfile
            archive = zipfile.ZipFile(name)
            filesInArchive = [ f.filename for f in archive.infolist() ]
            archiveType = Detector().paths(filesInArchive)
            if archiveType == 'Unknown': 
                return ('Compressed', 1)
            else: 
                return (archiveType, 1)
        except NameError:
            return ('Compressed', 1)
    
    def _directory(self, name):
        '''go recursively tough all files and return most recurrent file type.'''
        collector = {}
        for entry in os.listdir(name):
            #print os.path.join(name,entry)
            (fileType, score) = self._filesystem(os.path.join(name, entry))
            if fileType in collector:
                collector[fileType] += score
            else:
                collector[fileType] = score
        return self._getBest(collector)
    
        
    def paths(self, names):
        ''' Return most recurrent type based on array of paths '''
        collector = {}
        for name in names:
            ext = self._fileExtension(name)
            if ext == '': continue # ignore extensionless files
            fileType = self._extensionToType(ext)[0]
            if fileType in collector:
                collector[fileType] += 1
            else:
                collector[fileType] = 1
        return self._getBest(collector)[0]
            
        

def move(src, dst, attempt=0):
    '''Move `src` to `dst`.
    If `dst` already exists, script will add incrementally number to `dst`'''
    if args.debug:
        print src, ' = > ', dst 
    if args.simulate:
        return
    
    tmpdst = dst
    if attempt > 0:
        p1 = dst.rfind('.')
        p2 = dst.rfind('/')
        if p1 == -1 or p1 < p2:
            tmpdst += ' ' + str(attempt)
        else:
            (a, b, c) = dst.rpartition('.')
            b = ' ' + str(attempt) + '.'
            tmpdst = a + b + c
    
    try:
        if os.path.isfile(tmpdst):
            raise OSError
        os.rename(src, tmpdst)
        
    except OSError:
        # TODO: what if dst is not writable? infinite loop?
        move(src, dst, attempt + 1)

def dropMess(name):
    '''Tidy given directory.'''
    newDiff = {}
    try:
        for entry in os.listdir(name):
            if entry in Detector.types.keys():
                continue    
            path = os.path.join(name, entry)
            newDiff[name] = os.stat(path).st_mtime
            if newDiff[name] > time.time() - delay - 10:
                continue

            ftype = Detector().filesystem(path)
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
            if args.debug:
                print 
            for watchDir in watchDirs:
                dropMess(watchDir)
            time.sleep(delay)
                    
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(file(os.path.expandvars(configFile)))
    watchDirs = config.sections()
    for i in range(len(watchDirs)):
        watchDirs[i] = os.path.expandvars(watchDirs[i])
    
    parser = argparse.ArgumentParser(description='Automated filesystem selforganisation.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-n', action='store_true', help='Ninja mode (run in background)', dest='daemon')
    parser.add_argument('-d', action='store_true', help='Log actions', dest='debug')
    parser.add_argument('-s', action='store_true', help='Simulate - dont move anything', dest='simulate')
    args = parser.parse_args()
    
    if ifPossibleDigArchives:
        try: import rarfile
        except ImportError: 
            if args.debug: print 'rarfile module not installed'
        
        try: import zipfile
        except ImportError: 
            if args.debug: print 'zipfile module not installed'
    
    if args.daemon == True:
        from daemon import DaemonContext
        print 'Ninja mode activated.'
        with DaemonContext():
            main()
    else:
        print 'Started watching directories:'
        print watchDirs
        main()
