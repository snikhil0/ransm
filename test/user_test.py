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
import unittest
from ransm.user import User


class UserTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def testUser(self):
        user = User(1, 'Nikhil')
        self.assertEqual(user.uid, 1, 'Wrong uid')
        self.assertEqual(user.name, 'Nikhil')

    def testUserIncrement(self):
        user = User(1, 'Nikhil')
        user.increment('nodes')
        user.increment('relations')
        user.increment('ways')
        user.increment('screw')
        self.assertEqual(user.count_nodes, 1)
        self.assertEqual(user.count_ways, 1)
        self.assertEqual(user.count_relations, 1)
