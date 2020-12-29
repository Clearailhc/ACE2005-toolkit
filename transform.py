import json
import pandas as pd
import numpy as np
import random
import argparse

lang_name = {
    'en': 'English',
    'ar': 'Arabic',
    'zh': 'Chinese'
}

def load_file_list(language='en', name='train'):
    file_list_path = 'filelist/ace.' + language + '.' + name + '.txt'
    file_list = []
    with open(file_list_path) as f:
        for line in f.readlines():
            file_name = line.split('.sgm')[0].split(r'/')[-1]
            file_list.append(file_name)
    return file_list


def load_processed_data(file_list, language='English', name='train'):
    data = []
    # 读取句子和tokens
    for file in file_list:
        doc_data = []
        conll_path = r'cache_data/' + language + '/' + name + '/' + file + '.conllu'
        with open(conll_path) as f:
            conll_list = f.read().split('\n\n')
            for conll in conll_list:
                include_flag = 0  # 是否记录标记
                for i in range(len(conll.split('\n'))):
                    if 'sent_id = ' in conll.split('\n')[i]:
                        temp = dict()
                        temp['sent_id'] = conll.split('\n')[i].split()[-1]
                        temp['sentence'] = conll.split('\n')[i + 1][9:]
                        if len(temp['sentence'].split()) >= 5:  # TODO仅保留单词数大于5的句子
                            include_flag = 1  # 是否记录标记
                        elif language == 'Chinese':
                            include_flag = 1  # 对于中文，因为没有分词长度，所以全部保留
                        break
                if include_flag:
                    temp['tokens'] = []
                    for j in range(len(conll.split('\n')))[i + 2:]:
                        temp['tokens'].append(conll.split('\n')[j].split()[1])
                    doc_data.append(temp)

        # 读取entity, event, relation
        file_path = r'cache_data/' + language + '/' + name + '/' + file + '.v2.json'
        with open(file_path) as f:
            v2_data = json.loads(f.read())
            for sentence in doc_data:
                sent_id = sentence['sent_id']
                sentence['golden-entity-mentions'] = []  # 添加实体
                sentence['golden-event-mentions'] = []  # 添加事件
                sentence['golden-relation-mentions'] = []  # 添加关系
                for entity in v2_data['entities']:
                    if entity['sent_id'] == sent_id:
                        sentence['golden-entity-mentions'].append(entity)
                for event in v2_data['events']:
                    if event['sent_id'] == sent_id:
                        sentence['golden-event-mentions'].append(event)
                for relation in v2_data['relations']:
                    if relation['sent_id'] == sent_id:
                        sentence['golden-relation-mentions'].append(relation)
                del sentence['sent_id']  # 删除sent_id
        data += doc_data
    return data


