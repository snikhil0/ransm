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
from ransm.entity import NodeEntity, WayAttributeEntity, WayEntity, WAY_LENGTH_MAP, RelationEntity
from test import first_timestamp, last_timestamp, nodeCacheMock, ways, relations

class EntityTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNodeEntity(self):
        nodes = ((1, {'oneway': 'yes'}, (-122.1123, 38.45333), 1, first_timestamp, 1000),
                 (2, {'oneway': 'no'}, (-122.2123, 38.35333), 2, last_timestamp, 2000))
        nodeEntity = NodeEntity()
        nodeEntity.analyze(nodes)
        self.assertEqual(nodeEntity.max_version, 2)
        self.assertEqual(nodeEntity.min_version, 1)
        self.assertEqual(nodeEntity.minid, 1)
        self.assertEqual(nodeEntity.maxid, 2)
        self.assertEqual(nodeEntity.min_lat, 38.35333)
        self.assertEqual(nodeEntity.max_lat, 38.45333)
        self.assertEqual(nodeEntity.min_lon, -122.2123)
        self.assertEqual(nodeEntity.max_lon, -122.1123)

    def testWayEntity(self):
        wayEntity = WayEntity(nodeCacheMock)
        wayEntity.analyze(ways)

        self.assertEqual(wayEntity.max_version, 3)
        self.assertEqual(wayEntity.min_version, 2)
        self.assertEqual(wayEntity.minid, 90088567)
        self.assertEqual(wayEntity.maxid, 90088573)
        self.assertEqual(wayEntity.commonAttributes.tiger_tagged_ways, 1)
        self.assertEqual(wayEntity.commonAttributes.version_increase_over_tiger, 4)
        self.assertEqual(wayEntity.commonAttributes.untouched_by_user_edits, 0)
        self.assertEqual(wayEntity.commonAttributes.sum_versions, 5)
        self.assertEqual(wayEntity.entity_count, 2)

        length_way1 = wayEntity.calc_length([65433897, 259415186, 1044247254, 65486041,
                                             65394577, 689360672, 65396646])
        length_way2 = wayEntity.calc_length([1044247424, 1044247388, 1044247395, 1044247254])

        self.assertEqual(length_way1 + length_way2, wayEntity.length)
        self.assertEqual(len(wayEntity.attribute_models), 1)

        attribute = wayEntity.attribute_models['local']
        self.assertEqual(attribute.commonAttributes.tiger_tagged_ways, 1)
        self.assertEqual(attribute.commonAttributes.untouched_by_user_edits, 0)
        self.assertEqual(attribute.commonAttributes.version_increase_over_tiger, 4)
        self.assertEqual(attribute.commonAttributes.sum_versions, 5)
        self.assertEqual(attribute.sum_way_lengths, length_way1 + length_way2)
        self.assertEqual(attribute.sum_one_way_lengths, length_way1 + length_way2)
        self.assertEqual(attribute.sum_max_speed_lengths, 0)
        self.assertEqual(attribute.number_of_junctions, 0)
        self.assertEqual(attribute.sum_junction_length, 0)
        self.assertEqual(attribute.number_of_access, 0)
        self.assertEqual(attribute.sum_access_length, 0)

        self.assertEqual(wayEntity.tiger_factor(), 0.8)
        self.assertEqual(wayEntity.mean_version, 0) #Not used

        self.assertEqual(attribute.routing_factor(), 0.45)
        self.assertEqual(attribute.junction_factor(), 0)
        self.assertEqual(attribute.tiger_factor(), 0.8)

        self.assertEqual(wayEntity.attribute_factor('local'), (1 * 0.2 + 0.4 * 0.45 + 0.3 * 0.8))

    def testWayAttributeEntity(self):
        attribute = WayAttributeEntity()
        attribute.analyze(ways[0][0], ways[0][1], ways[0][3], first_timestamp, 1)
        self.assertEqual(attribute.entity_count, 1)
        self.assertEqual(attribute.number_of_access, 0)
        self.assertEqual(attribute.number_of_junctions, 0)
        self.assertEqual(attribute.sum_junction_length, 0)
        self.assertEqual(attribute.sum_one_way_lengths, 1)
        self.assertEqual(attribute.commonAttributes.sum_versions, 3)
        self.assertEqual(attribute.sum_way_lengths, 1)
        self.assertEqual(attribute.sum_access_length, 0)
        self.assertEqual(attribute.sum_max_speed_lengths, 0)
        self.assertEqual(attribute.tiger_factor(), 2.0/3)
        self.assertEqual(attribute.commonAttributes.tiger_tagged_ways, 1)
        self.assertEqual(attribute.routing_factor(), 0.45)
        self.assertEqual(attribute.commonAttributes.untouched_by_user_edits, 0)
        self.assertEqual(attribute.commonAttributes.version_increase_over_tiger, 2)

    def testRelationEntity(self):
        WAY_LENGTH_MAP[90088573] = 1
        WAY_LENGTH_MAP[90088567] = 2

        relationEntity = RelationEntity()
        relationEntity.analyze(relations)

        self.assertEquals(relationEntity.entity_count, 2)
        self.assertEqual(relationEntity.num_turnrestrcitions, 1)
        self.assertEqual(relationEntity.sum_restriction_length, 4)
        self.assertEqual(relationEntity.sum_turn_restriction_length, 3)

