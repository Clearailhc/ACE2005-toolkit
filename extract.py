import os
import json
import string
import argparse
from conllu import parse
from collections import OrderedDict
from tqdm import tqdm
from udpipe import Model

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


def get_file_names(dirpath):
    filenames = []
    for file in os.listdir(dirpath):
        if file.endswith(".conllu"):
            filenames.append(os.path.splitext(file)[0])
    return filenames


def load_json(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data


def load_conllu(conllu_file):
    conllu_data = []
    with open(conllu_file, 'r', encoding='utf-8') as content_file:
        content = content_file.read()
        sentences = parse(content)
        for idx, sentence in enumerate(sentences):
            tokens, upos, head, deprel, offset = [], [], [], [], []
            reserved_offsets = []
            for widx, word in enumerate(sentence):
                if isinstance(word['id'], tuple):
                    # multi-word token, e.g., word['id'] = (4, '-', 5)
                    assert len(word['id']) == 3
                    indices = word['misc']['TokenRange'].split(':')
                    reserved_offsets.append([int(indices[0]), int(indices[1])])
                else:
                    tokens.append(word['form'])
                    upos.append(word['upostag'])
                    head.append(word['head'])
                    deprel.append(word['deprel'])
                    if word['misc'] is not None:
                        # single-word token
                        indices = word['misc']['TokenRange'].split(':')
                        offset.append([int(indices[0]), int(indices[1])])
                    elif len(reserved_offsets) > 0:
                        offset.append(reserved_offsets.pop())
                    else:
                        offset.append([-1, -1])

            assert len(tokens) == len(offset)
            sent_obj = OrderedDict([
                ('id', sentence.metadata['sent_id']),
                ('text', sentence.metadata['text']),
                ('word', tokens),
                ('upos', upos),
                ('head', head),
                ('deprel', deprel),
                ('offset', offset)
            ])
            conllu_data.append(sent_obj)

    return conllu_data


def compare_string_without_space(src_words, tgt_words, ignore_punc=False):
    src_chars = list(' '.join(src_words).replace(" ", ""))
    tgt_chars = list(' '.join(tgt_words).replace(" ", ""))
    if ignore_punc:
        src_chars = [ch for ch in src_chars if ch not in string.punctuation]
        tgt_chars = [ch for ch in tgt_chars if ch not in string.punctuation]
    return src_chars == tgt_chars


def find_span_offset(sentences, text, text_start, text_end, model, lang):
    match_positions = [-1, -1]
    type_of_match_found = ''
    best_sent_id = None
    best_sent = None

    tokenized_text = model.tokenize(text, 'ranges')
    conllu = parse(model.write(tokenized_text, "conllu"))
    text_words = [w['form'] for sent in conllu for w in sent]
    text_len = len(text_words)
    tokenized_text = ' '.join(text_words)

    for sent in sentences:
        best_sent = sent
        best_sent_id = sent['id']
        offsets = sent['offset']
        # TODO: we do not allow spanning across sentences, should we?
        if offsets[0][0] <= text_start and text_end <= offsets[-1][1]:
            start, end = [], []
            for i, tok in enumerate(offsets):
                if tok[0] == text_start:
                    start.append(i)
                if tok[1] == text_end + 1:
                    end.append(i)

            # best case
            if len(start) == 1 and len(end) == 1:
                if start[0] <= end[0]:
                    ent_words = sent['word'][start[0]:end[0] + 1]
                    # we make sure that the character sequence without space matches
                    if compare_string_without_space(text_words, ent_words):
                        type_of_match_found = 'exact_first'
                        match_positions = [start[0], end[0]]
                        break

            # we give another round if either len(start) == 0 or len(end) == 0
            # the conditions are written after exploring the data
            for i, tok in enumerate(offsets):
                if len(start) == 0:
                    if tok[0] == text_start - 1 or tok[0] == text_start + 1:
                        start.append(i)
                if len(end) == 0:
                    if tok[1] == text_end or tok[1] == text_end + 2 or tok[1] == text_end - 1:
                        end.append(i)

            if len(start) == 1 and len(end) == 1:
                if start[0] <= end[0]:
                    ent_words = sent['word'][start[0]:end[0] + 1]
                    if compare_string_without_space(text_words, ent_words):
                        type_of_match_found = 'exact_second'
                        match_positions = [start[0], end[0]]
                        break
                    else:
                        # let's tolerate punctuations for English
                        if lang == 'en' and compare_string_without_space(text_words, ent_words, ignore_punc=True):
                            type_of_match_found = 'exact_second_wo_punc'
                            match_positions = [start[0], end[0]]
                            break

            # after this point, only perform based on text match

            # first try to match the target text with its' original form
            # now, we consider one word and sub-word matches
            one_word_matches = []
            sub_word_matches = []
            one_word_match_dist = []
            sub_word_match_dist = []
            for i in range(len(sent['word'])):
                word = sent['word'][i]
                if word == text:
                    # if the target is 1 word, then perform direct match
                    one_word_matches.append([i, i])
                    one_word_match_dist.append(abs(offsets[i][0] - text_start))
                elif text in word and (len(start) != 0 or len(end) != 0):
                    # this basically performs partial match,
                    # e.g., 'israeli' to 'israeli-palestinian'
                    sub_word_matches.append([i, i])
                    sub_word_match_dist.append(abs(offsets[i][0] - text_start))

            if len(one_word_matches) == 1:
                type_of_match_found = 'one_word_match'
                match_positions = one_word_matches[0]
                break
            elif len(one_word_matches) == 0 and len(sub_word_matches) == 1:
                type_of_match_found = 'sub_word_match'
                match_positions = sub_word_matches[0]
                break
            elif len(one_word_matches) > 0:
                type_of_match_found = 'closest_one_word_match'
                index = one_word_match_dist.index(min(one_word_match_dist))
                match_positions = one_word_matches[index]
                break
            elif len(sub_word_matches) > 0:
                type_of_match_found = 'closest_sub_word_match'
                index = sub_word_match_dist.index(min(sub_word_match_dist))
                match_positions = sub_word_matches[index]
                break

            # let's try to match the target text with its' tokenized form
            tokenized_text_len = len(tokenized_text)
            tokenized_sent_text = ' '.join(sent['word'])

            if tokenized_text in tokenized_sent_text:
                matches = []
                match_dist = []
                for i in range(len(sent['word']) - text_len + 1):
                    match_found = False
                    selected_text = ' '.join(sent['word'][i: i + text_len])
                    if sent['word'][i: i + text_len] == text_words:
                        type_of_match_found = 'tokenized_text_match'
                        match_found = True
                    elif tokenized_text in selected_text:
                        # so, there are matches such as: `my ex` in `my ex's`
                        # `Nashville , Tenn` in `Nashville , Tenn.`
                        selected_text = ' '.join(sent['word'][i: i + text_len])
                        selected_text_len = len(selected_text)
                        for j in range(selected_text_len - tokenized_text_len + 1):
                            if selected_text[j:j + tokenized_text_len] == tokenized_text:
                                type_of_match_found = 'tokenized_partial_text_match'
                                match_found = True
                    if match_found:
                        matches.append([i, i + text_len - 1])
                        match_dist.append(abs(offsets[i][0] - text_start))

                if len(matches) > 0:
                    if len(matches) == 1:
                        match_positions = matches[0]
                    else:
                        index = match_dist.index(min(match_dist))
                        match_positions = matches[index]
                break

    return {
        'best_sent': best_sent,
        'sent_id': best_sent_id,
        'start': match_positions[0],
        'end': match_positions[1]
    }


def find_subspan_offset(sent, offset, text, text_start, text_end, model):
    ent_start, ent_end = offset
    start, end = [], []
    for i in range(ent_start, ent_end + 1):
        offset = sent['offset'][i]
        if offset[0] == text_start:
            start.append(i)
        if offset[1] == text_end + 1:
            end.append(i)

    # best case
    if len(start) == 1 and len(end) == 1:
        if start[0] <= end[0]:
            return [start[0], end[0]]

    # we give another round if either len(start) == 0 or len(end) == 0
    # the conditions are written after exploring the data
    for i in range(ent_start, ent_end + 1):
        offset = sent['offset'][i]
        if len(start) == 0:
            if offset[0] == text_start - 1 or offset[0] == text_start + 1:
                start.append(i)
        if len(end) == 0:
            if offset[1] == text_end or offset[1] == text_end + 2 or offset[1] == text_end - 1:
                end.append(i)

    if len(start) == 1 and len(end) == 1:
        if start[0] <= end[0]:
            return [start[0], end[0]]

    # first try to match the target text with its' original form
    # now, we consider one word and sub-word matches
    one_word_matches = []
    sub_word_matches = []
    one_word_match_dist = []
    sub_word_match_dist = []
    for i in range(ent_start, ent_end + 1):
        offset = sent['offset'][i]
        word = sent['word'][i]
        if word == text:
            # if the target is 1 word, then perform direct match
            one_word_matches.append([i, i])
            one_word_match_dist.append(abs(offset[0] - text_start))
        elif text in word and (len(start) != 0 or len(end) != 0):
            # this basically performs partial match,
            # e.g., 'israeli' to 'israeli-palestinian'
            sub_word_matches.append([i, i])
            sub_word_match_dist.append(abs(offset[0] - text_start))

    if len(one_word_matches) == 1:
        return one_word_matches[0]
    elif len(one_word_matches) == 0 and len(sub_word_matches) == 1:
        return sub_word_matches[0]
    elif len(one_word_matches) > 0:
        index = one_word_match_dist.index(min(one_word_match_dist))
        return one_word_matches[index]
    elif len(sub_word_matches) > 0:
        index = sub_word_match_dist.index(min(sub_word_match_dist))
        return sub_word_matches[index]

    # let's try to match the target text with its' tokenized form
    tokenized_text = model.tokenize(text, 'ranges')
    conllu = parse(model.write(tokenized_text, "conllu"))
    text_words = [w['form'] for sent in conllu for w in sent]
    text_len = len(text_words)
    tokenized_text = ' '.join(text_words)
    tokenized_text_len = len(tokenized_text)

    entity_words = sent['word'][ent_start: ent_end + 1]
    tokenized_sent_text = ' '.join(entity_words)

    if tokenized_text in tokenized_sent_text:
        matches = []
        match_dist = []
        for i in range(len(entity_words) - text_len + 1):
            offset = sent['offset'][i]
            match_found = False
            selected_text = ' '.join(entity_words[i: i + text_len])
            if entity_words[i: i + text_len] == text_words:
                match_found = True
            elif tokenized_text in selected_text:
                # so, there are matches such as: `my ex` in `my ex's`
                # `Nashville , Tenn` in `Nashville , Tenn.`
                selected_text = ' '.join(entity_words[i: i + text_len])
                selected_text_len = len(selected_text)
                for j in range(selected_text_len - tokenized_text_len + 1):
                    if selected_text[j:j + tokenized_text_len] == tokenized_text:
                        match_found = True
            if match_found:
                matches.append([i + ent_start, i + ent_start + text_len - 1])
                match_dist.append(abs(offset[0] - text_start))

        if len(matches) > 0:
            if len(matches) == 1:
                return matches[0]
            else:
                index = match_dist.index(min(match_dist))
                return matches[index]

    return [-1, -1]


# An Entity example is as follows.
# {
# 	"entity-id": "AFP_ENG_20030304.0250-E1-3",
# 	"entity-type": "ORG:Medical-Science",
# 	"text": "The Davao Medical Center",
# 	"position": [493, 516],
# 	"head": {
# 		"text": "Davao Medical Center",
# 		"position": [497, 516]
# 	}
# }
def correct_entities(list_of_entity, sentences, lang, model):
    corrected_entities = []
    skipped, dropped, wrong_head = 0, 0, 0
    for entity in list_of_entity:
        if entity['entity-type'] == 'TIM:time':
            skipped += 1
            continue
        new_entity = dict()
        new_entity['entity-id'] = entity['entity-id']
        new_entity['entity-type'] = entity['entity-type']
        new_entity['text'] = entity['text']
        entity_offset = find_span_offset(sentences,
                                         entity['text'],
                                         entity['position'][0],
                                         entity['position'][1],
                                         model, lang)
        if entity_offset['start'] != -1:
            head_offset = find_subspan_offset(entity_offset['best_sent'],
                                              [entity_offset['start'],
                                               entity_offset['end']],
                                              entity['head']['text'],
                                              entity['head']['position'][0],
                                              entity['head']['position'][1],
                                              model)
            if head_offset[0] != -1:
                if head_offset[0] < entity_offset['start'] or \
                        head_offset[0] > entity_offset['end']:
                    head_offset[0] = -1
                    wrong_head += 1
                if head_offset[1] < entity_offset['start'] or \
                        head_offset[1] > entity_offset['end']:
                    head_offset[1] = -1
                    wrong_head += 1

            if head_offset[0] == -1 or head_offset[1] == -1:
                wrong_head += 1
                dropped += 1
                continue

            new_entity['sent_id'] = entity_offset['sent_id']
            new_entity['position'] = [entity_offset['start'], entity_offset['end']]
            new_entity['head'] = {
                'text': entity['head']['text'],
                'position': [head_offset[0], head_offset[1]]
            }
            corrected_entities.append(new_entity)
        else:
            dropped += 1

    return corrected_entities, dropped, skipped, wrong_head


# An Event example is as follows.
# {
# 	"event-id": "AFP_ENG_20030304.0250-EV1-1",
# 	"event_type": "Life:Die",
# 	"arguments": [
# 		{
# 			"text": "At least 19 people",
# 			"position": [181, 198],
# 			"role": "Victim",
# 			"entity-id": "AFP_ENG_20030304.0250-E24-29"
# 		},
# 		{
# 			"text": "southern Philippines airport",
# 			"position": [253, 280],
# 			"role": "Place",
# 			"entity-id": "AFP_ENG_20030304.0250-E26-32"
# 		},
# 		{
# 			"text": "Tuesday",
# 			"position": [243, 249],
# 			"role": "Time-Within",
# 			"entity-id": "AFP_ENG_20030304.0250-T2-1"
# 		}
# 	],
# 	"text": "At least 19 people were killed and 114 people were wounded in\nTuesday's southern
# 	Philippines airport blast, officials said, but\nreports said the death toll could climb to 30",
# 	"position": [181, 353],
# 	"trigger": {
# 		"text": "killed",
# 		"position": [205, 210]
# 	}
# }
def correct_events(list_of_events, list_of_entities, sentences, lang, model):
    entities = dict()
    for entity in list_of_entities:
        entities[entity['entity-id']] = entity

    corrected_events = []
    dropped, wrong_trigger = 0, 0
    for event in list_of_events:
        new_event = dict()
        new_event['event-id'] = event['event-id']
        new_event['event_type'] = event['event_type']
        new_event['arguments'] = []
        for argument in event['arguments']:
            if argument['entity-id'] in entities:
                entity = entities[argument['entity-id']]
                new_event['arguments'].append({
                    'text': argument['text'],
                    'sent_id': entity['sent_id'],
                    'position': entity['position'],
                    'role': argument['role'],
                    'entity-id': argument['entity-id']
                })

        new_event['text'] = event['text']
        event_offset = find_span_offset(sentences,
                                        event['text'],
                                        event['position'][0],
                                        event['position'][1],
                                        model, lang)

        if event_offset['start'] != -1:
            trigger_offset = find_subspan_offset(event_offset['best_sent'],
                                                 [event_offset['start'],
                                                  event_offset['end']],
                                                 event['trigger']['text'],
                                                 event['trigger']['position'][0],
                                                 event['trigger']['position'][1],
                                                 model)

            if trigger_offset[0] != -1:
                if trigger_offset[0] < event_offset['start'] or \
                        trigger_offset[0] > event_offset['end']:
                    trigger_offset[0] = -1
                    wrong_trigger += 1
                if trigger_offset[1] < event_offset['start'] or \
                        trigger_offset[1] > event_offset['end']:
                    trigger_offset[1] = -1
                    wrong_trigger += 1

            if trigger_offset[0] == -1 or trigger_offset[1] == -1:
                wrong_trigger += 1
                dropped += 1
                continue

            new_event['sent_id'] = event_offset['sent_id']
            new_event['position'] = [event_offset['start'], event_offset['end']]
            new_event['trigger'] = {
                'text': event['trigger']['text'],
                'position': [trigger_offset[0], trigger_offset[1]]
            }
            corrected_events.append(new_event)
        else:
            dropped += 1

    return corrected_events, dropped, wrong_trigger


def correct_relations(list_of_relations, list_of_entities, sentences, lang, model):
    entities = dict()
    for entity in list_of_entities:
        entities[entity['entity-id']] = entity

    corrected_relations = []
    dropped = 0
    for relation in list_of_relations:
        new_relation = dict()
        new_relation['relation-id'] = relation['relation-id']
        new_relation['relation-type'] = relation['relation-type']
        new_relation['text'] = relation['text']

        relation_offset = find_span_offset(sentences,
                                           relation['text'],
                                           relation['position'][0],
                                           relation['position'][1],
                                           model, lang)

        if relation_offset['start'] != -1:
            new_relation['sent_id'] = relation_offset['sent_id']
            new_relation['position'] = [relation_offset['start'], relation_offset['end']]
            new_relation['arguments'] = []
            for argument in relation['arguments']:
                if argument['entity-id'] in entities:
                    entity = entities[argument['entity-id']]
                    new_relation['arguments'].append({
                        'text': argument['text'],
                        'sent_id': entity['sent_id'],
                        'position': entity['position'],
                        'role': argument['role'],
                        'entity-id': argument['entity-id']
                    })
            corrected_relations.append(new_relation)
        else:
            dropped += 1

    return corrected_relations, dropped


def modify_files(opt, split):
    target_dir = os.path.join(opt.data, split)
    filenames = get_file_names(target_dir)
    ent, ent_dropped, ent_skipped, ent_wrong_head = 0, 0, 0, 0
    eve, eve_dropped, eve_wrong_trigger = 0, 0, 0
    rel, rel_dropped = 0, 0
    model = Model(model_map[opt.lang])
    for filename in tqdm(filenames, total=len(filenames)):
        sentences = load_conllu(os.path.join(target_dir, '{}.conllu'.format(filename)))
        jsonObj = load_json(os.path.join(target_dir, '{}.v1.json'.format(filename)))

        modified_entities, dropped, skipped, wrong_head = correct_entities(jsonObj['entities'],
                                                                           sentences,
                                                                           opt.lang,
                                                                           model)
        ent_dropped += dropped
        ent_skipped += skipped
        ent_wrong_head += wrong_head
        ent += len(jsonObj['entities'])

        modified_events, dropped, wrong_trigger = correct_events(jsonObj['events'],
                                                                 modified_entities,
                                                                 sentences,
                                                                 opt.lang,
                                                                 model)
        eve_dropped += dropped
        eve_wrong_trigger += wrong_trigger
        eve += len(jsonObj['events'])

        modified_relations, dropped = correct_relations(jsonObj['relations'],
                                                        modified_entities,
                                                        sentences,
                                                        opt.lang,
                                                        model)
        rel_dropped += dropped
        rel += len(jsonObj['relations'])

        with open(os.path.join(target_dir, '{}.v2.json'.format(filename)), 'w') as fw:
            json.dump(OrderedDict([
                ('entities', modified_entities),
                ('events', modified_events),
                ('relations', modified_relations)
            ]), fw)

    print('[Entities] Total {:>5}, Skipped {:>4}, Dropped {:>4}, Wrong-Head {:>2}.'.format(
        ent, ent_skipped, ent_dropped, ent_wrong_head))
    print('[Events] Total {:>5}, Dropped {:>4}, Wrong-Trigger {:>2}.'.format(
        eve, eve_dropped, eve_wrong_trigger))
    print('[Relations] Total {:>5}, Dropped {:>4}.'.format(rel, rel_dropped))


def main(args):
    args.data = os.path.join(args.data, lang_name[args.lang])
    print('--' * 10 + ' Train ' + '--' * 10)
    modify_files(args, 'train')
    print('--' * 10 + ' Dev ' + '--' * 10)
    modify_files(args, 'dev')
    print('--' * 10 + ' Test ' + '--' * 10)
    modify_files(args, 'test')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='./processed-data/',
                        help="Path of ACE2005 data")
    parser.add_argument('--lang', type=str, help="Name of the language", default='en',
                        choices=['en', 'ar', 'zh'])
    args = parser.parse_args()
    print('\n' + '*' * 20 + lang_name[args.lang] + '*' * 20 + '\n')
    main(args)
