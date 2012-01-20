import ConfigParser
import argparse
import os
import time
from subprocess import Popen, PIPE
from inspect import ismodule

configFile = './config.ini'
config = None

watchDirs = []
_prevDiffs = {}
digArchives = None
extractArchives = None
delay = None
rarfile = zipfile = tarfile = None

class OpenedNode(Exception): pass

class Node:
    path = '' 
    dir = ''
    fileName = '' 
    fileBaseName = '' 
    extension = ''
    
    isFilesystem = True
    category = None
    
    def __init__(self, path, isFilesystem = True):
        self.path = path
        (self.dir, self.fileName) = os.path.split(path)
        (self.fileBaseName, self.extension) = os.path.splitext(self.fileName)
        self.extension = self.extension[1:]
        self.isFilesystem = isFilesystem
    
    def getCategory(self):
        if not self.category:
            self.category = Detector().getCategory(self)
        return self.category

    def move(self, targetPath, attempt=0):
        '''Move `src` to `targetPath`.
        If `targetPath` already exists, script will add incrementally number to `targetPath`'''
        
        
        if args.debug:
            print self.path, ' -=> ', targetPath 
        if args.simulate:
            return
        
        if attempt > 1000 and args.debug:
            print 'i tried 1000 times to move %s and failed' % self.path
            return
        
        tmpdst = targetPath
        if attempt > 0:
            p1 = targetPath.rfind('.')
            p2 = targetPath.rfind('/')
            if p1 == -1 or p1 < p2:
                tmpdst += ' ' + str(attempt)
            else:
                (a, b, c) = targetPath.rpartition('.')
                b = ' ' + str(attempt) + '.'
                tmpdst = a + b + c
        
        # TODO: this is unreadable
        try:
            if os.path.isfile(tmpdst):
                raise OSError
            os.rename(self.path, tmpdst)
            self.__init__(targetPath)
            
        except OSError:
            # TODO: what if targetPath is not writable? infinite loop?
            self.move(targetPath, attempt + 1)
            self.__init__(targetPath)
        


