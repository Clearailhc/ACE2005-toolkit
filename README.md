# ACE2005-toolkit
### ACE 2005 data preprocess
#### File structure
 
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
│   ├── Arabic/
│   ├── Chinese/
│   └── English/
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
├── output (final output, empty before run)
│   ├── BIO (BIO output)
│   │   ├── train/
│   │   ├── test/
│   │   └── dev/
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
#### Preprocess steps
1. Download the ACE2005 raw data and rename into `ace_2005` ;
2. Install all the requirements by `pip install -r requirements.txt`;
3. Start preprocess by `bash run.sh en`, `en` can be replaced by `zh` or `ar`;
4. Enter `n` to get data divided by filelist, or enter `y` and `train/dev/test rate`(e.g. `0.8 0.1 0.1`) to get data divided by sentences;
5. Enter `y` to get transform the data into BIO-type format, the transformed data will be in `output/BIO/`
6. The final output will be in `output/`.
#### Output format
The output will save separately in `output/`, each file can be loaded by `json.loads()`. After loading, the data will be in `python list` type, each line will be in `python dict` type:
```
{
    "sentence": "Orders went out today to deploy 17,000 U.S. Army soldiers in the Persian Gulf region.",
    "tokens": [
        "Orders",
        "went",
        "out",
        "today",
        "to",
        "deploy",
        "17,000",
        "U.S.",
        "Army",
        "soldiers",
        "in",
        "the",
        "Persian",
        "Gulf",
        "region",
        "."
    ],
    "golden-entity-mentions": [
        {
            "entity-id": "CNN_CF_20030303.1900.02-E4-186",
            "entity-type": "GPE:Nation",
            "text": "U.S",
            "sent_id": "4",
            "position": [
                7,
                7
            ],
            "head": {
                "text": "U.S",
                "position": [
                    7,
                    7
                ]
            }
        },
        ...
    ],
    "golden-event-mentions": 
        {
            "event-id": "CNN_CF_20030303.1900.02-EV1-1",
            "event_type": "Movement:Transport",
            "arguments": [
                {
                    "text": "17,000 U.S. Army soldiers",
                    "sent_id": "4",
                    "position": [
                        6,
                        9
                    ],
                    "role": "Artifact",
                    "entity-id": "CNN_CF_20030303.1900.02-E25-1"
                },
                {
                    "text": "the Persian Gulf region",
                    "sent_id": "4",
                    "position": [
                        11,
                        15
                    ],
                    "role": "Destination",
                    "entity-id": "CNN_CF_20030303.1900.02-E76-191"
                }
            ],
            "text": "Orders went out today to deploy 17,000 U.S. Army soldiers\nin the Persian Gulf region",
            "sent_id": "4",
            "position": [
                0,
                15
            ],
            "trigger": {
                "text": "deploy",
                "position": [
                    5,
                    5
                ]
            }
        },
        ...
    ],
    "golden-relation-mentions": [
        {
            "relation-id": "CNN_CF_20030303.1900.02-R1-1",
            "relation-type": "ORG-AFF:Employment",
            "text": "17,000 U.S. Army soldiers",
            "sent_id": "4",
            "position": [
                6,
                9
            ],
            "arguments": [
                {
                    "text": "17,000 U.S. Army soldiers",
                    "sent_id": "4",
                    "position": [
                        6,
                        9
                    ],
                    "role": "Arg-1",
                    "entity-id": "CNN_CF_20030303.1900.02-E25-1"
                },
                {
                    "text": "U.S. Army",
                    "sent_id": "4",
                    "position": [
                        7,
                        8
                    ],
                    "role": "Arg-2",
                    "entity-id": "CNN_CF_20030303.1900.02-E66-157"
                }
            ]
        }, 
        ...
    ]
}
```
You will get all the golden data of `entities, events and relations` in output files.
#### Adjustment
You can change the file names in `filelist/`, which will directly change the files belong to `train/dev/test`, we use a default (`529/30/40`) division.
#### Related work
- [ACE05-Processor](https://github.com/wasiahmad/ACE05-Processor)
- [ace2005-preprocessing](https://github.com/nlpcl-lab/ace2005-preprocessing)
#### Email us
Any questions can contact us by `haochenli@pku.edu.cn`.