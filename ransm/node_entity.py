__author__ = 'snikhil'

class NodeEntity(object):

    def analyze(self, nodes):
        #callback method for the ways
        for osmid, tags, refs in nodes:
            print osmid

    
