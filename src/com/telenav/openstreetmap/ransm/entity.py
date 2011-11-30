import sys
from datetime import datetime
from com.telenav.openstreetmap.ransm.user import User
import math

class Entity(object):

    def __init__(self):
        self.entity_count = 0
        self.min_version = sys.maxint
        self.max_version = 0
        self.mean_version = 0
        self.first_timestamp = datetime.max
        self.last_timestamp = datetime.min
        self.maxid = 0
        self.minid = sys.maxint
        self.users = {}
        self.ages = []

    def average_age(self):
        return sum(self.ages, 0.0) / len(self.ages)

    def extract_user(self, tags):
        if 'uid' in tags:
            uid = tags['uid']
        if 'user' in tags:
            name = tags['user']

        if uid not in self.users:
            self.users[uid] = User(uid, name)
        else:
            self.users[uid].increment(uid, 'ways')

    def extract_min_max_timestamp(self, osmtimestamp):
        timestamp = datetime.utcfromtimestamp(osmtimestamp)
        if timestamp > self.last_timestamp:
            self.last_timestamp = timestamp
        if timestamp < self.first_timestamp:
            self.first_timestamp = timestamp

    def extract_min_max_id(self, osmid):
        if osmid > self.maxid:
            self.maxid = osmid
        if osmid < self.minid:
            self.minid = osmid

    def extract_min_max_lat_lon(self, lon, lat):
        if lon > self.max_lon:
            self.max_lon = lon
        if lon < self.min_lon:
            self.min_lon = lon
        if lat < self.min_lat:
            self.min_lat = lat
        if lat > self.max_lat:
            self.max_lat = lat

    def extract_min_max_version(self, osmversion):
        if osmversion > self.max_version:
            self.max_version = osmversion
        if osmversion < self.min_version:
            self.min_version = osmversion
