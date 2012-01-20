import unittest
import random
import string
import os
from subprocess import Popen

import sys
sys.path.insert(0, os.path.abspath('..'))
from dropmess import Detector, Node


TESTGROUND = 'testground'

allExts = []
for (_, exts) in Detector.categories.items():
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
        for (_, exts) in Detector.categories.items():
            for ext in exts:
                open( TESTGROUND + os.sep + getRandomName(None, ext), 'w').close()
        
    def tearDown(self):
        Popen('rm -rf '+ TESTGROUND + os.sep + '*', shell=True).wait()
        
    def test_extensionToType(self):
        params = (
                  ('txt', 'Documents'),
                  ('mp3', 'Music'),
                  ('dsadsa', 'Unknown'),
                  ('', 'Unknown')
                  )
        for (extension, expectedCategory) in params:
            self.assertEqual(Detector()._extensionToCategory(extension)[0], expectedCategory)
        
    def test_file(self):
        params = (
                  ('a.txt', 'Documents'),
                  ('a.mp3', 'Music'),
                  ('a.dsadsa', 'Unknown'),
                  ('a', 'Unknown'),
                  ('', 'Unknown')
                  )
        for (filePath, expectedCategory) in params:
            self.assertEqual(Detector()._file(Node(filePath))[0], expectedCategory)
        
    def test_paths(self):
        def paths(names, expected):
            category = Detector().paths(names)
            self.assertEqual(category, expected, 'Paths malfunction: %s != %s' % (category, expected) )
            
        paths([], 'Unknown')
        paths([Node('')], 'Unknown')
        paths([Node('a.txt')], 'Documents')
        self.assertIsNotNone( Detector().paths([Node(getRandomName()) for _ in range(0,10000)]) )
        
    def test_filesystem(self):
        self.assertIsNotNone(Detector().filesystem(Node(TESTGROUND)))
        
    def test_compressed(self):
        #TODO:
        pass
        
if __name__ == '__main__':
    unittest.main()