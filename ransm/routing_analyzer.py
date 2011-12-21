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
import datetime
from imposm.parser import OSMParser
import sys
import os
from time import time
import math
from tcdb import hdb

# This class does the way routing analysis.
# The analysis is based on tags corresponding to
# ways, nodes and relations


# location of the tokyo cabinet node cache
from entity import WayEntity, NodeEntity, RelationEntity, CoordEntity, Containers

CACHE_LOCATION = '/tmp'

#The maximum value for the data temperature value
DATA_TEMP = 100
BASIC_TEMP = 68

## Weights
# Relative weighing value for the routing temperature
ROUTING_WEIGHT = 0.4

# Relative weighing value for the TIGER temperature
TIGER_WEIGHT = 0.3

# Relative weighing value for the Freshness temperature
# Calculated 
FRESHNESS_WEIGHT = 0.2

# Relative weighing value for the Relations temperature
# See relation_temperature()
RELATION_WEIGHT = 0.1

# Relative weighing factor for the proportion representing the most recent 1/10/25/50/75% of edits
# These factors are used to calculate data freshness.
AGE_WEIGHT1 = 0.4
AGE_WEIGHT10 = 0.3
AGE_WEIGHT25 = 0.2
AGE_WEIGHT50 = 0.05
AGE_WEIGHT75 = 0.05
OLD_WEIGHT = -0.5

# Relative weighing value for the number of users doing 95% of the edits.
USER_WEIGHT95 = 0.1

# Base temperature
ZERO_DATA_TEMPERATURE = 32

# The relative weighing factors for each of the binned way categories as
# defined in entity.py
ROAD_CATEGORY_WEIGHTS = {'highways': 0.4, 'main': 0.30, 'local': 0.20, 'guidance': 0.1,
                         'unclassified':-0.1, 'uncommon':-0.2}

