from datetime import datetime
from com.telenav.openstreetmap.ransm.user import User
from com.telenav.openstreetmap.ransm.entity import Entity
__author__ = 'snikhil'

class NodeEntity(Entity):

    def __init__(self):
        Entity.__init__(self)

    def analyze(self, nodes):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp in nodes:

            self.entity_count += 1
            self.extract_user(tags)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            self.ages.push(osmtimestamp)

