from datetime import datetime
from com.telenav.openstreetmap.ransm.entity import Entity
from com.telenav.openstreetmap.ransm.user import User


__author__ = 'snikhil'

class RelationEntity(Entity):

    def __init__(self):
        Entity.__init__(self)
        self.num_turnrestrcitions = 0

    def analyze(self, relations):
        #callback method for the ways
        for osmid, tags, refs, osmversion, osmtimestamp in relations:
            self.entity_count += 1
            self.extract_user(tags)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            self.ages.push(osmtimestamp)

            if 'type' in tags and tags['type'] == 'restriction':
                self.num_turnrestrcitions += 1

