Fixture data info

How was this fixture data created?
* Created a line vector grid of 1x1 degree size, 0.01 degree interval
* Added id, highway, oneway, maxspeed, access tags
* Assigned highway=[motorway|primary|secondary] to a sample of the data
* Assigned highway=residential to the remainder of the data
* Assigned oneway=yes to a sample of the data
* Saved as Shapefile
* Converted to OSM using ogr2osm
* Added nodes at intersections using JOSM Utils plugin
* Added version, timestamp, user, uid attributes to node and way elements using a text editor (using constant values)
* Added tiger tags to all ways using constant values.