class RoutingAnalyzer(object):

    def __init__(self, nodecache):
        
        self.nodecache = nodecache
        self.constants = Containers()
        # Initialize feature containers, passing cache ref
        self.coords_entity = CoordEntity(self.nodecache)
        self.nodes_entity = NodeEntity(self.constants)
        self.ways_entity = WayEntity(self.nodecache, self.constants)
        self.relations_entity = RelationEntity(self.constants)

        self.nodeParser = OSMParser(concurrency=4, nodes_callback=self.nodes_entity.analyze)

        # Initialize the parser
        self.parser = OSMParser(concurrency=4, coords_callback=self.coords_entity.analyze,
                                ways_callback=self.ways_entity.analyze,
                                relations_callback=self.relations_entity.analyze)


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
    def routing_attributes_temperature(self, ways):
        highway_factor = ways.attribute_factor('highways')
        main_factor = ways.attribute_factor('main')
        local_factor = ways.attribute_factor('local')
        guidance_factor = ways.attribute_factor('guidance')
        unclassified_factor = ways.attribute_factor('unclassified')
        uncommon_factor = float (ways.uncommon_highway_length)/ways.length
        
        factors = highway_factor * ROAD_CATEGORY_WEIGHTS['highways'] + \
                main_factor * ROAD_CATEGORY_WEIGHTS['main'] + \
                local_factor * ROAD_CATEGORY_WEIGHTS['local'] + \
                guidance_factor * ROAD_CATEGORY_WEIGHTS['guidance'] + \
                unclassified_factor * ROAD_CATEGORY_WEIGHTS['unclassified'] + \
                uncommon_factor * ROAD_CATEGORY_WEIGHTS['uncommon']

        array = (highway_factor, main_factor, local_factor, guidance_factor, unclassified_factor, uncommon_factor, factors)
        return map(lambda x: BASIC_TEMP * x, array)
    
    # This function calculates the RELATION dimension of data temperature
    def relation_temperature(self, relations, intersections):
        number_of_intersections = len(filter(lambda x: x > 1, intersections.values()))
        return (float(relations.num_turnrestrcitions)/number_of_intersections) * BASIC_TEMP

    def freshness_temperature(self, edit_ages, edit_counts, current_date):
        # Aggregate user and edit counts
        # count all the dates that are within 1 month, 3months, 6 months, 1 year, 2 years
        # from the current date and give it an appropriate weight
        ages = edit_ages

        # don't reverse it, so when we ask for 95% edits it gets from the ascending order
        counts = edit_counts.values()
        counts.sort()

        # Freshness factors calculation
        # Count the number of values above the 1% , 10% age score, this gives the number of edits that are fresher
        # than 1% of the value.
        len_array = len(ages)
        ages1_factor = float(len(filter(lambda a:  current_date - datetime.timedelta(days = 30) <= a, ages)))/len_array * AGE_WEIGHT1
        ages10_factor = float(len(filter(lambda a: current_date - datetime.timedelta(days = 90) <= a, ages)))/len_array * AGE_WEIGHT10
        ages25_factor = float(len(filter(lambda a: current_date - datetime.timedelta(days = 180) <= a, ages)))/len_array * AGE_WEIGHT25
        ages50_factor = float(len(filter(lambda a: current_date - datetime.timedelta(days = 365) <= a, ages)))/len_array * AGE_WEIGHT50
        ages75_factor = float(len(filter(lambda a: current_date - datetime.timedelta(days = 730) <= a, ages)))/len_array * AGE_WEIGHT75

        # if the age of the data is older than 4 years weigh it negatively
        old_factor = (len_array - len(filter(lambda a: current_date + datetime.timedelta(days = -1460) <= a, ages)))/len_array * OLD_WEIGHT

        # Calculate 95 percintile of users, this is not part of freshness but
        # is used in the freshness temperature.
        user95_factor = float(len(filter(lambda a: a <= self.percentile(counts, 0.95), counts)))/len(counts) * USER_WEIGHT95
        return (ages1_factor + ages10_factor + ages25_factor   + user95_factor + ages50_factor + old_factor +
                ages75_factor) * BASIC_TEMP

    def data_temperatures(self):
        # Normalize the data temperature to between 0 and 40 and add a buffer of zero celsius
        reltemp = self.relation_temperature(self.relations_entity, self.constants.INTERSECTIONS) * DATA_TEMP # extra factor to improve
        # contribution from relations
        routingtemp = self.routing_attributes_temperature(self.ways_entity)
        freshnesstemp = self.freshness_temperature(self.constants.AGES, self.constants.USERS_EDITS, datetime.datetime.today())
        tigertemp = self.ways_entity.tiger_factor() * BASIC_TEMP
        finaltemp = ( RELATION_WEIGHT * reltemp +
                      ROUTING_WEIGHT * routingtemp[6] +
                      FRESHNESS_WEIGHT * freshnesstemp + 
                      TIGER_WEIGHT * tigertemp
                      + ZERO_DATA_TEMPERATURE 
                    )
        return reltemp, routingtemp[0], routingtemp[1], routingtemp[2], routingtemp[3], routingtemp[4], routingtemp[5], \
               routingtemp[6], freshnesstemp, tigertemp, finaltemp

    # The main function that parses the xml file and
    # calls the data temp calculations
    def run(self, filename):

        # check if the filename exists
        if not os.path.exists(filename):
            return

        # Timings can be done outside of the program using time(1)
        # and should probably be deprecated here
        t0 = time()
        
        # Parse the input data
        self.nodeParser.parse(filename)
        self.parser.parse(filename)
        t1 = time()

        # Print the parsing time
        # print 'The parsing of the file took %f' %(t1 - t0)
        
        # Calculate data temperature
        datatemps = self.data_temperatures()
        print 'Data temperatures for %s are: %s' % (filename, datatemps)
        #print 'Data temperature calculation took %fs' % (time() - t1)
        #print 'Total process took %fs' %(time() - t0)
        return datatemps

def usage():
    print 'python routing_analyzer.py [file.xml|pbf]'

def create_node_cache(infile=None):
    
    nodeCache = hdb.HDB()
    try:
        base_name = 'nodes.tch'
        if infile:
            base_name = os.path.basename(infile) + '_nodes.tch'
        
        node_cache_path = os.path.join(CACHE_LOCATION, base_name)
        if os.path.exists(node_cache_path):
            os.remove(node_cache_path)
        nodeCache.open(node_cache_path)
    except Exception:
        print 'node cache could not be created at %s, does the directory exist? If not, create it. If so, Check permissions and disk space.' % CACHE_LOCATION
        exit(1)
    return nodeCache


def main(args):
    if len(args) > 2 or len(args) < 2:
        usage()
        exit()

    nodeCache = create_node_cache(args[1])
    analysis_engine = RoutingAnalyzer(nodeCache)
    analysis_engine.run(args[1])

if __name__ == "__main__":
    main(sys.argv)

