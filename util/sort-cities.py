from subprocess import call
import re
import os
import glob

osmosisbinary = '/osm/software/osmosis-latest/bin/osmosis'
filesdir = '/osm/planet/census-combinedstatisticalareas-2010/*.pbf'

for infile in glob.glob(filesdir):
    if 'sorted' in infile:
        continue
    outfile = re.sub('.osm.pbf', '-sorted.osm.pbf', infile)
    if os.path.exists(outfile):
        continue
    call([osmosisbinary, '--rb', infile, '--sort', '--wb', outfile])
