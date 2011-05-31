import ConfigParser, os
import os


possibleFiles = ['$HOME/.dropmess.ini']
currentFile = None
config = None

def get(section, option):
    global config
    config.get(section, option)
    
def set(section, option, value):
    global config
    config.get(section, option, value)

def save():
    global config
    f = open(currentFile, 'w')
    config.write(f)
    f.close()
    
def load():
    global config
    config = ConfigParser.ConfigParser()
    config.readfp(file(os.path.expandvars(possibleFiles[0])))

load()