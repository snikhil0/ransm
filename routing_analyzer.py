from imposm.parser import OSMParser
import sys
import os
from time import time
import numpy as np
import math
from tcdb import hdb

# This class does the way routing analysis.
# The analysis is based on tags corresponding to
# ways, nodes and relations
from entity import WayEntity, NodeEntity, RelationEntity, CoordEntity
from user import UserMgr

# location of the tokyo cabinet node cache
CACHE_LOCATION = '/tmp'

#The maximum value for the data temperature value
DATA_TEMP = 100
BASIC_TEMP = 68

# Relative weighing value for the number of users doing 95% of the edits.
USER_WEIGHT95 = 0.2

# Relative weighing value for the routing temperature
ROUTING_WEIGHT = 0.4

# Relative weighing value for the TIGER temperature
TIGER_WEIGHT = 0.2

# Relative weighing value for the Freshness temperature
# Calculated 
FRESHNESS_WEIGHT = 0.3

# Relative weighing factor for the proportion representing the most recent 1/10/25/50/75% of edits
# These factors are used to calculate data freshness.
AGE_WEIGHT1 = 0.3
AGE_WEIGHT10 = 0.25
AGE_WEIGHT25 = 0.1
AGE_WEIGHT50 = 0.1
AGE_WEIGHT75 = 0.05


# Relative weighing value for the Relations temperature
# See relation_temperature()
RELATION_WEIGHT = 0.1

# Base temperature
ZERO_DATA_TEMPERATURE = 32

# The relative weighing factors for each of the binned way categories as
# defined in entity.py
ROAD_CATEGORY_WEIGHTS = {'highways': 0.3, 'main': 0.20, 'local': 0.10, 'guidance': 0.2,
                         'unclassified':-0.1, 'uncommon':-0.1}

