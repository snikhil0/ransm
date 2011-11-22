from imposm.parser import OSMParser
import sys

# This class does the way routing analysis.
# The analysis is based on tags corresponding to
# ways, nodes and relations
from ransm.way_entity import WayEntity
from ransm.node_entity import NodeEntity
from ransm.relation_entity import RelationEntity

class RoutingAnalyzer():

    def __init__(self):
        ways_entity = WayEntity()
        nodes_entity = NodeEntity()
        relations_entity = RelationEntity()
        self.parser = OSMParser(concurrency=4, nodes_callback=nodes_entity.analyze,
                                ways_callback=ways_entity.analyze,
                                relations_callback=relations_entity.analyze)

    def run(self, filename):
        pass



def usage():
        print 'python routing_analyzer.py [file.xml|pbf]'
        
def main(args):
    if len(args) > 2 or len(args) < 2:
        usage()
        exit()

if __name__ == "__main__":
    main(sys.argv)

