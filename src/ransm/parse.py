# parse.py
# --------
# Get metrics relevant for routing from OSM PBF files. 
#
# Usage:
# ------
# parse.py requires a modified version of imposm.parser which can be 
# found at https://github.com/mvexel/imposm.parser
# 
# Right now, the OSM file is hardcoded into the script (see the PBF_FILE
# variable).
#
#
# Copyright 2011 Martijn van Exel / geospatial omnivore
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

import sys
from imposm.parser import OSMParser
from time import time
from datetime import datetime

PBF_FILE = '/home/mvexel/osm/planet/zillow/Salt_Lake_City_UT.osm.pbf'

class NavTagsCounter(object):
	turnrestrictions = 0
	meanwayversion = 0
	firstobject = datetime.max
	lastobject = datetime.min
	numcoords = numnodes = numways = numrelations = 0
	maxnodeid = maxwayid = maxrelationid = 0
	minnodeid = minwayid = minrelationid = sys.maxint
	minlon = minlat = float(180.0)
	maxlon = maxlat = float(-180.0)

	def coord(self, coord):
		for osmid, lon, lat, osmversion, osmtimestamp in coord:
			self.numcoords += 1
			objdate = datetime.utcfromtimestamp(osmtimestamp)
			self.lastobject = self.lastobject if self.lastobject > objdate else objdate
			self.firstobject = self.firstobject if self.firstobject < objdate else objdate
			self.minnodeid = self.minnodeid if self.minnodeid < osmid else osmid
			self.maxnodeid = self.maxnodeid if self.minnodeid > osmid else osmid
			self.minlon = self.minlon if self.minlon < lon else lon
			self.minlat = self.minlat if self.minlat < lat else lat
			self.maxlon = self.maxlon if self.maxlon > lon else lon
			self.maxlat = self.maxlat if self.maxlat > lat else lat

	def node(self, node):
		for osmid, tags, ref, osmversion, osmtimestamp in node:
			self.numnodes += 1

	def way(self, way):
		for osmid, tags, ref, osmversion, osmtimestamp in way:
			self.numways += 1
			objdate = datetime.utcfromtimestamp(osmtimestamp)
			self.meanwayversion = float(((self.numways - 1) * self.meanwayversion + osmversion) / float(self.numways))
			self.lastobject = self.lastobject if self.lastobject > objdate else objdate
			self.firstobject = self.firstobject if self.firstobject < objdate else objdate
			self.minwayid = self.minwayid if self.minwayid < osmid else osmid
			self.maxwayid = self.maxwayid if self.minwayid > osmid else osmid

	def relation(self, relation):
		for osmid, tags, refs, osmversion, osmtimestamp in relation:
			self.numrelations += 1
			objdate = datetime.utcfromtimestamp(osmtimestamp)
			if 'type' in tags and tags['type'] == 'restriction':
				self.turnrestrictions += 1
			self.lastobject = self.lastobject if self.lastobject > objdate else objdate
			self.firstobject = self.firstobject if self.firstobject < objdate else objdate
			self.minrelationid = self.minrelationid if self.minrelationid < osmid else osmid
			self.maxrelationid = self.maxrelationid if self.minrelationid > osmid else osmid

t0 = time()
counter = NavTagsCounter()
p = OSMParser(concurrency = 4, coords_callback = counter.coord, nodes_callback = counter.node, ways_callback = counter.way, relations_callback = counter.relation)
p.parse(PBF_FILE)
t1 = time()

print 'number of coords / nodes / ways / relations: %d / %d / %d / %d' % (counter.numcoords, counter.numnodes, counter.numways, counter.numrelations)
print 'min / max node id: %d / %d' % (counter.minnodeid, counter.maxnodeid)
print 'min / max way id: %d / %d' % (counter.minwayid, counter.maxwayid)
print 'min / max relation id: %d / %d' % (counter.minrelationid, counter.maxrelationid)
print 'bbox: (%f %f, %f %f)' % (counter.minlon, counter.minlat, counter.maxlon, counter.maxlat)
print 'first object: %s' % (counter.firstobject)
print 'last object: %s' % (counter.lastobject)
print 'mean way version: %f' % (counter.meanwayversion)
print 'turn restrictions: %d' % (counter.turnrestrictions)
print 'took %fs' % (t1 - t0)
