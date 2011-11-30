'''
Created on Nov 29, 2011

@author: snikhil
'''

class User(object):
    '''
    classdocs
    '''


    def __init__(self, uid, name):
        '''
        Constructor
        '''
        self.uid = uid
        self.name = name
        self.count_nodes = 0
        self.count_ways = 0
        self.count_relations = 0
        self.ranking = {'nodes':1, 'ways':3, 'relations':9}

    def increment(self, name):
        if name == 'nodes':
            self.count_nodes += 1
        elif name == 'ways':
            self.count_ways += 1
        elif name == 'relations':
            self.count_relations += 1


class UserMgr(object):
    usermap = {}

    def __init__(self):
        pass

    def add(self, user):
        if user.id not in self.usermap:
            self.usermap[user.uid] = user
        else:
            user1 = self.usermap[user.uid]
            user1.count_nodes += user.count_nodes
            user1.count_ways += user.count_ways
            user1.count_relations += user.count_relations

    def increment(self, uid, name):
        if uid in self.usermap:
            user = self.usermap[uid]
            user.increment(name)

    def merge(self, unodes, uways, urelations):
        self.usermap = unodes.copy()
        for k, v in uways.iteritems():
            self.add(v)
        for k, v in urelations.iteritems():
            self.add(v)



