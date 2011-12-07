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
        if user.uid not in self.usermap:
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

    def merge(self, users_cache):
        for k, v in users_cache.iteritems():
            self.add(v)
        self.user_edit_counts()

    def merge_ages(self, ages_cache):
        self.ages = ages_cache

    def count(self):
        return len(self.usermap)

    def user_edit_counts(self):
        num = self.count()
        for v in self.usermap.values():
            self.edit_counts.append((v.count_nodes + v.count_ways + v.count_relations) / num)
