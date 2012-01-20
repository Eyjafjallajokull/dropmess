**dropmess** is a small python script for automatic filesystem categorization. For example it will turn your messy download directory:

    .
    ├── backup.tar.gz
    ├── code.rb
    ├── document.pdf
    ├── DSC_0014.JPG
    ├── DSC_0015.JPG
    ├── DSC_0016.JPG
    ├── track01.mp3
    ├── track02.mp3
    ├── track03.mp3
    └── script.sh
    
into nicely:
    
    .
    ├── Compressed
    ├── Documents
    ├── Images
    ├── Music
    └── Sources

Features
--------

- categorize files (and folders) into subdirectories
- look into compressed files and determine their contents type
- extract compressed files

* supported archives: ZIP, RAR, TAR, TAR.GZ, TAR.BZ2
    
Setup
-----

1. Get code `git://github.com/Eyjafjallajokull/dropmess.git`
2. Customize `config.ini`
3. Start with `python dropmess.py`
4. Learn more about command line arguments with `python dropmess.py -h`
5. (Optional) To run script as daemon install [python-daemon](http://pypi.python.org/pypi/python-daemon)
6. (Optional) Install python module [rarfile](http://pypi.python.org/pypi/rarfile/2.2) to support RAR files
