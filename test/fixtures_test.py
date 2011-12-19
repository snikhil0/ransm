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
import unittest

PATH = './fixtures/'

class Fixtures(TestCase):

    def setUp(self):
        pass

    def test_data_temperature(self):
        for infile in glob.glob(os.path.join(PATH, '*.osm')):
            command = 'python ../ransm/routing_analyzer.py %s' %infile
            os.system(command)
if __name__ == '__main__':
    unittest.main()