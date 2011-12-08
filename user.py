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
        else:
            print 'Wrong type'