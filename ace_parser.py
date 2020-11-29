from xml.etree import ElementTree


class Parser:
    def __init__(self, path):
        self.entity_mentions = []
        self.event_mentions = []
        self.relation_mentions = []
        self.parse_xml(path + '.apf.xml')

    def parse_xml(self, xml_path):
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()
        for child in root[0]:
            if child.tag == 'entity':
                self.entity_mentions.extend(self.parse_entity_tag(child))
            elif child.tag in ['value', 'timex2']:
                self.entity_mentions.extend(self.parse_value_timex_tag(child))
            elif child.tag == 'event':
                self.event_mentions.extend(self.parse_event_tag(child))
            elif child.tag == 'relation':
                self.relation_mentions.extend(self.parse_relation_tag(child))

    @staticmethod
    def parse_entity_tag(node):
        entity_mentions = []

        for child in node:
            if child.tag != 'entity_mention':
                continue
            extent = child[0]
            head = child[1]
            charset = extent[0]
            head_charset = head[0]

            entity_mention = dict()
            entity_mention['entity-id'] = child.attrib['ID']
            entity_mention['entity-type'] = '{}:{}'.format(node.attrib['TYPE'], node.attrib['SUBTYPE'])
            entity_mention['text'] = charset.text
            entity_mention['position'] = [int(charset.attrib['START']), int(charset.attrib['END'])]
            entity_mention["head"] = {"text": head_charset.text,
                                      "position": [int(head_charset.attrib['START']), int(head_charset.attrib['END'])]}

            entity_mentions.append(entity_mention)

        return entity_mentions

    @staticmethod
    def parse_relation_tag(node):
        relation_mentions = []

        for child in node:
            if child.tag != 'relation_mention':
                continue
            extent = child[0]
            charset = extent[0]

            relation_mention = dict()
            relation_mention['relation-id'] = child.attrib['ID']
            relation_mention['relation-type'] = '{}:{}'.format(node.attrib['TYPE'], node.attrib['SUBTYPE'])
            relation_mention['text'] = charset.text
            relation_mention['position'] = [int(charset.attrib['START']), int(charset.attrib['END'])]
            relation_mention['arguments'] = []
            for child2 in child:
                if child2.tag == 'relation_mention_argument':
                    extent = child2[0]
                    charset = extent[0]
                    relation_mention['arguments'].append({
                        'text': charset.text,
                        'position': [int(charset.attrib['START']), int(charset.attrib['END'])],
                        'role': child2.attrib['ROLE'],
                        'entity-id': child2.attrib['REFID'],
                    })
            relation_mentions.append(relation_mention)

        return relation_mentions

    @staticmethod
    def parse_event_tag(node):
        event_mentions = []
        for child in node:
            if child.tag == 'event_mention':
                event_mention = dict()
                event_mention['event-id'] = child.attrib['ID']
                event_mention['event_type'] = '{}:{}'.format(node.attrib['TYPE'], node.attrib['SUBTYPE'])
                event_mention['arguments'] = []
                for child2 in child:
                    if child2.tag == 'ldc_scope':
                        charset = child2[0]
                        event_mention['text'] = charset.text
                        event_mention['position'] = [int(charset.attrib['START']), int(charset.attrib['END'])]
                    if child2.tag == 'anchor':
                        charset = child2[0]
                        event_mention['trigger'] = {
                            'text': charset.text,
                            'position': [int(charset.attrib['START']), int(charset.attrib['END'])],
                        }
                    if child2.tag == 'event_mention_argument':
                        extent = child2[0]
                        charset = extent[0]
                        event_mention['arguments'].append({
                            'text': charset.text,
                            'position': [int(charset.attrib['START']), int(charset.attrib['END'])],
                            'role': child2.attrib['ROLE'],
                            'entity-id': child2.attrib['REFID'],
                        })
                event_mentions.append(event_mention)
        return event_mentions

    @staticmethod
    def parse_value_timex_tag(node):
        entity_mentions = []

        for child in node:
            extent = child[0]
            charset = extent[0]

            entity_mention = dict()
            entity_mention['entity-id'] = child.attrib['ID']

            if 'TYPE' in node.attrib:
                entity_mention['entity-type'] = node.attrib['TYPE']
            if 'SUBTYPE' in node.attrib:
                entity_mention['entity-type'] += ':{}'.format(node.attrib['SUBTYPE'])
            if child.tag == 'timex2_mention':
                entity_mention['entity-type'] = 'TIM:time'

            entity_mention['text'] = charset.text
            entity_mention['position'] = [int(charset.attrib['START']), int(charset.attrib['END'])]

            entity_mention["head"] = {"text": charset.text,
                                      "position": [int(charset.attrib['START']), int(charset.attrib['END'])]}

            entity_mentions.append(entity_mention)

        return entity_mentions
