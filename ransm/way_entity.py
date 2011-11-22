__author__ = 'snikhil'

class WayEntity(object):
    score_ways = {} #dictionary of osmid and score

    # the three broad categories of roads
    score_highways = {}
    score_arterial = {}
    score_local = {}

    def analyze(self, ways):
        #callback method for the ways
        for osmid, tags, refs in ways:
            pass