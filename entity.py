# Copyright 2011 Martijn Van Excel and Telenav Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
from datetime import datetime
from user import  User
from math import *

# The radius of the earth, used in the Haversine formula for
# simplified distance calculations
EARTH_RADIUS_IN_MILES = 3963.19

# Binning OSM features into a limited number of categories:
#   - highways
#   - main
#   - local
#   - guidance
#   - unclassified

# [MvE] this needs some scrutiny!
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

# The relative weighing factors used in calculating the 
# ROUTING factor: oneway, maxspeed and access tags
ONE_WAY_WEIGHT = 0.45
MAX_SPEED_WEIGHT = 0.45
ACCESS_WEIGHT = 0.1

# The relative weighing factors used in calculating the
# TIGER factor: untouched, version increment over tiger
UNTOUCHED_WEIGHT = -0.3
VERSION_INCREASE_OVER_TIGER = 0.7

# The relative weighing factors used in the ATTRIBUTE factor
# ATTRIBUTE factor: length
LENGTH_WEIGHT = 0.2
ROUTING_WEIGHT = 0.4
JUNCTION_WEIGHT = 0.1
TIGER_WEIGHT = 0.3

WAY_LENGTH_MAP = {}

# Cache used for temperature computation that is
# computed in one entity and used in another. This does not belong to the
# entity class but is a more global container
USERS_CACHE = {}
AGES_CACHE = []
NODES_CACHE = {}

# Map of the tiger tags and count for them
# tiger:tlid, tiger:cfcc etc
TIGER_BREAKDOWN = {}

# Common functions to extract user information and age (timestamps)
# and populate the above
def average_age():
    if len(AGES_CACHE) > 0:
        return sum(AGES_CACHE, 0.0) / len(AGES_CACHE)
    return 0

def extract_user(uid, type):
    if uid not in USERS_CACHE:
        USERS_CACHE[uid] = User(uid, str(uid))
    else:
        USERS_CACHE[uid].increment(type)


class Entity(object):
    '''
    Base class for all other entities
    Stores the repetitive basic information like:
    count
    min, mean and max versions
    first and last timestamps
    min and max ids
    '''

    def __init__(self):
        '''
        Constructor: initialize members
        '''
        self.entity_count = 0
        self.min_version = sys.maxint
        self.max_version = 0
        self.mean_version = 0
        self.first_timestamp = datetime.max
        self.last_timestamp = datetime.min
        self.maxid = 0
        self.minid = sys.maxint

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
    '''
        The class that gets the callback for Coords from Imposm parser.
        Holds all the information relevant to the Coord and shares user and age information
        with the global containers
        The use of Coords in the routing analysis is to store the nodes in the
        Tokyo Cabinet style node cache for computing distances for ways based on node ids.
        The CoordEntity is the class that holds information for ALL Coords. So this infact is
        a container for all coords.
    '''
    
    def __init__(self, nodecache):
        Entity.__init__(self)
        self.min_lat = self.min_lon = float(-180.0)
        self.max_lat = self.max_lon = float(180.0)
        self.nodecache = nodecache

    # This is the callback for the Coords
    # Different entities have different callback arguments and hence have not be abstracted
    # Maybe python allows this in some form
    def analyze(self, coord):
        for osmid, lon, lat, osmversion, osmtimestamp, osmuid in coord:
            self.entity_count += 1
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_lat_lon(lon, lat)
            self.extract_min_max_version(osmversion)
            self.nodecache[osmid] = (lon,lat)

class NodeEntity(Entity):
    '''
        This class gets the callback for Nodes from Imposm parser.
        Holds the information relevant to the node. No special tags are stored for Nodes yet,
        but the class can be extended. Again, the NodeEntity is a container for all nodes and hence
        the information stored is either a comparison or accumulation of information from each node.
    '''
    def __init__(self):
        Entity.__init__(self)

    # Callback method for the nodes
    def analyze(self, nodes):
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in nodes:
            self.entity_count += 1
            extract_user(osmuid, 'nodes')
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            AGES_CACHE.append(float(osmtimestamp / 1000.0))
            if osmid not in NODES_CACHE:
                NODES_CACHE[osmid] = (ref[0], ref[1])


