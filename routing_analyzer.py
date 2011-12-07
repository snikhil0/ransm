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
from entity import WayEntity, NodeEntity, RelationEntity, CoordEntity, USERS_CACHE, AGES_CACHE
from user import UserMgr

# location of the tokyo cabinet node cache
CACHE_LOCATION = '/tmp'

#The maximum value for the data temperature value
DATA_TEMP = 100
BASIC_TEMP = 68

## Weights

# Relative weighing value for the number of users doing 95% of the edits.
USER_WEIGHT95 = 0.2

# Relative weighing value for the routing temperature
ROUTING_WEIGHT = 0.4

# Relative weighing value for the TIGER temperature
TIGER_WEIGHT = 0.2

# Relative weighing value for the Freshness temperature
# Calculated 
FRESHNESS_WEIGHT = 0.3

# Relative weighing value for the Relations temperature
# See relation_temperature()
RELATION_WEIGHT = 0.1

# Relative weighing factor for the proportion representing the most recent 1/10/25/50/75% of edits
# These factors are used to calculate data freshness.
AGE_WEIGHT1 = 0.3
AGE_WEIGHT10 = 0.25
AGE_WEIGHT25 = 0.1
AGE_WEIGHT50 = 0.1
AGE_WEIGHT75 = 0.05


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
            return float(key(N[int(k)]))
        d0 = key(N[int(f)]) * (c - k)
        d1 = key(N[int(c)]) * (k - f)
        return float(d0 + d1)

    # This function calculates the ROUTING dimension of data temperature
    # by calculating the atributes factor for each of the binned categories
    # of way features and weighing them according to the relative bin weight
    def routing_attributes_temperature(self):
        highway_factor = self.ways_entity.attribute_factor('highways')
        main_factor = self.ways_entity.attribute_factor('main')
        local_factor = self.ways_entity.attribute_factor('local')
        guidance_factor = self.ways_entity.attribute_factor('guidance')
        unclassified_factor = self.ways_entity.attribute_factor('unclassified')
        uncommon_factor = float (self.ways_entity.uncommon_highway_length)/self.ways_entity.length
        
        factors = highway_factor * ROAD_CATEGORY_WEIGHTS['highways'] + \
                main_factor * ROAD_CATEGORY_WEIGHTS['main'] + \
                local_factor * ROAD_CATEGORY_WEIGHTS['local'] + \
                guidance_factor * ROAD_CATEGORY_WEIGHTS['guidance'] + \
                unclassified_factor * ROAD_CATEGORY_WEIGHTS['unclassified'] + \
                uncommon_factor * ROAD_CATEGORY_WEIGHTS['uncommon']
        
        return factors * BASIC_TEMP

    # This function calculates the RELATION dimension of data temperature
    def relation_temperature(self):
        return float(self.relations_entity.restriction_length)/self.ways_entity.length * BASIC_TEMP

    def data_temerature(self):
        # Aggregate user and edit counts
        # reverse the AGES because the newest will be at the top, so when we get the 1%, 10%,
        # we search from the top
        array = self.userMgr.ages
        array.sort(reverse=True)

        # don't reverse it, so when we ask for 95% edits it gets from the ascending order
        counts = self.userMgr.edit_counts
        counts.sort()

        # Freshness factors calculation
        max_array = max(array)
        ages1_factor = self.percentile(array, 0.01)/max_array * AGE_WEIGHT1
        ages10_factor = self.percentile(array, 0.10)/max_array * AGE_WEIGHT10
        ages25_factor = self.percentile(array, 0.25)/max_array * AGE_WEIGHT25
        ages50_factor = self.percentile(array, 0.50)/max_array * AGE_WEIGHT50
        ages75_factor = self.percentile(array, 0.75)/max_array * AGE_WEIGHT75

        # Calculate 95 percintile of users, this is not part of freshness but
        # is used in the freshness temperature.
        user95_factor = self.percentile(counts, 0.95)/max(counts) * USER_WEIGHT95

        # Normalize the data temperature to between 0 and 40 and add a buffer of zero celsius
        return  (RELATION_WEIGHT * self.relation_temperature() + \
                   ROUTING_WEIGHT * self.routing_attributes_temperature() + FRESHNESS_WEIGHT * \
                    (ages1_factor + ages10_factor + ages25_factor   + \
                   user95_factor + ages50_factor + ages75_factor)  * BASIC_TEMP + \
                   TIGER_WEIGHT * self.ways_entity.tiger_factor() * BASIC_TEMP + ZERO_DATA_TEMPERATURE)

    def run(self, filename):
        # Timings can be done outside of the program using time(1)
        # and should probably be deprecated here
        t0 = time()
        
        # Parse the input data
        self.parser.parse(filename)
        t1 = time()

        # Print the parsing time
        print 'The parsing of the file took %f' %(t1 - t0)
        # Merge the User collections from the various feature containers
        self.userMgr.merge(USERS_CACHE)

        # Merge the ages collections from the various feature containers
        self.userMgr.merge_ages(AGES_CACHE)

        # Calculate data temperature
        datatemp = self.data_temerature()

        print 'Data temperature for %s is: %f' % (filename, datatemp)

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
        print 'Data temperature calculation took %fs' % (time() - t1)
        print 'Total process took %fs' %(time() - t0)

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

