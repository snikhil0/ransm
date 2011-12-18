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
from unittest import TestCase
import os, glob
import csv
import unittest
from ransm.routing_analyzer import RoutingAnalyzer, create_node_cache, flush

PATH = './fixtures/'
CSVOUT = os.path.join(PATH, 'results.csv')

class Fixtures(TestCase):

    def setUp(self):
        pass

    def test_data_temperature(self):
        csv_writer = csv.writer(open(CSVOUT, 'wb'), delimiter=',')
        csv_writer.writerow('relation temperature, routing temperature, freshness temperature,\
                            tiger temperature, final temperature')
        
        for infile in glob.glob(os.path.join(PATH, '*.osm')):
            db = create_node_cache(infile)
            ran = RoutingAnalyzer(db)
            ran.run(infile)
            csv_writer.writerow(ran.datatemps)
        print 'finished. Results in %s' % CSVOUT
        
if __name__ == '__main__':
    unittest.main()