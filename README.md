# ACE2005-toolkit
### ACE 2005 data preprocess
#### file structure
 
```
ACE2005-toolkit
├── ace_2005 (the ACE2005 raw data)
│   ├── data
│   │   └── ...
│   ├── docs
│   │   └── ...
│   │── dtd
│   │   └── ...
│   └── index.html
├── cache_data (empty before run)
│   ├── Arabic
│   ├── Chinese
│   └── English
├── filelist (train/dev/test doc files)
│   ├── ace.ar.dev
│   ├── ace.ar.test
│   ├── ace.ar.train
│   ├── ace.en.dev
│   ├── ace.en.test
│   ├── ace.en.train
│   ├── ace.zh.dev
│   ├── ace.zh.test
│   └── ace.zh.train
│   
├── output(final output, empty before run)
│   └── ...
├── udpipe (udpipe files)
│   ├── arabic-padt-ud-2.5-191206
│   ├── chinese-gsd-ud-2.5-191206
│   └── english-ewt-ud-2.5-191206
├── ace_parser.py
├── extract.py
├── format.py
├── transform.py
├── udpipe.py
├── requirements.txt
└── run.sh

```
#### preprocess steps
1. Download the ACE2005 raw data and rename into `ace_2005` ;
2. Install all the requirements by `pip install -r requirements.txt`;
3. Start preprocess by `bash run.sh en`, `en` can be replaced by `zh` or `ar`;
4. Enter `n` to get data divided by filelist, or enter `y` and `train/dev/test rate`(e.g. `0.8 0.1 0.1`) to get data divided by sentences;
5. The final output will in `output/`.

#### adjustment
You can change the file names in `filelist/`, which will directly change the files belong to `train/dev/test`, we use a default (`529/30/40`) division.
#### related work
- [ACE05-Processor](https://github.com/wasiahmad/ACE05-Processor)
- [ace2005-preprocessing](https://github.com/nlpcl-lab/ace2005-preprocessing)
#### email us
Any questions can contact us by `haochenli@pku.edu.cn`.