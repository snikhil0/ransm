'''
Created on Nov 28, 2011

@author: snikhil
'''
from datetime import datetime
from com.telenav.openstreetmap.ransm.entity import Entity
from com.telenav.openstreetmap.ransm.user import User
__author__ = 'snikhil'

class WayEntity(Entity):

    def __init__(self):
        Entity.__init__(self)

    def analyze(self, ways):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp in ways:
            self.entity_count += 1
            self.extract_min_max_id(osmid)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_version(osmversion)
            self.extract_user(tags)
            self.ages.push(osmtimestamp)

