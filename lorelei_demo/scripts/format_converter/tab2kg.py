import argparse
import json
from collections import OrderedDict


def tab2kg(tab_string):
    kg = KnowledgeGraph()
    entities = OrderedDict()
    for line in tab_string.splitlines():
        line = line.split('\t')
        entity_mention_head = line[2]
        entity_mention_offset = line[3]
        entity_mention_type = line[6]
        try:
            entity_mention_token_offset = line[8]
            entity_mention_translation = [item.split('#') for item in
                                          line[9].split('|')]
            entity_mention_transliteration = [item.split('#') for item in
                                              line[10].split('|')]
        except IndexError:
            entity_mention_token_offset = ''
            entity_mention_translation = ''
            entity_mention_transliteration = ''

        try:
            entities[entity_mention_head] += 1

        except KeyError:
            entities[entity_mention_head] = 1
            entity_id = "ELISA_IE_Entity_%s" % \
                        str(list(entities.keys()).index(
                            entity_mention_head) + 1).zfill(
                            5)  # entity id starts from 1
            entity_type = line[5]
            kg.add_entity(entity_id, entity_type, [])

        entity_mention_id = "ELISA_IE_Entity_%s-%s" % (
            str(list(entities.keys()).index(entity_mention_head) + 1).zfill(5),
            str(entities[entity_mention_head]))

        kg.add_entity_mention(entity_mention_id, entity_mention_offset,
                              entity_mention_head, entity_mention_type,
                              entity_mention_token_offset,
                              entity_mention_translation,
                              entity_mention_transliteration)

    return kg.to_json()


class KnowledgeGraph(object):
    def __init__(self):
        self.attribute = []
        self.entity_mention = []
        self.entity = []
        self.event_mention = []
        self.event = []
        self.relation = []

    def to_json(self):
        d = dict()
        d['attribute'] = [item.to_dict() for item in self.attribute]
        d['entity_mention'] = [item.to_dict() for item in self.entity_mention]
        d['entity'] = [item.to_dict() for item in self.entity]
        d['event_mention'] = [item.to_dict() for item in self.event_mention]
        d['event'] = [item.to_dict() for item in self.event]
        d['relation'] = [item.to_dict() for item in self.relation]
        return json.dumps(d, indent=4, sort_keys=True, ensure_ascii=False)  # pretty print json

    def add_entity_mention(self, mention_id, docid_offsets, mention_head, mention_type,
                           entity_mention_token_offset, entity_mention_translation, entity_mention_transliteration):
        self.entity_mention.append(EntityMention(mention_id, docid_offsets, mention_head, mention_type,
                                                 entity_mention_token_offset, entity_mention_translation,
                                                 entity_mention_transliteration))

    def add_attribute(self, attribute_id, attribute_type, docid_offset, attribute_head, attribute_value):
        self.attribute.append(Attribute(attribute_id, attribute_type, docid_offset, attribute_head, attribute_value))

    def add_entity(self, entity_id, entity_type, attributes):
        self.entity.append(Entity(entity_id, entity_type, attributes))

    def add_event_mention(self, mention_id, event_offsets, event_extent, trigger_offsets, trigger, arguments):
        self.event_mention.append(EventMention(mention_id, event_offsets, event_extent,
                                               trigger_offsets, trigger, arguments))

    def add_event(self, event_id, event_type, arguments):
        self.event.append(Event(event_id, event_type, arguments))

    def add_relation(self, relation_id, relation_type, arguments):
        self.relation.append(Relation(relation_id, relation_type, arguments))


class Attribute(object):
    def __init__(self, attribute_id, attribute_type, docid_offset, attribute_head, attribute_value):
        self.attribute_id = attribute_id
        self.attribute_type = attribute_type
        self.docid_offset = docid_offset
        self.attribute_head = attribute_head
        self.attribute_value = attribute_value

    def to_dict(self):
        d = dict()
        d['attribute_id'] = self.attribute_id
        d['attribute_type'] = self.attribute_type
        d['docid_offset'] = self.docid_offset
        d['attribute_head'] = self.attribute_head
        d['attribute_value'] = self.attribute_value
        return d


class EntityMention(object):
    def __init__(self, mention_id, docid_offsets, mention_head, mention_type, mention_token_offset,
                 mention_translation, mention_transliteration):
        self.mention_id = mention_id
        self.docid_offsets = docid_offsets
        self.mention_head = mention_head
        self.mention_type = mention_type
        self.mention_token_offset = mention_token_offset
        self.mention_translation = mention_translation
        self.mention_transliteration = mention_transliteration

    def to_dict(self):
        d = dict()
        d['mention_id'] = self.mention_id
        d['docid:offsets'] = self.docid_offsets
        d['mention_head'] = self.mention_head
        d['mention_type'] = self.mention_type
        d['sentenceid:tokenindexes'] = self.mention_token_offset
        d['translations'] = self.mention_translation
        d['transliterations'] = self.mention_transliteration

        return d


class Entity(object):
    def __init__(self, entity_id, entity_type, attributes):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.attributes = attributes

    def to_dict(self):
        d = dict()
        d['entity_id'] = self.entity_id
        d['entity_type'] = self.entity_type
        d['attributes'] = self.attributes
        return d


class EventMention(object):
    def __init__(self, mention_id, event_offsets, event_extent, trigger_offsets, trigger, arguments):
        self.mention_id = mention_id
        self.event_offsets = event_offsets
        self.event_extent = event_extent
        self.trigger_offsets = trigger_offsets
        self.trigger = trigger
        self.arguments = arguments

    def to_dict(self):
        d = dict()
        d['mention_id'] = self.mention_id
        d['event_offsets'] = self.event_offsets
        d['event_extent'] = self.event_extent
        d['trigger_offsets'] = self.trigger_offsets
        d['trigger'] = self.trigger
        d['arguments'] = self.arguments
        return d


class Event(object):
    def __init__(self, event_id, event_type, arguments):
        self.event_id = event_id
        self.event_type = event_type
        self.arguments = arguments

    def to_dict(self):
        d = dict()
        d['event_id'] = self.event_id
        d['event_type'] = self.event_type
        d['arguments'] = self.arguments
        return d


class Relation(object):
    def __init__(self, relation_id, relation_type, arguments):
        self.relation_id = relation_id
        self.relation_type = relation_type
        self.arguments = arguments

    def to_dict(self):
        d = dict()
        d['relation_id'] = self.relation_id
        d['relation_type'] = self.relation_type
        d['arguments'] = self.arguments
        return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('tab_file')
    parser.add_argument('kg_file')
    args = parser.parse_args()

    tab_str = open(args.tab_file).read()

    kg_str = tab2kg(tab_str)

    with open(args.kg_file, 'w') as f:
        f.write(kg_str)



