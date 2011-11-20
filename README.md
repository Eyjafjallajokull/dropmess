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
    
Setup
-----

1. Install [python-daemon](http://pypi.python.org/pypi/python-daemon)
2. Get code
3. Add directiories in `config.ini`
4. Start with `python dropmess.py -n`
