import sys
from datetime import datetime
from user import  User
from math import *

EARTH_RADIUS_IN_MILES = 3963.19
ROAD_CATEGORY = {'motorway': 'highways', 'trunk':'main', 'primary':'main', 'secondary':'local',
                     'tertiary': 'local', 'residential':'local', 'unclassified': 'unclassified', 'road':'unclassified',
                     'living_street': 'local', 'service': 'local', 'track':'local', 'pedestrian':'local',
                     'raceway':'local', 'services':'local', 'rest_area':'local', 'bus_guideway':'local',
                     'path':'local', 'cycleway':'guidance', 'footway':'guidance', 'mini_roundabout':'guidance',
                     'stop':'guidance', 'give_way':'guidance', 'traffic_signals':'guidance',
                     'crossing':'guidance', 'roundabout':'guidance', 'motorway_junction':'guidance',
                     'turning_circle':'guidance', 'construction':'guidance', 'motorway_link':'local',
                     'trunk_link':'local', 'primary_link':'local', 'secondary_link':'local',
                     'tertiary_link':'local'}

ONE_WAY_WEIGHT = 0.4
MAX_SPEED_WEIGHT = 0.6

UNTOUCHED_WEIGHT = -0.3
VERSION_INCREASE_OVER_TIGER = 0.7

LENGTH_COST = 0.2
ROUTING_COST = 0.4
JUNCTION_COST = 0.15
TIGER_COST = 0.25

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
        self.nodes = {}

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
    def __init__(self, nodecache):
        Entity.__init__(self)
        self.min_lat = self.min_lon = float(-180.0)
        self.max_lat = self.max_lon = float(180.0)
        self.nodecache = nodecache

    def analyze(self, coord):
        for osmid, lon, lat, osmversion, osmtimestamp, osmuid in coord:
            self.entity_count += 1
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_lat_lon(lon, lat)
            self.extract_min_max_version(osmversion)
            self.nodecache[osmid] = (lon,lat)

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
            self.ages.append(float(osmtimestamp / 1000.0))
            if osmid not in self.nodes:
                self.nodes[osmid] = (ref[0], ref[1])


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
            self.ages.append(float(osmtimestamp / 1000.0))

            if 'type' in tags and tags['type'] == 'restriction':
                self.num_turnrestrcitions += 1


class RoutingCost(Entity):
    length = 0

    def __init__(self):
        Entity.__init__(self)
        self.tigerbreakdown = {}
        self.tiger_tagged_ways = 0
        self.untouched_by_user_edits = 0
        self.version_increase_over_tiger = 0
        self.sum_versions = 0
        self.sum_way_lengths = 0
        self.sum_one_way_lengths = 0
        self.sum_max_speed_lengths = 0
        self.number_of_junctions = 0

    def tiger_cost(self):
        # Refactor later to compute temps from different sources and fuze them
        datatemp_untouched_by_users = UNTOUCHED_WEIGHT * float(self.untouched_by_user_edits)/self.tiger_tagged_ways
        datatemp_version_increase_over_tiger = VERSION_INCREASE_OVER_TIGER * float(self.version_increase_over_tiger)/self.sum_versions
        tiger_contributed_datatemp = datatemp_untouched_by_users + datatemp_version_increase_over_tiger
        return  tiger_contributed_datatemp

    def routing_cost(self):
        # routing features normalized by way distances
        if not self.sum_one_way_lengths:
            return 0
        datatemp_oneway = float(self.sum_one_way_lengths)/self.sum_way_lengths
        datatemp_maxspeed = float(self.sum_max_speed_lengths)/self.sum_way_lengths
        return ONE_WAY_WEIGHT * datatemp_oneway + MAX_SPEED_WEIGHT * datatemp_maxspeed

    def junction_cost(self):
        return self.number_of_junctions/self.entity_count

