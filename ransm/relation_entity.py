__author__ = 'snikhil'

class RelationEntity(object):

    def analyze(self, relations):
        #callback method for the ways
        for osmid, tags, refs in relations:
            print osmid