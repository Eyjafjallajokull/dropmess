import unittest
import random
import string
import os
from subprocess import Popen

import sys
sys.path.insert(0, os.path.abspath('..'))
from dropmess import Detector


TESTGROUND = 'testground'

allExts = []
for (_, exts) in Detector.types.items():
    for ext in exts:
        allExts.append(ext)


def getRandomName(length=None, ext=''):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + """!#$&'()+,-.;<=>@[\]^_`{}~ """
    ext = str(ext)
    if ext == '': ext = getRandomExt()
    if not ext.startswith('.'): ext = '.' + ext
    if length == None: length = random.randint(1,50)
    return ''.join(random.sample(chars, length)) + ext

def getRandomExt():
    return random.choice(allExts)


class TestDetector(unittest.TestCase):

    def setUp(self):
        for (_, exts) in Detector.types.items():
            for ext in exts:
                open( TESTGROUND + os.sep + getRandomName(None, ext), 'w').close()
        
    def tearDown(self):
        Popen('rm -rf '+ TESTGROUND + os.sep + '*', shell=True).wait()
        
    def test_extensionToType(self):
        self.assertEqual(Detector()._extensionToType('txt')[0], 'Documents')
        self.assertEqual(Detector()._extensionToType('mp3')[0], 'Music')
        self.assertEqual(Detector()._extensionToType('dsadsa')[0], 'Unknown')
        self.assertEqual(Detector()._extensionToType('')[0], 'Unknown')
        
    def test_file(self):
        self.assertEqual(Detector()._file('a.txt')[0], 'Documents')
        self.assertEqual(Detector()._file('a.mp3')[0], 'Music')
        self.assertEqual(Detector()._file('a.dsadsa')[0], 'Unknown')
        self.assertEqual(Detector()._file('a')[0], 'Unknown')
        self.assertEqual(Detector()._file('')[0], 'Unknown')
        
    def test_paths(self):
        def paths(names, expected):
            category = Detector().paths(names)
            self.assertEqual(category, expected, 'Paths malfunction: %s != %s' % (category, expected) )
            
        paths([], 'Unknown')
        paths([''], 'Unknown')
        paths(['',''], 'Unknown')
        paths(['a.txt'], 'Documents')
        self.assertIsNotNone( Detector().paths([getRandomName() for _ in range(0,10000)]) )
        
    def test_filesystem(self):
        self.assertIsNotNone(Detector().filesystem(TESTGROUND))
        
    def test_compressed(self):
        #TODO:
        pass
        
if __name__ == '__main__':
    unittest.main()