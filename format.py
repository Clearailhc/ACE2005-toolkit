import os
import json
import argparse
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from collections import OrderedDict
from udpipe import Model
from ace_parser import Parser
from prettytable import PrettyTable

model_map = {
    'en': 'udpipe/english-ewt-ud-2.5-191206.udpipe',
    'zh': 'udpipe/chinese-gsd-ud-2.5-191206.udpipe',
    'ar': 'udpipe/arabic-padt-ud-2.5-191206.udpipe'
}

lang_name = {
    'en': 'English',
    'ar': 'Arabic',
    'zh': 'Chinese'
}


def check_duplicate_files(train, dev, test):
    num_train = len(set(train))
    num_dev = len(set(dev))
    num_test = len(set(test))
    if num_train != len(train):
        print('Warning: duplicate file found in train split')
    if num_dev != len(dev):
        print('Warning: duplicate file found in dev split')
    if num_test != len(test):
        print('Warning: duplicate file found in test split')
    total_files = len(train) + len(dev) + len(test)
    if total_files != num_train + num_dev + num_test:
        print('Warning: duplicate file found in train/dev/test split')


def get_filenames(args):
    """Check if file exists, return a file list for train/dev/test split."""

    def read_files(split):
        filepath = os.path.join(args.filelist, 'ace.%s.%s.txt' % (args.lang, split))
        filelist = []
        not_found = []
        with open(filepath) as f:
            for line in f:
                filename = '.'.join(line.strip().split('.')[:-2])
                sgm_file = os.path.join(args.data, '{}.sgm'.format(filename))
                xml_file = os.path.join(args.data, '{}.apf.xml'.format(filename))
                if os.path.exists(sgm_file) and os.path.exists(xml_file):
                    filelist.append(filename)
                else:
                    not_found.append(filename)
        print('[{:>5}] out of {:>3} files, {:>2} were not found.'.format(
            split.upper(), len(filelist) + len(not_found), len(not_found)))
        if not_found:
            print('Files that were not found - ', not_found)
        return filelist

    train = read_files('train')
    dev = read_files('dev')
    test = read_files('test')
    check_duplicate_files(train, dev, test)
    return train, dev, test


def parse_sgm(model, sgm_path):
    sgm_file = os.path.join(args.data, '{}.sgm'.format(sgm_path))
    with open(sgm_file, 'r') as f:
        soup = BeautifulSoup(f.read(), features='html.parser')
        sgm_text = soup.text

        sentences = model.tokenize(sgm_text, 'ranges')
        total_words = 0
        for s in sentences:
            total_words += len(s.words)
            model.tag(s)
            model.parse(s)
        conllu = model.write(sentences, "conllu")
        return conllu, len(sentences), total_words


def parse_xml(xml_path):
    parser = Parser(os.path.join(args.data, xml_path))
    return OrderedDict([
        ('entities', parser.entity_mentions),
        ('events', parser.event_mentions),
        ('relations', parser.relation_mentions)
    ])


def process_data(opt, model, filenames, split):
    outdir = os.path.join(opt.output, split)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    total_entities = 0
    total_events = 0
    total_relations = 0
    total_event_arguments = 0
    total_sentences = 0
    total_words = 0
    for filename in tqdm(filenames, total=len(filenames)):
        outfile = os.path.split(filename)[-1]
        conllu_file = os.path.join(outdir, '{}.conllu'.format(outfile))
        with open(conllu_file, 'w') as fw:
            conllu, num_sent, num_words = parse_sgm(model, filename)
            total_sentences += num_sent
            total_words += num_words
            fw.write(conllu)

        json_file = os.path.join(outdir, '{}.v1.json'.format(outfile))
        with open(json_file, 'w') as fw:
            jsonobj = parse_xml(filename)
            total_entities += len(jsonobj['entities'])
            total_events += len(jsonobj['events'])
            total_relations += len(jsonobj['relations'])
            total_event_arguments += sum([len(em['arguments']) for em in jsonobj['events']])
            json.dump(jsonobj, fw)

    return {
        'total_files': len(filenames),
        'total_sentences': total_sentences,
        'total_words': total_words,
        'total_entities': total_entities,
        'total_events': total_events,
        'total_relations': total_relations,
        'total_event_arguments': total_event_arguments
    }


def main(args):
    args.data = os.path.join(args.data, lang_name[args.lang])
    args.output = os.path.join(args.output, lang_name[args.lang])
    Path(args.output).mkdir(parents=True, exist_ok=True)
    train_files, dev_files, test_files = get_filenames(args)

    model = Model(model_map[args.lang])
    train_stat = process_data(args, model, train_files, 'train')
    dev_stat = process_data(args, model, dev_files, 'dev')
    test_stat = process_data(args, model, test_files, 'test')

    table = PrettyTable()
    table.field_names = ["Attribute", "Train", "Dev", "Test", "Total"]
    table.align["Attribute"] = "l"
    table.align["Train"] = "r"
    table.align["Dev"] = "r"
    table.align["Test"] = "r"
    table.align["Total"] = "r"

    table.add_row([
        '#Documents', train_stat['total_files'],
        dev_stat['total_files'], test_stat['total_files'],
        train_stat['total_files'] + dev_stat['total_files'] + test_stat['total_files']
    ])
    table.add_row([
        '#Sentences', train_stat['total_sentences'],
        dev_stat['total_sentences'], test_stat['total_sentences'],
        train_stat['total_sentences'] + dev_stat['total_sentences'] + test_stat['total_sentences']
    ])
    table.add_row([
        '#Words', train_stat['total_words'],
        dev_stat['total_words'], test_stat['total_words'],
        train_stat['total_words'] + dev_stat['total_words'] + test_stat['total_words']
    ])
    table.add_row([
        'Entity Mentions', train_stat['total_entities'],
        dev_stat['total_entities'], test_stat['total_entities'],
        train_stat['total_entities'] + dev_stat['total_entities'] + test_stat['total_entities']
    ])
    table.add_row([
        'Relation Mentions', train_stat['total_relations'],
        dev_stat['total_relations'], test_stat['total_relations'],
        train_stat['total_relations'] + dev_stat['total_relations'] + test_stat['total_relations']
    ])
    table.add_row([
        'Event Mentions', train_stat['total_events'],
        dev_stat['total_events'], test_stat['total_events'],
        train_stat['total_events'] + dev_stat['total_events'] + test_stat['total_events']
    ])
    table.add_row([
        'Event Arguments', train_stat['total_event_arguments'],
        dev_stat['total_event_arguments'], test_stat['total_event_arguments'],
        train_stat['total_event_arguments'] + dev_stat['total_event_arguments'] + test_stat['total_event_arguments']
    ])

    print(table)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='./ace_2005/data/',
                        help="Path of ACE2005 data")
    parser.add_argument('--filelist', type=str, default='./filelist/',
                        help="List of files for train/dev/test split")
    parser.add_argument('--lang', type=str, help="Name of the language", default='en',
                        choices=['en', 'ar', 'zh'])
    parser.add_argument('--output', type=str, default='./processed-data/',
                        help="Path of the output directory")
    args = parser.parse_args()
    print('\n' + '*' * 20 + lang_name[args.lang] + '*' * 20 + '\n')
    main(args)
