class User(object):
    def __init__(self, uid, name):
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
    edit_counts = []
    ages = []
    node_ages = []
    way_ages = []
    relation_ages = []

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
        self.usermap = unodes
        for k, v in uways.iteritems():
            self.add(v)
        for k, v in urelations.iteritems():
            self.add(v)
        self.user_edit_counts()

    def merge_ages(self, node_ages, way_ages, relation_ages):
        self.node_ages = node_ages
        self.way_ages = way_ages
        self.relation_ages = relation_ages
        self.ages = node_ages + way_ages + relation_ages

    def count(self):
        return len(self.usermap)

    def user_edit_counts(self):
        num = self.count()
        for v in self.usermap.values():
            self.edit_counts.append((v.count_nodes + v.count_ways + v.count_relations) / num)