class WayEntity(Entity):
    def __init__(self, nodecache):
        Entity.__init__(self)
        self.refs = []
        self.nodecache = nodecache
        self.way_length_map = {}
        self.costmodel = {} #key is road category, value is routing cost model
        self.RCM = RoutingCost()
        self.uncommon_highway_count = 0
        self.uncommon_highway_length = 0

        
    def attribute_cost(self, road_category):
        if road_category not in ROAD_CATEGORY.values():
            return 0
        road_feature = self.costmodel[road_category]
        length_cost = float(road_feature.sum_way_lengths)/self.RCM.sum_way_lengths
        routing_cost = road_feature.routing_cost()
        junction_cost = road_feature.junction_cost()
        tiger_cost = road_feature.tiger_cost()

        return length_cost * LENGTH_COST + routing_cost * ROUTING_COST + \
               junction_cost * JUNCTION_COST + tiger_cost * TIGER_COST


    def analyze(self, ways):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in ways:
            self.entity_count += 1
            self.refs = ref
            self.extract_min_max_id(osmid)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_version(osmversion)
            self.extract_user(osmuid, 'ways')
            self.ages.append(float(osmtimestamp / 1000.0))


            # only compute lengths for road tags
            if 'highway' in tags:
                self.length = self.calc_length()
                self.way_length_map[osmid] = self.length
                self.RCM.sum_way_lengths += self.length

                if tags['highway'] not in ROAD_CATEGORY:
                    self.uncommon_highway_count += 1
                    self.uncommon_highway_length += self.length
                    continue

                if ROAD_CATEGORY[tags['highway']] not in self.costmodel:
                    self.costmodel[ROAD_CATEGORY[tags['highway']]] = RoutingCost()
                    
                road_category_entity = self.costmodel[ROAD_CATEGORY[tags['highway']]]

                road_category_entity.entity_count += 1
                road_category_entity.extract_min_max_id(osmid)
                road_category_entity.extract_min_max_timestamp(osmtimestamp)
                road_category_entity.extract_min_max_version(osmversion)
                road_category_entity.extract_user(osmuid, 'ways')
                road_category_entity.ages.append(float(osmtimestamp / 1000.0))
                road_category_entity.length += self.length
                road_category_entity.sum_way_lengths += self.length

                if 'oneway' in tags:
                    road_category_entity.sum_one_way_lengths += self.length

                if 'maxspeed' in tags:
                    road_category_entity.sum_max_speed_lengths += self.length

                if 'tiger:tlid' in tags:
                    tigerTagValue = tags['tiger:tlid']
                    road_category_entity.tiger_tagged_ways += 1
                    if tigerTagValue not in road_category_entity.tigerbreakdown:
                        road_category_entity.tigerbreakdown[tigerTagValue] = 1
                    else:
                        road_category_entity.tigerbreakdown[tigerTagValue] += 1
                    if osmversion == 1:
                        road_category_entity.untouched_by_user_edits += 1

                    road_category_entity.version_increase_over_tiger += (osmversion - 1)
                    road_category_entity.sum_versions += osmversion

                if 'junction' in tags:
                    road_category_entity.number_of_junctions += 1

            if 'junction' in tags:
                self.RCM.number_of_junctions += 1
            if 'oneway' in tags:
                self.RCM.sum_one_way_lengths += self.length

            if 'maxspeed' in tags:
                self.RCM.sum_max_speed_lengths += self.length

            if 'tiger:tlid' in tags:
                tigerTagValue = tags['tiger:tlid']
                self.RCM.tiger_tagged_ways += 1
                if tigerTagValue not in self.RCM.tigerbreakdown:
                    self.RCM.tigerbreakdown[tigerTagValue] = 1
                else:
                    self.RCM.tigerbreakdown[tigerTagValue] += 1
                if osmversion == 1:
                    self.RCM.untouched_by_user_edits += 1

                self.RCM.version_increase_over_tiger += (osmversion - 1)
                self.RCM.sum_versions += osmversion

    def calc_length(self):
        if len(self.refs) < 2:
            return 0
        lastcoord = ()
        length = 0.0
        for ref in self.refs:
            if ref in self.nodecache:
                coord = self.nodecache[ref]
                if not lastcoord:
                    lastcoord = (coord[0], coord[1])
                    continue
                length += self.haversine(coord[0], coord[1], lastcoord[0], lastcoord[1])
        return length

    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        mi = EARTH_RADIUS_IN_MILES * c
        return mi