class Detector:
    ''' Detect category of given filesystem node or list of paths
    Examples:
    Detector().filesystem('/home/user/file.txt')
    Detector().filesystem('/home/user/Directory')
    Detector().paths(['/home/user/abc.txt', '/home/user/def.mp3'])
    '''
    
    '''The list of known file extensions grouped by category '''
    categories = {
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
    
    def getCategory(self, node):
        if node.isFilesystem:
            return self.filesystem(node)
        else:
            return self._extensionToCategory(node)
    
    def _getBest(self, categoriesWithScores):
        ''' Return most recurrent category from dictionary variable with structure:
            {'Video':1, 'Audio':3}'''
        maxScore = 0
        maxCategory = 'Unknown'
        for fileCategory, score in categoriesWithScores.items():
            if maxScore < score:
                maxScore = score
                maxCategory = fileCategory
        return (maxCategory, maxScore)
    
    def _extensionToCategory(self, ext):
        ''' Return category associated with given extension '''
        for (category, exts) in self.categories.items():
            if ext in exts:
                return (category, 1)
        return ('Unknown', 1)
        
    
    def filesystem(self, node):
        ''' Return category of given node '''
        # run check for opened file descriptors
        result = Popen('lsof +D "%s" | wc -l' % node.path,
                       shell=True, stdout=PIPE, stderr=PIPE).communicate()[0]
        if result.strip() == '0': 
            return self._filesystem(node)[0]
        else:
            raise OpenedNode()
    
    def _filesystem(self, node):
        ''' Private filesystem method for recursion '''
        if (os.path.isfile(node.path)):
            return self._file(node)
        
        elif (os.path.isdir(node.path)):
            return self._directory(node)
            
    def _file(self, node):
        ''' Return category of file '''
        preHook = HooksPre().getAccurateCategory(node)
        if preHook[0]!='Unknown':
            return preHook
        else:
            return self._extensionToCategory(node.extension)
        
    
    def _directory(self, node):
        ''' Go recursively tough all files and return most recurrent file category '''
        collector = {}
        for entry in os.listdir(node.path):
            #print os.path.join(name,entry)
            subNode = Node( os.path.join(node.path, entry) )
            
            (fileCategory, score) = self._filesystem( subNode )
            if fileCategory in collector:
                collector[fileCategory] += score
            else:
                collector[fileCategory] = score
        return self._getBest(collector)
    
        
    def paths(self, nodes):
        ''' Return most recurrent category based on array of paths '''
        collector = {}
        for node in nodes:
            if node.extension == '': continue # ignore extensionless files
            fileCategory = self._extensionToCategory(node.extension)[0]
            if fileCategory in collector:
                collector[fileCategory] += 1
            else:
                collector[fileCategory] = 1
        return self._getBest(collector)[0]


class HooksPre():
    ''' More accurate category detector methods. '''
    
    def getAccurateCategory(self, node):
        self.node = node
        try:
            return getattr(self, '_handle_%s' % self.node.extension)()
        except AttributeError:
            return ('Unknown', 1)
    
    def _commonCompressedFile(self, filesInArchive):
        ''' Detect category of files from archive '''
        if not digArchives: return ('Compressed', 1)
        
        archiveCategory = Detector().paths([ Node(f, False) for f in filesInArchive ])
        if archiveCategory == 'Unknown':
            return ('Compressed', 1)
        else: 
            return (archiveCategory, 1)
        
    def _handle_rar(self):
        if not ismodule(rarfile): return ('Compressed', 1)
        
        filesInArchive = [ f.filename for f in rarfile.RarFile(self.node.path).infolist() ]
        return self._commonCompressedFile(filesInArchive)
        
    def _handle_zip(self):
        if not ismodule(zipfile): return ('Compressed', 1)
        
        filesInArchive = [ f.filename for f in zipfile.ZipFile(self.node.path).infolist() ]
        return self._commonCompressedFile(filesInArchive)
        
    def _handle_tar(self):
        if not ismodule(tarfile): return ('Compressed', 1)
        
        path = self.node.path
        if not (path.endswith('tar') or path.endswith('tar.gz') or path.endswith('tar.bz2')):
            return ('Compressed', 1)
        
        filesInArchive = tarfile.open(path, 'r:*').getnames()
        return self._commonCompressedFile(filesInArchive)
        
    def _handle_bz2(self):
        return self._handle_tar()
        
    def _handle_gz(self):
        return self._handle_tar()
    

class HooksPost():
    ''' Execute actions on moved items '''
    def __init__(self, node):
        self.node = node
        try:
            getattr(self, '_handle_%s' % self.node.extension)()
        except AttributeError:
            pass
    
    def _commonCompressedHandler(self, func):
        if not extractArchives or args.simulate: return
        
        targetPath = os.path.join(self.node.dir, self.node.fileBaseName)
        if not os.path.exists(targetPath):
            if args.debug:
                print 'extract ',self.node.path,'  -=>  ',targetPath
            func(self.node.path, targetPath)
            self.node.__init__(targetPath)
        else:
            if args.debug:
                print 'cant extract, dir exists'
        
    def _handle_rar(self):
        if not ismodule(rarfile): return
        self._commonCompressedHandler( lambda src, dst: rarfile.RarFile(src).extractall(dst) )
        
    def _handle_zip(self):
        if not ismodule(zipfile): return
        self._commonCompressedHandler( lambda src, dst: zipfile.ZipFile(src).extractall(dst) )
        
    #TODO: tar gz bz2


def dropMess(rootPath):
    ''' Tidy given directory '''
    newDiff = {}
    try:
        for nodeName in os.listdir(rootPath):
            if nodeName in Detector.categories.keys():
                continue
            node = Node( os.path.join(rootPath, nodeName) )
            newDiff[rootPath] = os.stat(node.path).st_mtime
            if newDiff[rootPath] > time.time() - delay - 10:
                continue
            
            try:
                node.getCategory()
            except OpenedNode:
                if args.debug:
                    print 'opened file(s) %s' % node.path
                continue
            
            targetPath = os.path.join(rootPath, node.category)
            if not os.path.isdir(targetPath):
                os.mkdir(targetPath)

            node.move( os.path.join(targetPath, nodeName))
            
            HooksPost(node)
    except OSError as err:
        print err
        exit(1)
    _prevDiffs[rootPath] = newDiff
    
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
    digArchives = int(config.get('global', 'digArchives')) == 1
    extractArchives = int(config.get('global', 'extractArchives')) == 1
    
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
    
    # initialize compression modules
    if digArchives:
        for module in ['rarfile', 'zipfile', 'tarfile']:
            try: vars()[module] = __import__(module)
            except ImportError: 
                if args.debug: print module + ' module not installed'
        
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
