import ConfigParser
import argparse
import os
import time

configFile = './config.ini'
config = None

watchDirs = []
_prevDiffs = {}
digArchives = None
delay = None

class Detector:
    '''The list of known file extensions grouped by type '''
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
            'css', 'html', 'js', 'xml'
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
        ''' Private filesystem method for recursion '''
        if (os.path.isfile(name)):
            return self._file(name)
        
        elif (os.path.isdir(name)):
            return self._directory(name)
            
    def _file(self, name):
        ''' Return type of file '''
        ext = self._fileExtension(name)
        
        try:
            return getattr(self, '_handle_'+ext)(name)
        except AttributeError:
            return self._extensionToType(ext)
    
    def _handle_rar(self, name):
        ''' Special handler for rar files '''
        try: rarfile
        except NameError: return ('Compressed', 1)
        
        archive = rarfile.RarFile(name)
        filesInArchive = [ f.filename for f in archive.infolist() ]
        return self._commonCompressedFile(filesInArchive)
        
    def _handle_zip(self, name):
        ''' Special handler for zip files '''
        try: zipfile
        except NameError: return ('Compressed', 1)
        
        archive = zipfile.ZipFile(name)
        filesInArchive = [ f.filename for f in archive.infolist() ]
        return self._commonCompressedFile(filesInArchive)
        
    def _handle_gz(self, name):
        ''' Special handler for tar, tar.gz and tar.bz2 files '''
        try: tarfile
        except NameError: return ('Compressed', 1)
        
        if not (name.endswith('tar') or name.endswith('tar.gz') or name.endswith('tar.bz2')):
            return ('Compressed', 1)
        
        archive = tarfile.open(name, 'r:*')
        filesInArchive = archive.getnames()
        return self._commonCompressedFile(filesInArchive)
        
    def _commonCompressedFile(self, filesInArchive):
        ''' Detect type of files from archive '''
        archiveType = Detector().paths(filesInArchive)
        if archiveType == 'Unknown': 
            return ('Compressed', 1)
        else: 
            return (archiveType, 1)
        
    
    def _directory(self, name):
        ''' Go recursively tough all files and return most recurrent file type '''
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
        print src, ' -=> ', dst 
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
    ''' Tidy given directory '''
    # TODO: review usage of _revDiffs, newDiff 
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
    _prevDiffs[name] = newDiff
    
def main():
    try:
        if args.once:
            for watchDir in watchDirs:
                dropMess(watchDir)
        else:
            while True:
                if args.debug:
                    print 
                for watchDir in watchDirs:
                    dropMess(watchDir)
                time.sleep(delay)
                    
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    # read config
    config = ConfigParser.ConfigParser({
                                        'delay':10,
                                        'digArchives':True})
    config.readfp(file(os.path.expandvars(configFile)))
    delay = int(config.get('global', 'delay'))
    digArchives = int(config.get('global', 'digArchives'))==1
    
    # read directories to watch
    watchDirs = config.sections()
    watchDirs.remove('global')
    for i in range(len(watchDirs)):
        watchDirs[i] = os.path.expandvars(watchDirs[i])
    
    # parse command line arguments
    parser = argparse.ArgumentParser(description='Automated filesystem selforganisation.', 
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-n', action='store_true', help='Ninja mode - run in background', dest='daemon')
    parser.add_argument('-d', action='store_true', help='Debug mode - print more messages', dest='debug')
    parser.add_argument('-1', action='store_true', help='Single run - run algorithm only once and exit ', dest='once')
    parser.add_argument('-s', action='store_true', help='Simulate - don\'t move anything', dest='simulate')
    args = parser.parse_args()
    
    if digArchives:
        for module in ['rarfile', 'zipfile', 'tarfile']:
            try: vars()[module] = __import__(module)
            except ImportError: 
                if args.debug: print module+' module not installed'
        
    if args.daemon:
        try: from daemon import DaemonContext
        except ImportError: 
            print 'daemon module not installed'
            exit(1)
        with DaemonContext():
            main()
    else:
        print watchDirs
        main()
