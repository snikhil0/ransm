from imposm.parser import OSMParser

cur = None

class Processor(object):
    cur = None
    cnt = 0
    def nodes(self, nodes): 
        if self.cur != 'n' and len(nodes) > 0:
            print '%i: %s -> n' % (self.cnt, self.cur)
            self.cur = 'n'
        self.cnt += len(nodes)

    def ways(self, ways):
        if self.cur != 'w' and len(ways) > 0:
            print '%i: %s -> w' % (self.cnt, self.cur)
            self.cur = 'w'
        self.cnt += len(ways)

p = Processor()
parser = OSMParser(concurrency=4, nodes_callback = p.nodes, ways_callback=p.ways)
parser.parse('/osm/planet/census-combinedstatisticalareas-2010/Austin-Round_Rock-Marble_Falls,_TX.osm.pbf')

