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
import time


first_timestamp = time.time()
last_timestamp = time.time() + 10000

ways = ((90088573, {'oneway': 'yes', 'highway': 'secondary', 'name': 'Moffet Boulevard',
                    'tiger:county': 'Santa Clara', 'tiger:name_base': 'Moffet'}, (65433897, 259415186, 1044247254,
                                                                                  65486041, 65394577,
                                                                                  689360672, 65396646), 3,
         first_timestamp, 1000),
        (90088567, {'oneway': 'yes', 'highway': 'secondary_link'}, (1044247424, 1044247388, 1044247395, 1044247254), 2,
         last_timestamp, 2000))

nodeCacheMock = {65433897: (-122.0730256, 37.4003229), 259415186: (-122.072894, 37.4004021),
                 1044247254: (-122.0722244, 37.4009026), 65486041: (-122.071587, 37.4013793),
                 65394577: (-122.071587, 37.4013793), 689360672: (-122.0694064, 37.4030326),
                 65396646: (-122.0693492, 37.4031059), 1044247424: (-122.0719762, 37.4012382),
                 1044247388: (-122.0722374, 37.4009704), 1044247395: (-122.0722529, 37.4009294)}

intersections = {65433897: 1, 259415186: 1,
                 1044247254: 2, 65486041:1,
                 65394577: 1, 689360672: 1,
                 65396646: 1, 1044247424: 1,
                 1044247388: 1, 1044247395: 1}

relations = ( (1, {'name': 'Somename', 'type':'restriction'}, [90088573, 90088567], 3, first_timestamp, 1000),
              (1, {'name': 'Somename', 'type':'route'}, [90088573], 2, last_timestamp, 2000))