class RoutingAnalyzer(object):
    def __init__(self):
        
        # Initialize the Tokyo Cabinet node cache.
        self.nodecache = hdb.HDB()
        try:
            self.nodecache.open(os.path.join(CACHE_LOCATION, 'nodes.tch'))
        except Exception:
            print 'node cache could not be created at %s, does the directory exist? If not, create it. If so, Check permissions and disk space.' % CACHE_LOCATION
            exit(1)

        # Initialize feature containers, passing cache ref
        self.ways_entity = WayEntity(self.nodecache)
        self.nodes_entity = NodeEntity()
        self.relations_entity = RelationEntity()
        self.coords_entity = CoordEntity(self.nodecache)
        
        # Initialize the parser
        self.parser = OSMParser(concurrency=4, coords_callback=self.coords_entity.analyze,
                                nodes_callback=self.nodes_entity.analyze,
                                ways_callback=self.ways_entity.analyze,
                                relations_callback=self.relations_entity.analyze)
        
        # Initialize the User manager.
        self.userMgr = UserMgr()


    # Calculate percentiles (not depending on numpy / scipy)
    # http://stackoverflow.com/questions/2374640/how-do-i-calculate-percentiles-with-python-numpy
    def percentile(self, N, percent, key=lambda x:x):

        """
        Find the percentile of a list of values.

        @parameter N - is a list of values. Note N MUST BE already sorted.
        @parameter percent - a float value from 0.0 to 1.0.
        @parameter key - optional key function to compute value from each element of N.

        @return - the ratio of all values below the percentile of the values and the total number in the array
        """
        if not N:
            return 0
        k = (len(N) - 1) * percent
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return key(N[int(k)])/N[len(N) -1]
        d0 = key(N[int(f)]) * (c - k)
        d1 = key(N[int(c)]) * (k - f)
        return (d0 + d1)/N[len(N) -1]

    # This function calculates the ROUTING dimension of data temperature
    # by calculating the atributes factor for each of the binned categories
    # of way features and weighing them according to the relative bin weight
    def routing_attributes_temperature(self):
        highway_costs = self.ways_entity.attribute_cost('highways')
        main_costs = self.ways_entity.attribute_cost('main')
        local_costs = self.ways_entity.attribute_cost('local')
        guidance_costs = self.ways_entity.attribute_cost('guidance')
        unclassified_costs = self.ways_entity.attribute_cost('unclassified')
        uncommon_costs = float (self.ways_entity.uncommon_highway_length)/self.ways_entity.RCM.sum_way_lengths
        costs = highway_costs * ROAD_CATEGORY_WEIGHTS['highways'] + \
                main_costs * ROAD_CATEGORY_WEIGHTS['main'] + \
                local_costs * ROAD_CATEGORY_WEIGHTS['local'] + \
                guidance_costs * ROAD_CATEGORY_WEIGHTS['guidance'] + \
                unclassified_costs * ROAD_CATEGORY_WEIGHTS['unclassified'] + \
                uncommon_costs * ROAD_CATEGORY_WEIGHTS['uncommon']
        
        return costs * BASIC_TEMP

    # This function calculates the RELATION dimension of data temperature
    def relation_temperature(self):
        return float(self.relations_entity.restriction_length)/self.ways_entity.RCM.sum_way_lengths * BASIC_TEMP

    def data_temerature(self):
        # Aggregate user and edit counts
        array = self.userMgr.ages
        array.sort()
        counts = self.userMgr.edit_counts
        counts.sort()

        # Freshness factors calculation 
        one_percentile_age = self.percentile(array, 0.01)
        cost_ages1 = one_percentile_age * AGE_WEIGHT1

        ten_percentile_age = self.percentile(array, 0.1)
        cost_ages10 = ten_percentile_age * AGE_WEIGHT10

        twentyfive_percentile_age = self.percentile(array, 0.25)
        cost_ages25 = twentyfive_percentile_age * AGE_WEIGHT25

        fifty_percentile_age = self.percentile(array, 0.50)
        cost_ages50 = fifty_percentile_age * AGE_WEIGHT50

        seventyfive_percentile_age = self.percentile(array, 0.75)
        cost_ages75 = seventyfive_percentile_age * AGE_WEIGHT75

        # Calculate 95 percintile of users, this is not part of freshness but
        # is used in the freshness temperature.
        nintyfive_percentile_user_edits = self.percentile(counts, 0.95)
        cost_user95 = nintyfive_percentile_user_edits * USER_WEIGHT95
        

        # Normalize the data temperature to between 0 and 40 and add a buffer of zero celsius
        datatemp = RELATION_WEIGHT * self.relation_temperature() + \
                   ROUTING_WEIGHT * self.routing_attributes_temperature() + FRESHNESS_WEIGHT * \
                    (cost_ages1 + cost_ages10 + cost_ages25   + \
                   cost_user95 + cost_ages50 + cost_ages75)  * BASIC_TEMP + \
                   TIGER_WEIGHT * self.ways_entity.RCM.tiger_cost() * BASIC_TEMP + ZERO_DATA_TEMPERATURE
        return datatemp

    def run(self, filename):
        # Timings can be done outside of the program using time(1)
        # and should probably be deprecated here
        t0 = time()
        
        # Parse the input data
        self.parser.parse(filename)
        t1 = time()
        
        # Merge the User collections from the various feature containers
        self.userMgr.merge(self.nodes_entity.users, self.ways_entity.users,
                           self.relations_entity.users)

        # Merge the ages collections from the various feature containers
        self.userMgr.merge_ages(self.nodes_entity.ages, self.ways_entity.ages,
                                self.relations_entity.ages)

        # Calculate data temperature
        datatemp = self.data_temerature()

        print 'data temperature for %s is: %f' % (filename, datatemp)

        #        print 'number of coords / nodes / ways / relations: %d / %d / %d / %d' % (self.coords_entity.entity_count,
        #                                                                                 self.nodes_entity.entity_count,
        #                                                                                 self.ways_entity.entity_count,
        #                                                                                 self.relations_entity.entity_count)
        #        print 'min / max node id: %d / %d' % (self.nodes_entity.minid, self.nodes_entity.maxid)
        #        print 'min / max way id: %d / %d' % (self.ways_entity.minid, self.ways_entity.maxid)
        #        print 'min / max relation id: %d / %d' % (self.relations_entity.minid, self.relations_entity.maxid)
        #        print 'bbox: (%f %f, %f %f)' % (self.coords_entity.min_lon, self.coords_entity.min_lat,
        #                                        self.coords_entity.max_lon, self.coords_entity.min_lat)
        #        print 'first way timestamp: %s' % (self.ways_entity.first_timestamp)
        #        print 'last way timestamp: %s' % (self.ways_entity.last_timestamp)
        #        print 'mean way version: %f' % (self.ways_entity.mean_version)
        #        print 'turn restrictions: %d' % (self.relations_entity.num_turnrestrcitions)
        print 'took %fs' % (t1 - t0)


def usage():
    print 'python routing_analyzer.py [file.xml|pbf]'


def main(args):
    if len(args) > 2 or len(args) < 2:
        usage()
        exit()

    analysis_engine = RoutingAnalyzer()
    analysis_engine.run(args[1])

if __name__ == "__main__":
    main(sys.argv)

