# Map

**openstreetmap** (osm)

**overpass turbo** - uses query language to query osm data,
used fr very specific exports

**josm** - above but simpler

**geofabrik** - source for .osm file of whole PH

## Tooling

**netconvert** - .osm -> .xml

- `netconvert --osm-files edsa_aurora.osm -o edsa_aurora.net.xml`

**osmconvert** (under osmctools) - Used for extracting smaller areas from ph.osm

- `osmconvert philippines-latest.osm.pbf -b=121.055,14.621,121.06,14.625 -o=edsa_aurora.osm`
