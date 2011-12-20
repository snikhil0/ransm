from subprocess import call
import re
import os
import glob
import sys

def main(osmosisbinary, filesdir, flag):
    for infile in glob.glob(os.path.join(filesdir, '*.osm')):
        print infile
        if 'sorted' in infile:
            continue
        outfile = re.sub('.osm', '-sorted.osm', infile)
        print outfile
        if os.path.exists(outfile):
            continue
        if flag == 'xml':
            command = "%s --read-xml file=\"%s\" --sort --write-xml file=\"%s\"" %(osmosisbinary, infile, outfile)
        elif flag == 'pbf':
            command = "%s --read-pbf file=\"%s\" --sort --write-pbf file=\"%s\"" %(osmosisbinary, infile, outfile) 
        os.system(command) 

def usage():
    return 'python sort-cities.py [osmbinary] [filedir of osm files] [xml|pbf]'

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print usage()
    main(sys.argv[1], sys.argv[2], sys.argv[3])

