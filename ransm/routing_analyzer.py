from imposm.parser import OSMParser
import sys
from coord_entity import CoordEntity
from time import time
from way_entity import WayEntity
from node_entity import NodeEntity
from relation_entity import RelationEntity

# This class does the way routing analysis.
# The analysis is based on tags corresponding to
# ways, nodes and relations
class RoutingAnalyzer():

    def __init__(self):
        self.ways_entity = WayEntity()
        self.nodes_entity = NodeEntity()
        self.relations_entity = RelationEntity()
        self.coords_entity = CoordEntity()
        self.parser = OSMParser(concurrency = 4, coords_callback = self.coords_entity.analyze, nodes_callback = self.nodes_entity.analyze,
                                ways_callback = self.ways_entity.analyze,
                                relations_callback = self.relations_entity.analyze)

    def run(self, filename):
        t0 = time()
        self.parser.parse(filename)
        t1 = time()
        print 'number of coords / nodes / ways / relations: %d / %d / %d / %d' % (self.coords_entity.entity_count,
                                                                                 self.nodes_entity.entity_count,
                                                                                 self.ways_entity.entity_count,
                                                                                 self.relations_entity.entity_count)
        print 'min / max node id: %d / %d' % (self.nodes_entity.minid, self.nodes_entity.maxid)
        print 'min / max way id: %d / %d' % (self.ways_entity.minid, self.ways_entity.maxid)
        print 'min / max relation id: %d / %d' % (self.relations_entity.minid, self.relations_entity.maxid)
        print 'bbox: (%f %f, %f %f)' % (self.coords_entity.min_lon, self.coords_entity.min_lat,
                                        self.coords_entity.max_lon, self.coords_entity.min_lat)
        print 'first way timestamp: %s' % (self.ways_entity.first_timestamp)
        print 'last way timestamp: %s' % (self.ways_entity.last_timestamp)
        print 'mean way version: %f' % (self.ways_entity.mean_version)
        print 'turn restrictions: %d' % (self.relations_entity.num_turnrestrcitions)
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

