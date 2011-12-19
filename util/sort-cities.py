from subprocess import call
import re
import glob

osmosisbinary = '/osm/software/osmosis-latest/bin/osmosis'
filesdir = '/osm/planet/zillow/*.pbf'

for infile in glob.glob(filesdir):
    outfile = re.sub('.osm.pbf', '-sorted.osm.pbf', infile)
    print outfile
    call([osmosisbinary, '--rb', infile, '--sort', '--wb', outfile])
