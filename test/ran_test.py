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
import datetime
from ransm.entity import WayEntity, RelationEntity, Containers
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
        const = Containers()
        wayEntity = WayEntity(nodeCacheMock, const)
        wayEntity.analyze(ways)
        self.assertAlmostEqual(self.ran.routing_attributes_temperature(wayEntity)[6], 5.168)

    def testRelationTemperature(self):
        const = Containers()
        const.WAY_LENGTH_MAP[90088573] = 1
        const.WAY_LENGTH_MAP[90088567] = 2

        relationEntity = RelationEntity(const)
        relationEntity.analyze(relations)
        self.assertEqual(self.ran.relation_temperature(relationEntity, intersections), 68)
        intersections[1044247388] = 2
        self.assertEqual(self.ran.relation_temperature(relationEntity, intersections), 34)

    def testFreshnessTemperature(self):
        now = datetime.datetime.today()
        ages = [datetime.datetime.today(), now + datetime.timedelta(days=-1), now + datetime.timedelta(days=-45),
                now + datetime.timedelta(-366), now + datetime.timedelta(-990)]
        #ages = [1, 2, 3, 4, 5]
        counts = {1:10, 2:15, 3:100, 4:200, 5:250}
        self.assertAlmostEqual(self.ran.freshness_temperature(ages, counts, datetime.datetime.now()),
                         (0.4*0.4 + 0.6*0.3 + 0.6*.2 + 0.6*0.05 + 0.8 *0.05+ 0.8*0.1)*68)
        ages = [now + datetime.timedelta(-3000), now + datetime.timedelta(-3900), now + datetime.timedelta(-4000),
                now + datetime.timedelta(-4110), now + datetime.timedelta(-4200)]
        counts = {1:10, 2:15, 3:100, 4:200, 5:250}
        self.assertAlmostEqual(self.ran.freshness_temperature(ages, counts, datetime.datetime.now()),
                         (-0.5 + 0.8*0.1)*68)