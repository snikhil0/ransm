from ransm.entity import Entity
from ransm.entity_action import IEntityAction
from datetime import datetime

__author__ = 'snikhil'

class RelationEntity(Entity, IEntityAction):

    def __init__(self):
        self.num_turnrestrcitions = 0

    def analyze(self, relations):
        #callback method for the ways
        for osmid, tags, refs, osmversion, osmtimestamp in relations:
            self.entity_count += 1
            timestamp = datetime.utcfromtimestamp(osmtimestamp)

            if timestamp > self.last_timestamp:
                self.last_timestamp = timestamp

            if timestamp < self.first_timestamp:
                self.first_timestamp = timestamp

            if osmid > self.maxid:
                self.maxid = osmid

            if osmid < self.minid:
                self.minid = osmid

            if osmversion > self.max_version:
                self.max_version = osmversion

            if 'type' in tags and tags['type'] == 'restriction':
                self.num_turnrestrcitions += 1

