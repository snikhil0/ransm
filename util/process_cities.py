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
import os, glob
import csv
from tcdb import hdb
from ransm.routing_analyzer import RoutingAnalyzer, CACHE_LOCATION

PATH = '/osm/planet/zillow/'
CSVOUT = os.path.join(PATH, 'results.csv')

csv_writer = csv.writer(open(CSVOUT, 'wb'), delimiter=',')
        
for infile in glob.glob(os.path.join(PATH, '*.osm.pbf')):
    db = hdb.HDB()
    try:
        base_name = os.path.basename(infile) + '_nodes.tch'
        db.open(os.path.join(CACHE_LOCATION, base_name))
    except Exception:
            print 'node cache could not be created at %s, does the directory exist? If not, create it. If so, Check permissions and disk space.' % CACHE_LOCATION
            exit(1)
    ran = RoutingAnalyzer(db)
    datatemps = ran.run(infile)
    outrow = list(ran.datatemps)
    basepath, cityname = os.path.split(infile)
    outrow.insert(0,cityname)
    csv_writer.writerow(outrow)
#            print ran.datatemp
print 'finished. Results in %s' % CSVOUT