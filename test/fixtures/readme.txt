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

fixture1.osm
* 10202 nodes, all version 1, all created 2011-12-01 by the same user
* 201 ways, all version 1, all created 2011-12-01 by the same user
    motorway        9
    primary         16
    secondary       16
    tertiary        0
    unclassified    0
    residential     0
    cycleway        0
    footway         0
    road            5
    oneway          13
fixture1a.osm
    fixture1.osm + all residential roads have TIGER tags.
fixture1b.osm
    fixture1a.osm + all ways and nodes are version 2
fixture1c.osm
    fixture1a.osm + all ways are version 1, way nodes are version 2
    
fixture2a.osm
    fixture1.osm + 12 no left / no right turn restrictions on residential ways, all version 1, all created 2011-12-01 by the same user
fixture2b.osm
    fixture2a.osm + 12 no left / no right turn restrictions on primary ways, all version 1, all created 2011-12-01 by the same user
fixture2c.osm
    fixture2a.osm + 12 no left / no right turn restrictions on secondary ways, all version 1, all created 2011-12-01 by the same user
    
fixture3.osm
    fixture1.osm + all data created on 2008-01-01
    
GUIDANCE
fixture4a.osm
    fixture1.osm + 101 highway=traffic_signals nodes
fixture4b.osm
    fixture1.osm + 101 highway=mini_roundabout nodes
fixture4c.osm
    fixture1.osm + 101 highway=stop nodes
fixture4d.osm
    fixture1.osm + 101 highway=give_way nodes
fixture4e.osm
    fixture1.osm + 101 highway=crossing nodes
fixture4f.osm
    fixture1.osm + 101 highway=motorway_junction nodes on Motorway
fixture4g.osm
    fixture1.osm + 101 highway=roundabout nodes on nodes (THIS SHOULD BE PENALIZED)
fixture4h.osm
    fixture1.osm + 8 highway=residential changed to highway=cycleway
fixture4i.osm
    fixture1.osm + 8 highway=residential changed to highway=highway

    
WAY LENGTH
fixture5.osm
    fixture1.osm + all W-->E running ways split into individual segments (now has 10398 ways instead of 201)
    
    
TODO: Fixtures for incorrect guidance nodes (nodes not in way, way tags used on nodes, motorway_junction not on motorway)