class RelationEntity(Entity):
    '''
        The relation callback get here. This class is a container for holding information for all
        relations. Number of restrictions and total length of restrictions are members of this class.
    '''
    def __init__(self):
        Entity.__init__(self)
        self.num_turnrestrcitions = 0
        self.sum_restriction_length = 0
        self.sum_turn_restriction_length = 0

    #callback method for the relations
    def analyze(self, relations):
        for osmid, tags, refs, osmversion, osmtimestamp, osmuid in relations:
            self.entity_count += 1
            extract_user(osmuid, 'relations')
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            AGES_CACHE.append(float(osmtimestamp / 1000.0))
            length = 0
            for ref in refs:
                    if ref[0] in WAY_LENGTH_MAP:
                        length += WAY_LENGTH_MAP[ref[0]]

            self.sum_restriction_length += length
                    
            if 'type' in tags and tags['type'] == 'restriction':
                self.num_turnrestrcitions += 1
                self.sum_turn_restriction_length += length



class WayAttributeModel(Entity):
    '''
     This class maintains the information pertaining to the attributes for routing for a particular class of way.
     This inherits from Entity because we also keep account of the variables of the entity model.
    '''
    def __init__(self):
        Entity.__init__(self)
        self.tiger_tagged_ways = 0
        self.untouched_by_user_edits = 0
        self.version_increase_over_tiger = 0
        self.sum_versions = 0
        self.sum_way_lengths = 0
        self.sum_one_way_lengths = 0
        self.sum_max_speed_lengths = 0
        self.number_of_junctions = 0
        self.sum_junction_length = 0
        self.number_of_access = 0
        self.sum_access_length = 0


    # extract all the attribute level info
    def analyze(self, osmid, tags, osmversion, osmtimestamp, length):
        self.entity_count += 1
        self.extract_min_max_id(osmid)
        self.extract_min_max_timestamp(osmtimestamp)
        self.extract_min_max_version(osmversion)
        self.sum_way_lengths += length

        if 'access' in tags:
            self.sum_access_length += length
            self.number_of_access += 1
        if 'oneway' in tags:
            self.sum_one_way_lengths += length
        if 'maxspeed' in tags:
            self.sum_max_speed_lengths += length
        if 'tiger:tlid' in tags:
            tigerTagValue = tags['tiger:tlid']
            self.tiger_tagged_ways += 1
            if tigerTagValue not in TIGER_BREAKDOWN:
                TIGER_BREAKDOWN[tigerTagValue] = 1
            else:
                TIGER_BREAKDOWN[tigerTagValue] += 1

            if osmversion == 1:
                self.untouched_by_user_edits += 1

            self.version_increase_over_tiger += (osmversion - 1)
            self.sum_versions += osmversion
        if 'junction' in tags:
            self.number_of_junctions += 1
            self.sum_junction_length += length

    # Tiger factor is based on the number of edits that are untouched from tiger and number of versions over tiger
    # The former gets a negative weighting and the latter gets a positive weighting => the more edits the better
    # the data. Go figure!
    def tiger_factor(self):
        # Refactor later to compute temps from different sources and fuze them
        untouched_by_users_factor = UNTOUCHED_WEIGHT * float(self.untouched_by_user_edits)/self.tiger_tagged_ways
        version_increase_over_tiger_factor = VERSION_INCREASE_OVER_TIGER * float(self.version_increase_over_tiger)/self.sum_versions
        return untouched_by_users_factor + version_increase_over_tiger_factor

    # The routing factor counts all the ways that have either a one way tag, max speed tag or access tag. These are
    # normalized to the total length of all ways for the dataset. Again the larger the factor the better the data for
    # routing.
    def routing_factor(self):
        # routing features normalized by way distances
        if not self.sum_one_way_lengths:
            return 0
        oneway_factor = float(self.sum_one_way_lengths)/self.sum_way_lengths
        maxspeed_factor = float(self.sum_max_speed_lengths)/self.sum_way_lengths
        access_factor = float(self.sum_access_length)/self.sum_way_lengths
        
        return ONE_WAY_WEIGHT * oneway_factor + MAX_SPEED_WEIGHT * maxspeed_factor + access_factor * ACCESS_WEIGHT

    # Similar to the above ideas, but this counts the junctions.
    def junction_factor(self):
        return float(self.sum_junction_length)/self.sum_way_lengths

