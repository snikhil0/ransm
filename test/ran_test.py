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
from ransm.entity import WayEntity, RelationEntity, WAY_LENGTH_MAP
from ransm.routing_analyzer import RoutingAnalyzer
from test import relations, nodeCacheMock, ways, intersections


class Test(unittest.TestCase):

    ran = None

    def setUp(self):
        self.ran = RoutingAnalyzer(nodeCacheMock)

    def tearDown(self):
        pass

    def testPercentile(self):
        list = [1, 2, 3, 4, 5]
        p = self.ran.percentile(list, 0.75)
        below_p = filter(lambda l: l < p, list)
        self.assertEquals(4, p, 'Wrong ')
        self.assertEquals(3,len(below_p), 'Wrong')


    def testRoutingAttributeTemperature(self):
        wayEntity = WayEntity(nodeCacheMock)
        wayEntity.analyze(ways)
        self.assertEqual(self.ran.routing_attributes_temperature(wayEntity), (1 * 0.2 + 0.4 * 0.45 + 0.3 * 0.4)*0.2*68)

    def testRelationTemperature(self):
        WAY_LENGTH_MAP[90088573] = 1
        WAY_LENGTH_MAP[90088567] = 2

        relationEntity = RelationEntity()
        relationEntity.analyze(relations)
        self.assertEqual(self.ran.relation_temperature(relationEntity, intersections), 68)
        intersections[1044247388] = 2
        self.assertEqual(self.ran.relation_temperature(relationEntity, intersections), 34)

    def testFreshnessTemperature(self):
        ages = [1, 2, 3, 4, 5]
        counts = {1:10, 2:15, 3:100, 4:200, 5:250}
        self.assertAlmostEqual(self.ran.freshness_temperature(ages, counts),
                         (0.2*0.3 + 0.2*0.25 + 0.4*.15 + 0.6*0.05 + 0.8*0.05+0.8*0.1)*68)