from ransm.entity import Entity
from ransm.entity_action import IEntityAction
__author__ = 'snikhil'

class NodeEntity(Entity, IEntityAction):

    def __init__(self):
        pass

    def analyze(self, nodes):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp in nodes:

            self.entity_count += 1

            if osmtimestamp > self.last_timestamp:
                self.last_timestamp = osmtimestamp

            if osmtimestamp < self.first_timestamp:
                self.first_timestamp = osmtimestamp

            if osmid > self.maxid:
                self.maxid = osmid

            if osmid < self.minid:
                self.minid = osmid

            if osmversion > self.max_version:
                self.max_version = osmversion

            if osmversion < self.min_version:
                self.min_version = osmversion


