import json
import os
import numpy as np
from tqdm import tqdm
import argparse


def get_sentence_token(raw_data):
    """get sentences token from data"""
    token = []
    for sent in raw_data:
        token.append(sent['tokens'])
    return token


def get_entity_tag(raw_data):
    """get entity_tag for each token from data (not BIO type)"""
    entity_tag = []
    for sent in raw_data:
        sent_tag = []
        for i in range(len(sent['tokens'])):
            sent_tag.append(['O'])
        entity_tag.append(sent_tag)  # because of overlap,get a tag list for each token
    for i in range(len(raw_data)):
        temp_sent = raw_data[i]
        temp_entity_mentions = temp_sent['golden-entity-mentions']
        if len(temp_entity_mentions) == 0:  # skip if none
            continue
        type_list = []
        position_list = []
        length_list = []
        for entity in temp_entity_mentions:
            type_list.append(entity['entity-type'])
            position_list.append(
                [entity['position'][0], entity['position'][1] + 1])  # plus 1 to make sure not empty
            length_list.append(entity['position'][1] - entity['position'][0] + 1)
        length_list = np.array(length_list)
        index = np.argsort(length_list)[::-1]  # get the length idx from long to short
        for idx in index:
            temp_start = position_list[idx][0]
            for k in range(length_list[idx]):
                if k == 0:
                    entity_tag[i][temp_start + k] += ['B-'+type_list[idx]]
                else:
                    entity_tag[i][temp_start + k] += ['I-'+type_list[idx]]
                # entity_tag[i][position_list[idx][0]: position_list[idx][1]] = [type_list[idx]] * int(length_list[idx])
    for sent in entity_tag:  # delete 'O' if token is a named entity
        for token in sent:
            if len(token) > 1:
                del token[0]
    return entity_tag


def get_event_tag(raw_data):
    event_trigger_tag = []  # initial trigger tag
    for sent in raw_data:
        sent_tag = []
        for _ in range(len(sent['tokens'])):
            sent_tag.append(['O'])
        event_trigger_tag.append(sent_tag)  # trigger_tag dont overlap

    event_argument_tag = []  # initial argument tag
    for sent in raw_data:
        sent_tag = []
        for _ in range(len(sent['tokens'])):
            sent_tag.append(['O'])
        event_argument_tag.append(sent_tag)  # because of multi-event,get a tag list for each token

    for i in tqdm(range(len(raw_data)), total=len(raw_data)):
        temp_sent = raw_data[i]
        temp_event_mentions = temp_sent['golden-event-mentions']
        if len(temp_event_mentions) == 0:  # skip if none
            continue
        event_cnt = 0  # index events
        # tag trigger
        for event in temp_event_mentions:
            temp_event_type = event['event_type']  # get type
            trigger_position = [event['trigger']['position'][0], event['trigger']['position'][1] + 1]
            trigger_length = trigger_position[1] - trigger_position[0]
            temp_start = trigger_position[0]
            for k in range(trigger_length):
                if k == 0:
                    event_trigger_tag[i][k+temp_start] = ['B-' + temp_event_type + '-' + str(event_cnt)]
                else:
                    event_trigger_tag[i][k+temp_start] = ['I-' + temp_event_type + '-' + str(event_cnt)]
            # tag arguments
            for argument in event['arguments']:
                temp_argument_role = argument['role']
                argument_position = [argument['position'][0], argument['position'][1] + 1]
                argument_length = argument_position[1] - argument_position[0]
                temp_start = argument_position[0]
                for k in range(argument_length):
                    if k == 0:
                        event_argument_tag[i][k + temp_start] += ['B-' + temp_argument_role + '-' + str(event_cnt)]
                    else:
                        event_argument_tag[i][k + temp_start] += ['I-' + temp_argument_role + '-' + str(event_cnt)]
            event_cnt += 1

    for sent in event_argument_tag:  # delete 'O' if token is a named entity
        for token in sent:
            if len(token) > 1:
                del token[0]

    return event_trigger_tag, event_argument_tag
   
    
def get_BIO(path, type_name, save=False):
    with open(path) as f:
        raw_data = json.loads(f.read())
    token = get_sentence_token(raw_data)
    entity_BIO = get_entity_tag(raw_data)
    event_trigger_BIO, event_argument_BIO = get_event_tag(raw_data)
    if save:
        BIO_path = '/'.join(path.split('/')[:-1]) + '/' + 'BIO/'
        type_path = BIO_path + type_name + '/'
        try:
            os.mkdir(BIO_path)
        except:
            pass
        try:
            os.mkdir(type_path)
        except:
            pass
        for name in ['token', 'entity_BIO', 'event_trigger_BIO', 'event_argument_BIO']:
            out_path = type_path + name + '.json'
            with open(out_path, 'w', encoding='utf8') as f:
                f.write(json.dumps(eval(name), indent=4, ensure_ascii=False))

    return token, entity_BIO, event_trigger_BIO, event_argument_BIO


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', type=str, help="Name of the language", default='en',
                        choices=['en', 'ar', 'zh'])
    args = parser.parse_args()
    language = args.lang
    data_path = './output/'
    sentence = input("whether transform to BIO tags(y/n):") == 'y'
    if sentence:
        for type_name in ['train', 'test', 'dev']:
            raw_path = data_path + language + '-' + type_name + '.json'
            _ = get_BIO(raw_path, type_name, save=True)
