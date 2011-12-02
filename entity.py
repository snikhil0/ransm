import sys
from datetime import datetime
from user import  User

class Entity(object):

    def __init__(self):
        self.entity_count = 0
        self.min_version = sys.maxint
        self.max_version = 0
        self.mean_version = 0
        self.first_timestamp = datetime.max
        self.last_timestamp = datetime.min
        self.maxid = 0
        self.minid = sys.maxint
        self.users = {}
        self.ages = []

    def average_age(self):
        return sum(self.ages, 0.0) / len(self.ages)

    def extract_user(self, uid, type):
        if uid not in self.users:
            self.users[uid] = User(uid, str(uid))
        else:
            self.users[uid].increment(type)

    def extract_min_max_timestamp(self, osmtimestamp):
        timestamp = datetime.utcfromtimestamp(osmtimestamp)
        if timestamp > self.last_timestamp:
            self.last_timestamp = timestamp
        if timestamp < self.first_timestamp:
            self.first_timestamp = timestamp

    def extract_min_max_id(self, osmid):
        if osmid > self.maxid:
            self.maxid = osmid
        if osmid < self.minid:
            self.minid = osmid

    def extract_min_max_lat_lon(self, lon, lat):
        if lon > self.max_lon:
            self.max_lon = lon
        if lon < self.min_lon:
            self.min_lon = lon
        if lat < self.min_lat:
            self.min_lat = lat
        if lat > self.max_lat:
            self.max_lat = lat

    def extract_min_max_version(self, osmversion):
        if osmversion > self.max_version:
            self.max_version = osmversion
        if osmversion < self.min_version:
            self.min_version = osmversion

class CoordEntity(Entity):

    def __init__(self):
        Entity.__init__(self)
        self.min_lat = self.min_lon = float(-180.0)
        self.max_lat = self.max_lon = float(180.0)


    def analyze(self, coord):
        for osmid, lon, lat, osmversion, osmtimestamp, osmuid in coord:
            self.entity_count += 1
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_lat_lon(lon, lat)
            self.extract_min_max_version(osmversion)

class NodeEntity(Entity):

    def __init__(self):
        Entity.__init__(self)

    def analyze(self, nodes):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in nodes:
            self.entity_count += 1
            self.extract_user(osmuid, 'nodes')
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            self.ages.append(float(osmtimestamp/1000.0))

class RelationEntity(Entity):

    def __init__(self):
        Entity.__init__(self)
        self.num_turnrestrcitions = 0

    def analyze(self, relations):
        #callback method for the ways
        for osmid, tags, refs, osmversion, osmtimestamp, osmuid in relations:
            self.entity_count += 1
            self.extract_user(osmuid, 'relations')
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            self.ages.append(float(osmtimestamp/1000.0))

            if 'type' in tags and tags['type'] == 'restriction':
                self.num_turnrestrcitions += 1
                
class WayEntity(Entity):

    def __init__(self):
        Entity.__init__(self)
        self.tigerbreakdown = {}
        self.tiger_tagged_ways = 0
        self.untouched_by_user_edits = 0
        self.version_increase_over_tiger = 0
        self.sum_versions = 0

    def analyze(self, ways):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in ways:
            self.entity_count += 1
            self.extract_min_max_id(osmid)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_version(osmversion)
            self.extract_user(osmuid, 'ways')
            self.ages.append(float(osmtimestamp/1000.0))

            if 'tiger:tlid' in tags:
                tigerTagValue = tags['tiger:tlid']
                self.tiger_tagged_ways += 1
                if tigerTagValue not in self.tigerbreakdown:
                    self.tigerbreakdown[tigerTagValue] = 1
                else:
                    self.tigerbreakdown[tigerTagValue] += 1
                if osmversion == 1:
                    self.untouched_by_user_edits += 1

                self.version_increase_over_tiger += (osmversion - 1)
                self.sum_versions += osmversion


                