class WayEntity(Entity):
    '''
        This is where the callback for ways gets. The ways entity is a complicated beast,
        it contains a map of road categories to attribute model. The attribute model is defined below.
        The way entity is responsible for computing factors for the individual models and also giving an
        aggregated factor for all ways irrespective of categorization.

    '''
    def __init__(self, nodecache):
        Entity.__init__(self)
        self.nodecache = nodecache
        self.attribute_models = {} #key is road category, value is routing cost model
        self.uncommon_highway_count = 0
        self.uncommon_highway_length = 0
        self.length = 0

        # Repeated counts for both attributes and way entity
        # Refactor to separate class
        self.untouched_by_user_edits = 0
        self.version_increase_over_tiger = 0
        self.sum_versions = 0
        self.tiger_tagged_ways = 0

    # This function calculates the ATTRIBUTES factor which is used in the
    # ROUTING dimension of the data temperature. 
    def attribute_factor(self, road_category):
        if road_category not in ROAD_CATEGORY.values():
            return 0
        road_feature = self.attribute_models[road_category]
        length_factor = float(road_feature.sum_way_lengths)/self.length
        routing_factor = road_feature.routing_factor()
        junction_factor = road_feature.junction_factor()
        tiger_factor = road_feature.tiger_factor()

        return length_factor * LENGTH_WEIGHT + routing_factor * ROUTING_WEIGHT + \
               junction_factor * JUNCTION_WEIGHT + tiger_factor * TIGER_WEIGHT

    # Tiger factor is based on the number of edits that are untouched from tiger and number of versions over tiger
    # The former gets a negative weighting and the latter gets a positive weighting => the more edits the better
    # the data. Go figure!
    def tiger_factor(self):
        # Refactor later to compute temps from different sources and fuze them
        untouched_by_users_factor = UNTOUCHED_WEIGHT * float(self.untouched_by_user_edits)/self.tiger_tagged_ways
        version_increase_over_tiger_factor = VERSION_INCREASE_OVER_TIGER * float(self.version_increase_over_tiger)/self.sum_versions
        return untouched_by_users_factor + version_increase_over_tiger_factor


    def analyze(self, ways):
        #callback method for the ways
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in ways:
            self.entity_count += 1
            self.extract_min_max_id(osmid)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_version(osmversion)
            extract_user(osmuid, 'ways')
            AGES_CACHE.append(float(osmtimestamp / 1000.0))

            # only compute lengths for road tags
            if 'highway' in tags:
                length = self.calc_length(ref)
                # sum the lengths 
                self.length += length
                # keep a map for later reference : for relations
                WAY_LENGTH_MAP[osmid] = length

                # Keep a master tiger count
                if 'tiger:tlid' in tags:
                    self.tiger_tagged_ways += 1
                    if osmversion == 1:
                        self.untouched_by_user_edits += 1

                    self.version_increase_over_tiger += (osmversion - 1)
                    self.sum_versions += osmversion

                # get the road category: if it is not present in our map
                # then it is an uncommon one otherwise extract routing and entity level information
                # for those attributes
                if tags['highway'] not in ROAD_CATEGORY:
                    self.uncommon_highway_count += 1
                    self.uncommon_highway_length += length
                else:
                    if ROAD_CATEGORY[tags['highway']] not in self.attribute_models:
                        category = ROAD_CATEGORY[tags['highway']]
                        self.attribute_models[category] = WayAttributeModel()
                    
                    road_category_entity = self.attribute_models[ROAD_CATEGORY[tags['highway']]]
                    road_category_entity.analyze(osmid, tags, osmversion, osmtimestamp, length)

    def calc_length(self, refs):
        if len(refs) < 2:
            return 0
        lastcoord = ()
        length = 0.0
        for ref in refs:
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
