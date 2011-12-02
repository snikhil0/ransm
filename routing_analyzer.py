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

DATA_TEMP = 100
BASIC_TEMP = 68

USER_WEIGHT95 = 0.3
AGE_WEIGHT1 = 0.7
AGE_WEIGHT10 = 0.6
AGE_WEIGHT25 = 0.5
AGE_WEIGHT50 = 0.4
AGE_WEIGHT75 = 0.2
UNTOUCHED_WEIGHT = -0.3
VERSION_INCREASE_OVER_TIGER = 0.7
ONE_WAY_WEIGHT = 0.4
MAX_SPEED_WEIGHT = 0.7

ZERO_DATA_TEMPERATURE = 32
NORMALIZE = (USER_WEIGHT95 + AGE_WEIGHT1 + AGE_WEIGHT10 + AGE_WEIGHT25 + AGE_WEIGHT50 + AGE_WEIGHT75
             - UNTOUCHED_WEIGHT + VERSION_INCREASE_OVER_TIGER + ONE_WAY_WEIGHT + MAX_SPEED_WEIGHT) * 100

class RoutingAnalyzer(object):
    def __init__(self):
        self.nodecache = hdb.HDB()
        try:
            self.nodecache.open(os.path.join(CACHE_LOCATION, 'nodes.tch'))
        except Exception:
            print 'node cache could not be created at %s, does the directory exist? If not, create it. If so, Check permissions and disk space.' % CACHE_LOCATION
            exit(1)
        self.ways_entity = WayEntity(self.nodecache)
        self.nodes_entity = NodeEntity()
        self.relations_entity = RelationEntity()
        self.coords_entity = CoordEntity(self.nodecache)
        self.parser = OSMParser(concurrency=4, coords_callback=self.coords_entity.analyze,
                                nodes_callback=self.nodes_entity.analyze,
                                ways_callback=self.ways_entity.analyze,
                                relations_callback=self.relations_entity.analyze)
        self.userMgr = UserMgr()


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


    def data_temerature(self):
        array = self.userMgr.ages
        array.sort()
        counts = self.userMgr.edit_counts
        counts.sort()

        one_percentile_age = self.percentile(array, 0.01)
        ten_percentile_age = self.percentile(array, 0.1)
        twentyfive_percentile_age = self.percentile(array, 0.25)
        fifty_percentile_age = self.percentile(array, 0.50)
        seventyfive_percentile_age = self.percentile(array, 0.75)
        nintyfive_percentile_user_edits = self.percentile(counts, 0.95)

        datatemp_user95 = nintyfive_percentile_user_edits * USER_WEIGHT95 * DATA_TEMP
        datatemp_ages1 = one_percentile_age * AGE_WEIGHT1 * DATA_TEMP
        datatemp_ages10 = ten_percentile_age * AGE_WEIGHT10 * DATA_TEMP
        datatemp_ages25 = twentyfive_percentile_age * AGE_WEIGHT25 * DATA_TEMP
        datatemp_ages50 = fifty_percentile_age * AGE_WEIGHT50 * DATA_TEMP
        datatemp_ages75 = seventyfive_percentile_age * AGE_WEIGHT75 * DATA_TEMP

        print 'datatemp_user95 %f' %datatemp_user95
        print 'datatemp_ages1 %f' %datatemp_ages1
        print 'datatemp_ages10 %f' %datatemp_ages10
        print 'datatemp_ages25 %f' %datatemp_ages25
        print 'datatemp_ages50 %f' %datatemp_ages50
        print 'datatemp_ages75 %f' %datatemp_ages75

        # Refactor later to compute temps from different sources and fuze them
        datatemp_untouched_by_users = UNTOUCHED_WEIGHT * (float(self.ways_entity.untouched_by_user_edits)/self.ways_entity.tiger_tagged_ways) * DATA_TEMP
        datatemp_version_increase_over_tiger = VERSION_INCREASE_OVER_TIGER * \
                                               (float(self.ways_entity.version_increase_over_tiger)/self.ways_entity.sum_versions)\
                                                * DATA_TEMP

        tiger_contributed_datatemp = datatemp_untouched_by_users + datatemp_version_increase_over_tiger
        print 'tiger_contributed_datatemp %f' %tiger_contributed_datatemp
        
        # temp from routing features normalized by way distances
        datatemp_oneway = ONE_WAY_WEIGHT * \
        (float(self.ways_entity.sum_way_one_way_lengths)/self.ways_entity.sum_way_lengths) * DATA_TEMP

        datatemp_maxspeed = MAX_SPEED_WEIGHT * \
        (float(self.ways_entity.sum_max_speed_lengths)/self.ways_entity.sum_way_lengths) * DATA_TEMP

        # Normalize the data temperature to between 0 and 40 and add a buffer of zero celsius
        datatemp = ((datatemp_ages1 + datatemp_ages10 + datatemp_ages25 + datatemp_oneway + datatemp_maxspeed + \
                   datatemp_user95 + datatemp_ages50 + datatemp_ages75 + tiger_contributed_datatemp)/NORMALIZE) * BASIC_TEMP + ZERO_DATA_TEMPERATURE
        return datatemp


    def run(self, filename):
        t0 = time()
        self.parser.parse(filename)
        t1 = time()
        self.userMgr.merge(self.nodes_entity.users, self.ways_entity.users,
                           self.relations_entity.users)

        self.userMgr.merge_ages(self.nodes_entity.ages, self.ways_entity.ages,
                                self.relations_entity.ages)

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

