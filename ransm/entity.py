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
from math import *

# The radius of the earth, used in the Haversine formula for
# simplified distance calculations
import itertools

# The relative weighing factors used in calculating the
# ROUTING factor: oneway, maxspeed and access tags
ONE_WAY_WEIGHT = 0.3
MAX_SPEED_WEIGHT = 0.3
GUIDANCE_FACTOR = 0.3
ACCESS_WEIGHT = 0.1

# The relative weighing factors used in calculating the
# TIGER factor: untouched, version increment over tiger
UNTOUCHED_WEIGHT = -0.3
VERSION_INCREASE_OVER_TIGER = 1

# The relative weighing factors used in the ATTRIBUTE factor
# ATTRIBUTE factor: length
LENGTH_WEIGHT = 0.2
ROUTING_WEIGHT = 0.6
JUNCTION_WEIGHT = 0.1

EARTH_RADIUS_IN_MILES = 3963.19

# Binning OSM features into a limited number of categories:
#   - highways
#   - main
#   - local
#   - guidance
#   - unclassified
# [MvE] this needs some scrutiny!
ROAD_CATEGORY = {'motorway': 'highways', 'trunk': 'main', 'primary': 'main', 'secondary': 'local',
                 'tertiary': 'local', 'residential': 'local', 'unclassified': 'unclassified', 'road': 'unclassified',
                 'living_street': 'local', 'service': 'local', 'track': 'local', 'pedestrian': 'local',
                 'raceway': 'local', 'services': 'local', 'rest_area': 'local', 'bus_guideway': 'local',
                 'path': 'local', 'cycleway': 'NA', 'footway': 'NA', 'mini_roundabout': 'guidance',
                 'stop': 'guidance', 'give_way': 'guidance', 'traffic_signals': 'guidance',
                 'crossing': 'guidance', 'roundabout': 'guidance', 'motorway_junction': 'guidance',
                 'turning_circle': 'guidance', 'construction': 'guidance', 'motorway_link': 'local',
                 'trunk_link': 'local', 'primary_link': 'local', 'secondary_link': 'local',
                 'tertiary_link': 'local'}

class Containers(object):
    """
        A class that is made up of containers for
         ages, user edits, intersections, tiger breakdown among other things
    """
    WAY_LENGTH_MAP = {}

    # Cache used for temperature computation that is
    # computed in one entity and used in another. This does not belong to the
    # entity class but is a more global container
    USERS_EDITS = {}
    AGES = []

    # The mapping of the node id's to the number of times they are referenced
    # We need to keep the name of the ways (intersections are defined as ways
    # with different names share a node)
    INTERSECTIONS = {}

    # Map of the tiger tags and count for them
    # tiger:tlid, tiger:cfcc etc
    TIGER_BREAKDOWN = {}

    ## The way nodes that are needed for Guidance scores
    WAY_NODES = {}

    def __init__(self):
        pass

    

# Common functions to extract user information and age (timestamps)
# and populate the above
def average(ages):
    """
    Calculates the average of the array that is sent into it
    """
    if len(ages) > 0:
        return sum(ages, 0.0) / len(ages)

    return 0

def extract_user(uid, users):
    """
        increment the user edits map
        keeps track of number of edits made by the user
    """
    if uid not in users:
        users[uid] = 0

    users[uid] += 1

class Entity(object):
    """
    The base class for all the other entities. This class keeps track of the min, max
    versions, mat, lon, id and version. It also keeps track of the count of entities parsed
    """
    def __init__(self):
        """""
        Constructor: initialize members
        """""
        self.entity_count = 0
        self.min_version = sys.maxint
        self.max_version = 0
        self.mean_version = 0
        self.first_timestamp = datetime.max
        self.last_timestamp = datetime.min
        self.maxid = 0
        self.minid = sys.maxint
        self.max_lon = -sys.maxint
        self.min_lon = sys.maxint
        self.min_lat = sys.maxint
        self.max_lat = -sys.maxint

    def extract_min_max_timestamp(self, osmtimestamp):
        """
            extract the max and min timestamps from each parsed timestamp value
        """
        timestamp = datetime.utcfromtimestamp(osmtimestamp)
        if timestamp > self.last_timestamp:
            self.last_timestamp = timestamp
        if timestamp < self.first_timestamp:
            self.first_timestamp = timestamp

    def extract_min_max_id(self, osmid):
        """
            extract the max and min id's, called by callback for every xml element
        """
        if osmid > self.maxid:
            self.maxid = osmid
        if osmid < self.minid:
            self.minid = osmid

    def extract_min_max_lat_lon(self, lon, lat):
        """
            Extract the min and max lat,lon from entities callback
        """
        if lon > self.max_lon:
            self.max_lon = lon
        if lon < self.min_lon:
            self.min_lon = lon
        if lat < self.min_lat:
            self.min_lat = lat
        if lat > self.max_lat:
            self.max_lat = lat

    def extract_min_max_version(self, osmversion):
        """
            extract the min and max versions for entities (callback)
        """
        if osmversion > self.max_version:
            self.max_version = osmversion
        if osmversion < self.min_version:
            self.min_version = osmversion


