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

1. Get code.
2. Add directiories in `config.ini`
3. Start with `python dropmess.py -n`