def count_type(language='English'):
    """统计每个事件类型的数目"""
    event_type = ['O', 'Life:Be-Born', 'Life:Marry', 'Life:Divorce', 'Life:Injure', 'Life:Die', 'Movement:Transport',
                  'Transaction:Transfer-Ownership', 'Transaction:Transfer-Money',
                  'Business:Start-Org', 'Business:Merge-Org', 'Business:Declare-Bankruptcy', 'Business:End-Org',
                  'Conflict:Attack', 'Conflict:Demonstrate',
                  'Contact:Meet', 'Contact:Phone-Write',
                  'Personnel:Start-Position', 'Personnel:End-Position', 'Personnel:Nominate', 'Personnel:Elect',
                  'Justice:Arrest-Jail', 'Justice:Release-Parole', 'Justice:Trial-Hearing', 'Justice:Charge-Indict',
                  'Justice:Sue', 'Justice:Convict', 'Justice:Sentence', 'Justice:Fine', 'Justice:Execute',
                  'Justice:Extradite', 'Justice:Acquit', 'Justice:Appeal', 'Justice:Pardon']
    file_name = []
    all_count = []
    for name in ['train', 'dev', 'test']:
        file_list = load_file_list(language='en', name=name)
        for file in file_list:
            file_name.append(file)  # 扩充文件名
            event_count = [0] * 34

            # 计算文本中句子数目
            doc_sent_len = 0
            conll_path = r'cache_data/' + language + '/' + name + '/' + file + '.conllu'
            with open(conll_path) as f:
                conll_list = f.read().split('\n\n')
                for conll in conll_list:
                    for i in range(len(conll.split('\n'))):
                        if 'sent_id = ' in conll.split('\n')[i]:
                            temp = dict()
                            temp['sent_id'] = conll.split('\n')[i].split()[-1]
                            temp['sentence'] = conll.split('\n')[i + 1][9:]
                            if len(temp['sentence'].split()) >= 5:  # TODO仅保留单词数大于5的句子
                                doc_sent_len += 1
                            break

            file_path = r'cache_data/' + language + '/' + name + '/' + file + '.v2.json'
            with open(file_path) as f:
                v2_data = json.loads(f.read())
            for event in v2_data['events']:
                event_count[event_type.index(event['event_type'])] += 1
            event_count[0] = doc_sent_len - sum(event_count)
            all_count.append(event_count)
    type_matrix = np.array(all_count)
    type_dict = {}
    for i in range(len(event_type)):
        type_dict[event_type[i]] = type_matrix[:, i].tolist()
    type_df = pd.DataFrame.from_dict(type_dict, columns=file_name, orient='index')
    type_df = pd.DataFrame(type_df.values.T, index=type_df.columns, columns=type_df.index)
    type_df.to_csv('doc_type.csv')


def save_data(data, path):
    with open(path, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False) + '\n')


def print_count(data):
    len_data = len(data)
    count = 0
    multi_event_sent_count = 0
    multi_same_event_sent_count = 0
    for con in data:
        count += len(con["golden-event-mentions"])
        if len(con["golden-event-mentions"]) > 1:
            multi_event_sent_count += 1
            event_type = [event["event_type"] for event in con["golden-event-mentions"]]
            if len(set(event_type)) != len(event_type):
                multi_same_event_sent_count += 1
    print('[Total Sentence:] %d, [Total Event:]%d,\n [Multi-event-sentence:] %d, [Multi-same-event-sentence:] %d'
          % (len_data, count, multi_event_sent_count, multi_same_event_sent_count))


def data_split(all_data, rate=[0.8, 0.1, 0.1]):
    data_len = len(all_data)
    split_count = np.array(rate) * data_len
    random.shuffle(all_data)
    train = all_data[:int(split_count[0])]
    dev = all_data[int(split_count[0]): int(split_count[0] + split_count[1])]
    test = all_data[int(split_count[0] + split_count[1]):]
    # for name in ['train', 'dev', 'test']:
    #     print('++++++%s summary++++++' % name)
    #     print_count(eval(name))
    return train, dev, test


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', type=str, help="Name of the language", default='en',
                        choices=['en', 'ar', 'zh'])
    args = parser.parse_args()
    language = lang_name[args.lang]
    all_data = []
    for name in ['train', 'dev', 'test']:
        file_list = load_file_list(language=args.lang, name=name)
        temp_data = load_processed_data(file_list, language=language, name=name)
        globals()[name] = temp_data
        all_data += temp_data
    sentence = input("whether divide by sentence level(y/n):") == 'y'
    if sentence:
        rate = [float(i) for i in input("input the train/dev/test rate:").split()]
        assert sum(rate) == 1 and len(rate) == 3, "wrong rates!"
        train, dev, test = data_split(all_data, rate)

    for name in ['train', 'dev', 'test']:
        save_path = r'output/' + str(args.lang) + '-' + name + '.json'
        print("-" * 20 + ' ' + name + ' ' + "-" * 20)
        print_count(eval(name))
        save_data(eval(name), save_path)