class CoordEntity(Entity):
    """""
        The class that gets the callback for Coords from Imposm parser.
        Holds all the information relevant to the Coord and shares user and age information
        with the global containers
        The use of Coords in the routing analysis is to store the nodes in the
        Tokyo Cabinet style node cache for computing distances for ways based on node ids.
        The CoordEntity is the class that holds information for ALL Coords. So this infact is
        a container for all coords.
    """""
    
    def __init__(self, nodecache):
        """
            The constructor, passes the nodeCache which is a key,value pairs
            of nodeIds and lat, lon (stored in the tokyo file cabinet)
        """
        Entity.__init__(self)
        self.min_lat = self.min_lon = float(-180.0)
        self.max_lat = self.max_lon = float(180.0)
        self.nodecache = nodecache


    def analyze(self, coord):
        """
            This is the callback for the Coords. Different entities have different callback arguments
            and hence have not be abstracted. Maybe python allows this in some form
        """
        for osmid, lon, lat, osmversion, osmtimestamp, osmuid in coord:
            self.entity_count += 1
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_lat_lon(lon, lat)
            self.extract_min_max_version(osmversion)
            self.nodecache[osmid] = (lon, lat, osmtimestamp, osmversion)

class NodeEntity(Entity):
    """""
        This class gets the callback for Nodes from Imposm parser.
        Holds the information relevant to the node. No special tags are stored for Nodes yet,
        but the class can be extended. Again, the NodeEntity is a container for all nodes and hence
        the information stored is either a comparison or accumulation of information from each node.
    """""
    def __init__(self, constants):
        """
            Constructor
        """
        Entity.__init__(self)
        self.const = constants

    def analyze(self, nodes):
        """
            Callback method for the nodes
        """
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in nodes:
            self.entity_count += 1
            extract_user(osmuid, self.const.USERS_EDITS)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)
            self.extract_min_max_lat_lon(ref[0], ref[1])
            time = datetime.fromtimestamp(osmtimestamp)
            self.const.AGES.append(time)
            # store the node tags for later parsing for
            # guidance score
            self.const.WAY_NODES[osmid] = tags
                    
class RelationEntity(Entity):
    """""
        The relation callback get here. This class is a container for holding information for all
        relations. Number of restrictions and total length of restrictions are members of this class.
    """""
    def __init__(self, constants):
        """
            Constructor
        """
        Entity.__init__(self)
        self.num_turnrestrcitions = 0
        self.sum_restriction_length = 0
        self.sum_turn_restriction_length = 0
        self.const = constants

    def analyze(self, relations):
        """
            callback method for the relations
        """
        for osmid, tags, refs, osmversion, osmtimestamp, osmuid in relations:
            self.entity_count += 1
            extract_user(osmuid, self.const.USERS_EDITS)
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_version(osmversion)

            time = datetime.fromtimestamp(osmtimestamp)
            self.const.AGES.append(time)

            length = 0
            for ref in refs:
                    if ref in self.const.WAY_LENGTH_MAP:
                        length += self.const.WAY_LENGTH_MAP[ref]

            self.sum_restriction_length += length
                    
            if 'type' in tags and tags['type'] == 'restriction':
                self.num_turnrestrcitions += 1
                self.sum_turn_restriction_length += length

