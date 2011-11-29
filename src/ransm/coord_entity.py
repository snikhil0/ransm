from ransm.entity import Entity
from ransm.entity_action import IEntityAction

class CoordEntity(Entity, IEntityAction):

    def __init__(self):
        '''
        Constructor
        '''
        self.min_lat = self.min_lon = float(-180.0)
        self.max_lat = self.max_lon = float(180.0)

    def analyze(self, coord):
        for osmid, lon, lat, osmversion, osmtimestamp in coord:
            self.entity_count += 1

            if osmtimestamp > self.last_timestamp:
                self.last_timestamp = osmtimestamp

            if osmtimestamp < self.first_timestamp:
                self.first_timestamp = osmtimestamp

            if osmid > self.maxid:
                self.maxid = osmid

            if osmid < self.minid:
                self.minid = osmid

            if lon > self.max_lon:
                self.max_lon = lon

            if lon < self.min_lon:
                self.min_lon = lon

            if lat < self.min_lat:
                self.min_lat = lat

            if lat > self.max_lat:
                self.max_lat = lat

            if osmversion > self.max_version:
                self.max_version = osmversion

            if osmversion < self.min_version:
                self.min_version = osmversion





