from datetime import datetime
from com.telenav.openstreetmap.ransm.entity import Entity
class CoordEntity(Entity):

    def __init__(self):
        '''
        Constructor
        '''
        Entity.__init__(self)
        self.min_lat = self.min_lon = float(-180.0)
        self.max_lat = self.max_lon = float(180.0)


    def analyze(self, coord):
        for osmid, lon, lat, osmversion, osmtimestamp in coord:
            self.entity_count += 1
            self.extract_min_max_timestamp(osmtimestamp)
            self.extract_min_max_id(osmid)
            self.extract_min_max_lat_lon(lon, lat)
            self.extract_min_max_version(osmversion)