class CommonAttributes(object):
    """
    Repeated counts for both attributes and way entity
    Note that the version comes from the max of the way version and
    node versions
    """
    def __init__(self):
        """
            Constructor
        """
        self.untouched_by_user_edits = 0
        self.version_increase_over_tiger = 0
        self.sum_versions = 0
        self.tiger_tagged_ways = 0

    def analyze(self, tags, osmversion):
        """
            Parse the values and keep track of the member counts
        """
        visited = False
        for key in tags:
            if 'tiger' in key and not visited:
                self.tiger_tagged_ways += 1
                self.version_increase_over_tiger += (osmversion - 1)
                visited = True

                # Only if the way is tiger then the untouched
                # is when the version is 1
                if osmversion == 1:
                    self.untouched_by_user_edits += 1

        self.sum_versions += osmversion

    def tiger_factor(self, num_ways):
        """
            Tiger factor is based on the number of edits that are untouched from tiger and number of versions over tiger
            The former gets a negative weighting and the latter gets a positive weighting => the more edits the better
            the data. Go figure!
        """
        version_increase_over_tiger_factor = 0
        untouched_by_users_factor = UNTOUCHED_WEIGHT * float(self.untouched_by_user_edits)/num_ways
        if self.sum_versions:
            version_increase_over_tiger_factor = VERSION_INCREASE_OVER_TIGER * float(self.version_increase_over_tiger)/self.sum_versions
        return untouched_by_users_factor + version_increase_over_tiger_factor


class WayAttributeEntity(Entity):
    """""
     This class maintains the information pertaining to the attributes for routing for a particular class of way.
     This inherits from Entity because we also keep account of the variables of the entity model.
     The timestamp and the version come from the max of way version and node versions and similarly for timestamps
    """""
    def __init__(self, constant):
        """
            Constructor
        """
        Entity.__init__(self)
        self.commonAttributes = CommonAttributes()
        self.sum_way_lengths = 0
        self.sum_one_way_lengths = 0
        self.sum_max_speed_lengths = 0
        self.number_of_junctions = 0
        self.sum_junction_length = 0
        self.number_of_access = 0
        self.sum_access_length = 0
        self.sum_guidance_length = 0
        self.const = constant

    def analyze(self, osmid, tags, ref, osmversion, osmtimestamp, length):
        """
            Extract all the attribute level info
        """
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

        if 'junction' in tags:
            self.number_of_junctions += 1
            self.sum_junction_length += length

        guidance_keys =('stop','give_way', 'traffic_signals', 'crossing', 'roundabout',
                        'motorway_junction', 'turning_circle', 'construction')

        if tags['highway'] in guidance_keys:
            self.sum_guidance_length += length

        # Look in the reference nodes and check to see which ones have
        # guidance on them
        for r in ref:
            if r in self.const.WAY_NODES and 'highway' in self.const.WAY_NODES[r]:
                highway_value = self.const.WAY_NODES[r]['highway']
                if highway_value in guidance_keys:
                    self.sum_guidance_length += length
                    break # count them only once

        self.commonAttributes.analyze(tags, osmversion)


    def tiger_factor(self):
        """
            Tiger factor is based on the number of edits that are untouched from tiger and number of versions over tiger
            The former gets a negative weighting and the latter gets a positive weighting => the more edits the better
            the data. Go figure!
        """
        return self.commonAttributes.tiger_factor(self.entity_count)

    def routing_factor(self):
        """
            The routing factor counts all the ways that have either a one way tag, max speed tag or access tag. These are
            normalized to the total length of all ways for the dataset. Again the larger the factor the better the data for
            routing.
        """
        # routing features normalized by way distances
        if not self.sum_one_way_lengths:
            return 0
        oneway_factor = float(self.sum_one_way_lengths)/self.sum_way_lengths
        maxspeed_factor = float(self.sum_max_speed_lengths)/self.sum_way_lengths
        access_factor = float(self.sum_access_length)/self.sum_way_lengths
        guidance_factor = float(self.sum_guidance_length)/self.sum_way_lengths

        return ONE_WAY_WEIGHT * oneway_factor + MAX_SPEED_WEIGHT * maxspeed_factor + access_factor * ACCESS_WEIGHT + \
               GUIDANCE_FACTOR * guidance_factor

    def junction_factor(self):
        """
            Similar to the above ideas, but this counts the junctions.
        """
        if self.sum_way_lengths > 0:
            return float(self.sum_junction_length)/self.sum_way_lengths
        return 0
    
