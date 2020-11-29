#!/usr/bin/env bash

FILE=ace05.zip
OUT_DIR=./filelist/
if [[ ! -d $OUT_DIR ]]; then
    echo "Downloading file lists for data splits"
    fileid="1tvmrXHy0vrsSwb5IdtWvhFN1Z1EoEk88"
    curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=${fileid}" > /dev/null
    curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=${fileid}" -o ${FILE}
    rm ./cookie
    unzip ${FILE} -d $OUT_DIR && rm ${FILE}
fi

URL_PREFIX='https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131'
OUT_DIR=./udpipe/
if [[ ! -d $OUT_DIR ]]; then
    echo "Downloading UDPipe models"
    mkdir $OUT_DIR
    FILENAME=english-ewt-ud-2.5-191206.udpipe
    curl -o ${OUT_DIR}/${FILENAME} ${URL_PREFIX}/${FILENAME}
    FILENAME=arabic-padt-ud-2.5-191206.udpipe
    curl -o ${OUT_DIR}/${FILENAME} ${URL_PREFIX}/${FILENAME}
    FILENAME=chinese-gsd-ud-2.5-191206.udpipe
    curl -o ${OUT_DIR}/${FILENAME} ${URL_PREFIX}/${FILENAME}
fi

OUT_DIR=cache_data/
if [[ ! -d $OUT_DIR ]]; then
    mkdir $OUT_DIR
    python -W ignore format.py --data ./ace_2005/data/ \
    --filelist ./filelist/ --output $OUT_DIR --lang en
    python -W ignore format.py --data ./ace_2005/data/ \
    --filelist ./filelist/ --output $OUT_DIR --lang zh
    python -W ignore format.py --data ./ace_2005/data/ \
    --filelist ./filelist/ --output $OUT_DIR --lang ar
fi

python -W ignore extract.py --data $OUT_DIR --lang $1
python -W ignore transform.py --sentence False
#python -W ignore extract.py --data $OUT_DIR --lang ar
#python -W ignore extract.py --data $OUT_DIR --lang zh
rm -rf __pycache__/
