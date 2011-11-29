from entity import Entity
from datetime import datetime
__author__ = 'snikhil'

class NodeEntity(Entity):

    def __init__(self):
        Entity.__init__(self)

    def analyze(self, nodes):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp in nodes:

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

            if osmversion < self.min_version:
                self.min_version = osmversion