class WayEntity(Entity):
    """""
        This is where the callback for ways gets. The ways entity is a complicated beast,
        it contains a map of road categories to attribute model. The attribute model is defined below.
        The way entity is responsible for computing factors for the individual models and also giving an
        aggregated factor for all ways irrespective of categorization.

    """""
    def __init__(self, nodecache, constant):
        """
            Constructor
            Note the attribute models which is basically a model per road category
        """
        Entity.__init__(self)
        self.nodecache = nodecache
        self.attribute_models = {} #key is road category, value is routing cost model
        self.uncommon_highway_count = 0
        self.uncommon_highway_length = 0
        self.length = 0
        self.commonAttributes = CommonAttributes()
        self.const = constant

    def attribute_factor(self, road_category):
        """
             This function calculates the ATTRIBUTES factor which is used in the
             ROUTING dimension of the data temperature.
        """
        if road_category not in ROAD_CATEGORY.values() or road_category not in self.attribute_models:
            return 0

        road_feature = self.attribute_models[road_category]
        length_factor = float(road_feature.sum_way_lengths)/self.length
        routing_factor = road_feature.routing_factor()
        junction_factor = road_feature.junction_factor()

        return length_factor * LENGTH_WEIGHT + routing_factor * ROUTING_WEIGHT + \
               junction_factor * JUNCTION_WEIGHT

    def tiger_factor(self):
        """
            Tiger factor is based on the number of edits that are untouched from tiger and number of versions over tiger
            The former gets a negative weighting and the latter gets a positive weighting => the more edits the better
            the data. Go figure!
        """
        return self.commonAttributes.tiger_factor(self.entity_count)


    def analyze(self, ways):
        """
            Callback method for the ways
        """
        for osmid, tags, ref, osmversion, osmtimestamp, osmuid in ways:
            self.entity_count += 1
            self.extract_min_max_id(osmid)

            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_version(osmversion)
            extract_user(osmuid, self.const.USERS_EDITS)

            # get the latest time stamp and version from all the  nodes
            # and that represents the way timestamp and version
            node_timestamp = osmtimestamp
            node_version = osmversion
            for r in ref:
                if r in self.nodecache:
                    node = self.nodecache[r]
                    node_timestamp = max(node[2], osmtimestamp)
                    node_version = max(node[3], osmversion)

            time = datetime.fromtimestamp(osmtimestamp)
            self.const.AGES.append(time)

            # only compute lengths for road tags
            if 'highway' in tags:
                length = self.calc_length(ref)
                # sum the lengths 
                self.length += length
                # keep a map for later reference : for relations
                self.const.WAY_LENGTH_MAP[osmid] = length

                if 'oneway' not in tags:
                    for r in ref:
                        if r not in self.const.INTERSECTIONS:
                            self.const.INTERSECTIONS[r] = 0
                        self.const.INTERSECTIONS[r] += 1

                # Parse the common attributes
                self.commonAttributes.analyze(tags, node_version)

                # get the road category: if it is not present in our map
                # then it is an uncommon one otherwise extract routing and entity level information
                # for those attributes
                if tags['highway'] not in ROAD_CATEGORY:
                    self.uncommon_highway_count += 1
                    self.uncommon_highway_length += length
                else:
                    if ROAD_CATEGORY[tags['highway']] not in self.attribute_models:
                        category = ROAD_CATEGORY[tags['highway']]
                        self.attribute_models[category] = WayAttributeEntity(self.const)
                    
                    road_category_entity = self.attribute_models[ROAD_CATEGORY[tags['highway']]]
                    road_category_entity.analyze(osmid, tags, ref, node_version, node_timestamp, length)
                


    def calc_length(self, refs):
        """
            Calculates the length of the way given the list of node id refernces
            what this does is computes the length per edge and adds it up
        """
        length = 0
        for r1, r2 in itertools.combinations(refs, 2):
            length += self.haversine(r1, r2, self.nodecache)

        return length

    def haversine(self, node1, node2, nodeCache):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        if node1 not in nodeCache or node2 not in nodeCache:
            return 0

        coord1 = nodeCache[node1]
        coord2 = nodeCache[node2]
        lon1, lat1, lon2, lat2 = map(radians, [coord1[1], coord1[0], coord2[1], coord2[0]])
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        mi = EARTH_RADIUS_IN_MILES * c
        return mi